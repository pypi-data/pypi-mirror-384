# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

import json
import uuid
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import Dict, Generator, List, Tuple, Optional, Any
from jsonpath_ng import parse as parse_jsonpath

from ibm_watsonx_gov.clients.api_client import APIClient
from ibm_watsonx_gov.entities.agentic_app import (AgenticApp,
                                                  MetricsConfiguration, Node)
from ibm_watsonx_gov.entities.enums import MetricGroup
from ibm_watsonx_gov.entities.evaluation_result import AgentMetricResult, NodeData, MessageData, MetricMapping, MetricsMappingData
from ibm_watsonx_gov.entities.metric import MappingItem
from ibm_watsonx_gov.entities.foundation_model import FoundationModelInfo
from ibm_watsonx_gov.evaluators.impl.evaluate_metrics_impl import \
    _evaluate_metrics_async
from ibm_watsonx_gov.traces.span_node import SpanNode
from ibm_watsonx_gov.traces.span_util import (get_attributes,
                                              get_span_nodes_from_json)
from ibm_watsonx_gov.utils.async_util import (gather_with_concurrency,
                                              run_in_event_loop)
from ibm_watsonx_gov.utils.python_utils import add_if_unique
from ibm_watsonx_gov.metrics.utils import mapping_to_df

try:
    from opentelemetry.proto.trace.v1.trace_pb2 import Span
except:
    pass

TARGETED_USAGE_TRACE_NAMES = [
    # openAI
    "openai.embeddings",
    "ChatOpenAI.chat",
    "OpenAI.completion",
    # IBM
    "ChatWatsonx.chat",
    "WatsonxLLM.completion",
    # Azure
    "AzureChatOpenAI.chat",
    "AzureOpenAI.completion",
    # AWS
    "ChatBedrock.chat",
    "ChatBedrockConverse.chat",
    # Google
    "ChatVertexAI.chat",
    "VertexAI.completion",
    # Anthropic
    "ChatAnthropic.chat",
    "ChatAnthropicMessages.chat",
    # TODO: Add attributes for other frameworks as well.
]
ONE_M = 1000000
COST_METADATA = {  # Costs per 1M tokens
    # ref: https://platform.openai.com/docs/pricing
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "chatgpt-4o-latest": {"input": 5.0, "output": 15.0},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "text-embedding-3-large": {"input": 0.13, "output": 0.0},
    "text-embedding-3-small": {"input": 0.02, "output": 0.0},
    "text-embedding-ada-002": {"input": 0.10, "output": 0.0},

    # ref: https://docs.anthropic.com/en/docs/about-claude/models/overview#model-pricing
    "claude-opus-4-0": {"input": 15.0, "output": 75.0},
    "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
    "anthropic.claude-opus-4-20250514-v1:0": {"input": 15.0, "output": 75.0},
    "claude-opus-4@20250514": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-0": {"input": 3.0, "output": 15.0},
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "anthropic.claude-sonnet-4-20250514-v1:0": {"input": 3.0, "output": 15.0},
    "claude-sonnet-4@20250514": {"input": 3.0, "output": 15.0},
    "claude-3-7-sonnet-latest": {"input": 3.0, "output": 15.0},
    "claude-3-7-sonnet-20250219": {"input": 3.0, "output": 15.0},
    "anthropic.claude-3-7-sonnet-20250219-v1:0": {"input": 3.0, "output": 15.0},
    "claude-3-7-sonnet@20250219": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet-latest": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet-v2@20241022": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-latest": {"input": 0.80, "output": 4.0},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.0},
    "anthropic.claude-3-5-haiku-20241022-v1:0": {"input": 0.80, "output": 4.0},
    "claude-3-5-haiku@20241022": {"input": 0.80, "output": 4.0},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    "anthropic.claude-3-haiku-20240307-v1:0": {"input": 0.25, "output": 1.25},
    "claude-3-haiku@20240307": {"input": 0.25, "output": 1.25},

    # ref: https://cloud.google.com/vertex-ai/generative-ai/pricing
    "gemini-2.5-pro": {"input": 1.25, "output": 10.0},
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
    "gemini-2.5-flash-lite": {"input": 0.1, "output": 0.4},
    "gemini-2.0-flash-001": {"input": 0.15, "output": 0.6},
    "gemini-2.0-flash-lite-001": {"input": 0.075, "output": 0.3},

    # ref: https://mistral.ai/pricing#api-pricing
    # ref: https://aws.amazon.com/bedrock/pricing
    # ref: https://cloud.google.com/vertex-ai/generative-ai/pricing
    "pixtral-large-latest": {"input": 2.0, "output": 6.0},
    "mistral.pixtral-large-2502-v1:0": {"input": 2.0, "output": 6.0},
    "mistral-large-latest": {"input": 2.0, "output": 6.0},
    "mistral.mistral-large-2407-v1:0": {"input": 2.0, "output": 6.0},
    "mistralai/mistral-large-2411@001": {"input": 2.0, "output": 6.0},
    "mistral.mistral-large-2402-v1:0": {"input": 4.0, "output": 12.0},
    "mistral-medium-latest": {"input": 0.4, "output": 2.0},
    "mistral-small-latest": {"input": 0.1, "output": 0.3},
    "mistralai/mistral-small-2503@001": {"input": 0.1, "output": 0.3},
    "mistral.mistral-small-2402-v1:0": {"input": 1.0, "output": 3.0},
    "open-mistral-7b": {"input": 0.25, "output": 0.25},
    "mistral.mistral-7b-instruct-v0:2": {"input": 0.15, "output": 0.2},
    "open-mixtral-8x7b": {"input": 0.7, "output": 0.7},
    "mistral.mixtral-8x7b-instruct-v0:1": {"input": 0.45, "output": 0.7},

    # ref: https://aws.amazon.com/bedrock/pricing
    "command-r": {"input": 0.5, "output": 1.5},
    "cohere.command-r-v1:0": {"input": 0.5, "output": 1.5},
    "command-r-plus": {"input": 3.0, "output": 15},
    "cohere.command-r-plus-v1:0": {"input": 3.0, "output": 15},
    "command-light": {"input": 0.3, "output": 0.6},
    "cohere.command-light-text-v14": {"input": 0.3, "output": 0.6},
    "command": {"input": 1.0, "output": 2.0},
    "cohere.command-text-v14": {"input": 1.0, "output": 2.0},

    # ref: https://www.ai21.com/pricing
    # ref: https://aws.amazon.com/bedrock/pricing
    # ref: https://cloud.google.com/vertex-ai/generative-ai/pricing
    "jamba-large": {"input": 2.0, "output": 8.0},
    "ai21.jamba-1-5-large-v1:0": {"input": 2.0, "output": 8.0},
    "ai21/jamba-1.5-large@001": {"input": 2.0, "output": 8.0},
    "jamba-mini": {"input": 0.2, "output": 0.4},
    "ai21.jamba-1-5-mini-v1:0": {"input": 0.2, "output": 0.4},
    "ai21/jamba-1.5-mini@001": {"input": 0.2, "output": 0.4},

    # ref: https://www.ibm.com/products/watsonx-ai/pricing
    "ibm/granite-vision-3-2-2b": {"input": 0.10, "output": 0.10},
    "ibm/granite-3-2b-instruct": {"input": 0.10, "output": 0.10},
    "ibm/granite-guardian-3-8b": {"input": 0.20, "output": 0.20},
    "ibm/granite-8b-japanese": {"input": 0.60, "output": 0.60},
    "meta-llama/llama-3-2-11b-vision-instruct": {"input": 0.35, "output": 0.35},
    "meta-llama/llama-3-2-1b-instruct": {"input": 0.1, "output": 0.1},
    "meta-llama/llama-3-2-3b-instruct": {"input": 0.15, "output": 0.15},
    "meta-llama/llama-3-2-90b-vision-instruct": {"input": 2.0, "output": 2.0},
    "meta-llama/llama-3-3-70b-instruct": {"input": 0.71, "output": 0.71},
    "meta-llama/llama-3-405b-instruct": {"input": 5.0, "output": 16.0},
    "meta-llama/llama-guard-3-11b-vision": {"input": 0.35, "output": 0.35},
    "mistralai/mistral-small-3-1-24b-instruct-2503": {"input": 0.1, "output": 0.3},
    "mistralai/mistral-medium-2505": {"input": 3.0, "output": 10.0},
    "core42/jais-13b-chat": {"input": 1.8, "output": 1.8},
    "sdaia/allam-1-13b-instruct": {"input": 1.8, "output": 1.8},
    "meta-llama/llama-4-maverick-17b-128e-instruct-fp": {"input": 0.35, "output": 1.4},
    "ibm/granite-embedding-107m-multilingual": {"input": 0.10, "output": 0.10},
    "ibm/granite-embedding-278m-multilingual": {"input": 0.10, "output": 0.10},
    "ibm/slate-125m-english-rtrvr": {"input": 0.10, "output": 0.10},
    "ibm/slate-125m-english-rtrvr-v2": {"input": 0.10, "output": 0.10},
    "ibm/slate-30m-english-rtrvr": {"input": 0.10, "output": 0.10},
    "ibm/slate-30m-english-rtrvr-v2": {"input": 0.10, "output": 0.10},
    "intfloat/multilingual-e5-large": {"input": 0.10, "output": 0.10},
    "sentence-transformers/all-minilm-l12-v2": {"input": 0.10, "output": 0.10},
    "sentence-transformers/all-minilm-l6-v2": {"input": 0.10, "output": 0.10},
}


class TraceUtils:

    @staticmethod
    def build_span_trees(spans: list[dict], agentic_app: AgenticApp | None = None) -> List[SpanNode]:
        root_spans: list[SpanNode] = []

        span_nodes: dict[str, SpanNode] = {}
        for span in spans:
            span_nodes.update(get_span_nodes_from_json(span, agentic_app))

        # Create tree
        for _, node in span_nodes.items():
            parent_id = node.span.parent_span_id
            if not parent_id:
                root_spans.append(node)  # Root span which will not have parent
            else:
                parent_node = span_nodes.get(parent_id)
                if parent_node:
                    parent_node.add_child(node)
                else:
                    # Orphan span where parent is not found
                    root_spans.append(node)

        return root_spans

    @staticmethod
    def convert_array_value(array_obj: Dict) -> List:
        """Convert OTEL array value to Python list"""
        return [
            item.get("stringValue")
            or int(item.get("intValue", ""))
            or float(item.get("doubleValue", ""))
            or bool(item.get("boolValue", ""))
            for item in array_obj.get("values", [])
        ]

    @staticmethod
    def stream_trace_data(file_path: Path) -> Generator:
        """Generator that yields spans one at a time."""
        with open(file_path) as f:
            for line in f:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse line: {line}\nError: {e}")

    @staticmethod
    def __extract_usage_meta_data(span: Span) -> dict:
        """
        Extract meta data required to calculate usage metrics from spans
        """
        meta_data = {}
        attributes = get_attributes(span.attributes)
        model = attributes.get("gen_ai.request.model")

        if not model:
            return meta_data

        meta_data["cost"] = {
            "model": model,
            "total_prompt_tokens": attributes.get("gen_ai.usage.prompt_tokens", 0),
            "total_completion_tokens": attributes.get(
                "gen_ai.usage.completion_tokens", 0
            ),
            "total_tokens": attributes.get("llm.usage.total_tokens", 0),
        }
        meta_data["input_token_count"] = attributes.get(
            "gen_ai.usage.prompt_tokens", 0)
        meta_data["output_token_count"] = attributes.get(
            "gen_ai.usage.completion_tokens", 0)
        return meta_data

    @staticmethod
    def calculate_cost(usage_data: List[dict]) -> float:
        """Calculate cost for given list of usage."""
        total_cost = 0.0

        for data in usage_data:
            model = data["model"].lower()

            try:
                model_pricing = COST_METADATA[model]
            except KeyError:
                return 0
                # raise ValueError(
                #     f"Pricing not available for {model}")

            # Calculate costs (per 1M tokens)
            input_cost = (data["total_prompt_tokens"] /
                          ONE_M) * model_pricing["input"]
            output_cost = (data["total_completion_tokens"] / ONE_M) * model_pricing[
                "output"
            ]
            total_cost += input_cost + output_cost

        return total_cost

    @staticmethod
    async def compute_metrics_from_trace_async(span_tree: SpanNode, api_client: APIClient = None, **kwargs) -> tuple[list[AgentMetricResult], list[Node], list]:
        metric_results, edges = [], []

        # Add Interaction level metrics
        metric_results.extend(await TraceUtils.__compute_message_level_metrics(
            span_tree, api_client, **kwargs))

        # Add node level metrics result
        node_metric_results, nodes_list, experiment_run_metadata = await TraceUtils.__compute_node_level_metrics(
            span_tree, api_client, **kwargs)
        metric_results.extend(node_metric_results)

        for node in nodes_list:
            if node.name in experiment_run_metadata:
                node.foundation_models = list(
                    experiment_run_metadata[node.name]["foundation_models"])

        return metric_results, nodes_list, edges

    @staticmethod
    def compute_metrics_from_trace(span_tree: SpanNode, api_client: APIClient = None) -> tuple[
            list[AgentMetricResult], list[Node], list]:
        return run_in_event_loop(
            TraceUtils.compute_metrics_from_trace_async, span_tree, api_client)

    @staticmethod
    async def __compute_node_level_metrics(span_tree: SpanNode, api_client: APIClient | None, **kwargs):
        metric_results = []
        trace_metadata = defaultdict(list)
        experiment_run_metadata = defaultdict(lambda: defaultdict(set))
        nodes_list = []
        node_stack = list(span_tree.children)
        child_stack = list()
        node_execution_count = {}
        while node_stack or child_stack:
            is_parent = not child_stack
            node = child_stack.pop() if child_stack else node_stack.pop()
            if is_parent:
                parent_span: Span = node.span
                node_name, metrics_config_from_decorators, code_id, events, execution_order = None, [], "", [], None
                data = {}
                # inputs = get_nested_attribute_values(
                #     [node], "traceloop.entity.input")
                # outputs = get_nested_attribute_values(
                #     [node], "traceloop.entity.output")
            span: Span = node.span

            for attr in span.attributes:
                key = attr.key
                value = attr.value

                if is_parent:
                    if key == "traceloop.entity.name":
                        node_name = value.string_value
                    elif key == "gen_ai.runnable.code_id":
                        code_id = value.string_value
                    elif key == "traceloop.association.properties.langgraph_step":
                        execution_order = int(
                            value.int_value) if value else None
                    elif key in ("traceloop.entity.input", "traceloop.entity.output"):
                        try:
                            content = json.loads(value.string_value)
                            inputs_outputs = content.get(
                                "inputs" if key.endswith("input") else "outputs")
                            if isinstance(inputs_outputs, str):
                                inputs_outputs = json.loads(inputs_outputs)
                            if data:
                                data.update(inputs_outputs)
                            else:
                                data = inputs_outputs
                        except (json.JSONDecodeError, AttributeError) as e:
                            raise Exception(
                                "Unable to parse json string") from e
                if key.startswith("wxgov.config.metrics"):
                    metrics_config_from_decorators.append(
                        json.loads(value.string_value))
            if span.events:
                events.extend(span.events)

            if (not node_name) or (node_name == "__start__"):
                continue

            if span.name in TARGETED_USAGE_TRACE_NAMES:
                # Extract required details to calculate usage metrics from each span
                for k, v in TraceUtils.__extract_usage_meta_data(span).items():
                    trace_metadata[k].append(v)

            for k, v in TraceUtils.__get_run_metadata_from_span(span).items():
                experiment_run_metadata[node_name][k].add(v)

            child_stack.extend(node.children)

            if not child_stack:
                metrics_to_compute, all_metrics_config = TraceUtils.__get_metrics_to_compute(
                    span_tree.get_nodes_configuration(), node_name, metrics_config_from_decorators)

                add_if_unique(Node(name=node_name, func_name=code_id.split(":")[-1] if code_id else node_name, metrics_configurations=all_metrics_config), nodes_list,
                              ["name", "func_name"])

                if node_name in node_execution_count:
                    node_execution_count[node_name] += node_execution_count.get(
                        node_name)
                else:
                    node_execution_count[node_name] = 1

                coros = []
                for mc in metrics_to_compute:
                    coros.append(_evaluate_metrics_async(
                        configuration=mc.configuration,
                        data=data,
                        metrics=mc.metrics,
                        metric_groups=mc.metric_groups,
                        api_client=api_client,
                        **kwargs))

                results = await gather_with_concurrency(coros, max_concurrency=kwargs.get("max_concurrency", 10))
                for metric_result in results:
                    for mr in metric_result.to_dict():
                        node_result = {
                            "applies_to": "node",
                            "message_id": span_tree.get_message_id(),
                            "node_name": node_name,
                            "conversation_id": span_tree.get_conversation_id(),
                            "execution_count": node_execution_count.get(node_name),
                            "execution_order": execution_order,
                            **mr
                        }
                        metric_results.append(AgentMetricResult(**node_result))

                # Add node latency metric result
                metric_results.append(AgentMetricResult(name="latency",
                                                        display_name="Latency",
                                                        value=(int(
                                                            parent_span.end_time_unix_nano) - int(parent_span.start_time_unix_nano))/1e9,
                                                        group=MetricGroup.PERFORMANCE,
                                                        applies_to="node",
                                                        message_id=span_tree.get_message_id(),
                                                        conversation_id=span_tree.get_conversation_id(),
                                                        node_name=node_name,
                                                        execution_count=node_execution_count.get(
                                                            node_name),
                                                        execution_order=execution_order))

                # Get the node level metrics computed online during graph invocation from events
                metric_results.extend(TraceUtils.__get_metrics_results_from_events(
                    events=events,
                    message_id=span_tree.get_message_id(),
                    conversation_id=span_tree.get_conversation_id(),
                    node_name=node_name,
                    execution_count=node_execution_count.get(node_name),
                    execution_order=execution_order))

        metric_results.extend(
            TraceUtils.__compute_usage_metrics_from_trace_metadata(trace_metadata, span_tree.get_message_id(), span_tree.get_conversation_id()))

        return metric_results, nodes_list, experiment_run_metadata

    @staticmethod
    async def __compute_message_level_metrics(span_tree: SpanNode, api_client: APIClient | None, **kwargs) -> list[AgentMetricResult]:
        metric_results = []
        span = span_tree.span
        metric_results.append(AgentMetricResult(name="duration",
                                                display_name="Duration",
                                                value=(int(
                                                    span.end_time_unix_nano) - int(span.start_time_unix_nano))/1000000000,
                                                group=MetricGroup.PERFORMANCE,
                                                applies_to="message",
                                                message_id=span_tree.get_message_id(),
                                                conversation_id=span_tree.get_conversation_id()))

        if not span_tree.agentic_app:
            return metric_results

        data = {}

        attrs = get_attributes(
            span.attributes, ["traceloop.entity.input", "traceloop.entity.output"])
        inputs = attrs.get("traceloop.entity.input", "{}")
        if isinstance(inputs, str):
            inputs = json.loads(inputs).get("inputs", {})
        elif isinstance(inputs, dict):
            inputs = inputs.get("inputs", {})

        if "messages" in inputs:
            for message in reversed(inputs["messages"]):
                if "kwargs" in message and "type" in message["kwargs"] and message["kwargs"]["type"].upper() == "HUMAN":
                    data["input_text"] = message["kwargs"]["content"]
                    break
        else:
            data.update(inputs)

        outputs = attrs.get("traceloop.entity.output", "{}")
        if isinstance(outputs, str):
            outputs = json.loads(outputs).get("outputs", {})
        elif isinstance(outputs, dict):
            outputs = outputs.get("outputs", {})

        if "messages" in outputs:
            # The messages is a list depicting the history of messages with the agent.
            # It need NOT be the whole list of messages in the conversation though.
            # We will traverse the list from the end to find the human input of the message,
            # and the AI output.

            # If there was no input_text so far, find first human message
            if "input_text" not in data:
                for message in reversed(outputs["messages"]):
                    if "kwargs" in message and "type" in message["kwargs"] and message["kwargs"]["type"].upper() == "HUMAN":
                        data["input_text"] = message["kwargs"]["content"]
                        break

            # Find last AI message
            for message in reversed(outputs["messages"]):
                if "kwargs" in message and "type" in message["kwargs"] and message["kwargs"]["type"].upper() == "AI":
                    data["generated_text"] = message["kwargs"]["content"]
                    break
        else:
            data.update(outputs)

        metric_result = await _evaluate_metrics_async(configuration=span_tree.agentic_app.metrics_configuration.configuration,
                                                      data=data,
                                                      metrics=span_tree.agentic_app.metrics_configuration.metrics,
                                                      metric_groups=span_tree.agentic_app.metrics_configuration.metric_groups,
                                                      api_client=api_client,
                                                      **kwargs)
        metric_result = metric_result.to_dict()
        for mr in metric_result:
            node_result = {
                "applies_to": "message",
                "message_id": span_tree.get_message_id(),
                "conversation_id": span_tree.get_conversation_id(),
                **mr
            }

            metric_results.append(AgentMetricResult(**node_result))

        return metric_results

    @staticmethod
    def __get_metrics_to_compute(nodes_config, node_name, metrics_configurations):
        metrics_to_compute, all_metrics_config = [], []

        if nodes_config.get(node_name):
            metrics_config = nodes_config.get(node_name)
            for mc in metrics_config:
                mc_obj = MetricsConfiguration(configuration=mc.configuration,
                                              metrics=mc.metrics,
                                              metric_groups=mc.metric_groups)
                metrics_to_compute.append(mc_obj)
                all_metrics_config.append(mc_obj)

        for mc in metrics_configurations:
            mc_obj = MetricsConfiguration.model_validate(
                mc.get("metrics_configuration"))

            all_metrics_config.append(mc_obj)
            if mc.get("compute_real_time") == "false":
                metrics_to_compute.append(mc_obj)

        return metrics_to_compute, all_metrics_config

    @staticmethod
    def __get_metrics_results_from_events(events, message_id, conversation_id, node_name, execution_count, execution_order):
        results = []
        if not events:
            return results

        for event in events:
            for attr in event.attributes:
                if attr.key == "attr_wxgov.result.metric":
                    val = attr.value.string_value
                    if val:
                        mr = json.loads(val)
                        mr.update({
                            "node_name": node_name,
                            "message_id": message_id,
                            "conversation_id": conversation_id,
                            "execution_count": execution_count,
                            "execution_order": execution_order
                        })
                        results.append(AgentMetricResult(**mr))

        return results

    @staticmethod
    def __compute_usage_metrics_from_trace_metadata(trace_metadata: dict, message_id: str, conversation_id: str) -> list:
        metrics_result = []

        for metric, data in trace_metadata.items():
            if metric == "cost":
                metric_value = TraceUtils.calculate_cost(data)
            elif metric == "input_token_count":
                metric_value = sum(data)
            elif metric == "output_token_count":
                metric_value = sum(data)
            else:
                continue
            agent_mr = {
                "name": metric,
                "value": metric_value,
                "display_name": metric,
                "message_id": message_id,
                "applies_to": "message",
                "conversation_id": conversation_id,
                "group": MetricGroup.USAGE.value
            }

            metrics_result.append(AgentMetricResult(**agent_mr))

        return metrics_result

    @staticmethod
    def __get_run_metadata_from_span(span: Span) -> dict:
        """
        Extract run specific metadata from traces
        1. Foundation model involved in run
        2. Tools involved in run
        """
        metadata = {}
        attributes = get_attributes(span.attributes)
        provider = attributes.get(
            "traceloop.association.properties.ls_provider", attributes.get("gen_ai.system"))
        llm_type = attributes.get("llm.request.type")
        model_name = attributes.get("gen_ai.request.model")

        if model_name:
            metadata["foundation_models"] = FoundationModelInfo(
                model_name=model_name, provider=provider, type=llm_type
            )

        return metadata

    @staticmethod
    async def __process_span_and_extract_data(span_tree: SpanNode, metric_mappings: List[MetricMapping], **kwargs
                                              ) -> Tuple[MessageData, List[NodeData], MetricsMappingData, List[Node], List[AgentMetricResult], Dict]:
        """
        Extract and process span tree data to generate metrics, node information, and mapping data.

        This method traverses a span tree extracting:
        - Usage duration metrics
        - Node information and I/O data
        - Experiment run metadata
        - Metric mapping data
        - Application I/O data
        """
        root_span = span_tree.span
        conversation_id = str(span_tree.get_conversation_id())
        message_id = str(span_tree.get_message_id())

        app_io_start_time = TraceUtils._timestamp_to_iso(
            root_span.start_time_unix_nano)
        app_io_end_time = TraceUtils._timestamp_to_iso(
            root_span.end_time_unix_nano)

        app_io_data = TraceUtils._extract_app_io_from_attributes(
            root_span.attributes)

        # Initialize data structures
        metrics_from_traces = []
        trace_metadata = defaultdict(list)
        experiment_run_metadata = defaultdict(lambda: defaultdict(set))
        nodes_list = []
        node_execution_count = {}
        nodes_data = []
        node_metric_map = {}

        # Build quick index for span name to mapping items lookup
        span_mapping_items = defaultdict(list)
        for metric_mapping in metric_mappings:
            for mapping_item in metric_mapping.mapping.items:
                if mapping_item.span_name:
                    span_mapping_items[mapping_item.span_name].append(
                        mapping_item)
        metric_map_data = defaultdict(
            lambda: defaultdict(lambda: defaultdict()))

        # Process span tree using iterative DFS
        TraceUtils._process_span_tree(
            span_tree=span_tree,
            root_span=root_span,
            conversation_id=conversation_id,
            message_id=message_id,
            app_io_data=app_io_data,
            span_mapping_items=span_mapping_items,
            metrics_from_traces=metrics_from_traces,
            trace_metadata=trace_metadata,
            experiment_run_metadata=experiment_run_metadata,
            nodes_list=nodes_list,
            node_execution_count=node_execution_count,
            nodes_data=nodes_data,
            metric_map_data=metric_map_data
        )

        # Compute usage metrics from trace metadata
        usage_metrics = TraceUtils.__compute_usage_metrics_from_trace_metadata(
            trace_metadata, message_id, conversation_id
        )
        metrics_from_traces.extend(usage_metrics)

        # Prepare message data
        messages_data = MessageData(
            message_id=message_id,
            message_ts=app_io_end_time,
            conversation_id=conversation_id,
            start_time=app_io_start_time,
            end_time=app_io_end_time,
            input=TraceUtils._string_to_bytes(app_io_data["input"]),
            output=TraceUtils._string_to_bytes(app_io_data["output"]),
            num_loops=sum(node_execution_count.values()) -
            len(node_execution_count)
        )

        metric_mapping_data = MetricsMappingData(
            message_id=message_id,
            metric_mappings=metric_mappings,
            data=metric_map_data
        )

        return (
            messages_data,
            nodes_data,
            metric_mapping_data,
            nodes_list,
            metrics_from_traces,
            experiment_run_metadata,
            node_execution_count,
        )

    @staticmethod
    def _timestamp_to_iso(timestamp_ns: int) -> str:
        """Convert nanosecond timestamp to ISO format string."""
        return datetime.fromtimestamp(timestamp_ns / 1e9).isoformat()

    @staticmethod
    def _extract_app_io_from_attributes(attributes: List) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract application input and output from span attributes.
        """
        app_input = None
        app_output = None

        for attribute in attributes:
            att_key = attribute.key
            att_val = attribute.value.string_value

            if att_key == "traceloop.entity.input":
                app_input = TraceUtils._safe_json_dumps(att_val)
            elif att_key == "traceloop.entity.output":
                app_output = TraceUtils._safe_json_dumps(att_val)

        return {"input": app_input, "output": app_output}

    @staticmethod
    def _safe_json_dumps(value: str) -> str:
        """
        Safely JSON dump a string value only if it's not already JSON-formatted.
        """
        if value and '\\"' not in value:
            try:
                return json.dumps(value)
            except (TypeError, ValueError):
                return value
        return value

    @staticmethod
    def _string_to_bytes(text: Optional[str]) -> Optional[bytes]:
        """Convert string to bytes if not None."""
        return bytes(text, "utf-8") if text is not None else None

    @staticmethod
    def _process_span_tree(span_tree: SpanNode, root_span: Span, conversation_id: str, message_id: str, app_io_data: Dict, span_mapping_items: defaultdict[str, list[MappingItem]],
                           metrics_from_traces: List[AgentMetricResult], trace_metadata: defaultdict[str, list], experiment_run_metadata: defaultdict[str, defaultdict[str, set]],
                           nodes_list: List[Node], node_execution_count: Dict[str, int], nodes_data: List[NodeData], metric_map_data: defaultdict
                           ) -> None:
        """
        Process the span tree using iterative depth-first search.
        """
        node_stack: List[SpanNode] = [span_tree]
        child_stack: List[SpanNode] = []
        current_parent_context = {}

        while node_stack or child_stack:
            is_parent = not child_stack
            node = child_stack.pop() if child_stack else node_stack.pop()
            current_span = node.span

            if not current_span.name:
                # No data to extract from current span
                continue
            if is_parent:
                current_parent_context = TraceUtils._initialize_parent_context(
                    node)

            # Process span attributes for I/O data and metric mappings
            TraceUtils._process_span_attributes(
                current_span=current_span,
                is_parent=is_parent,
                parent_context=current_parent_context,
                span_mapping_items=span_mapping_items,
                metric_map_data=metric_map_data
            )

            if current_parent_context.get("name") == "__start__":
                if app_io_data["input"] is None:
                    # Reading the application input from `__start__` node
                    app_io_data["input"] = current_parent_context["input"]
                    # No data to extract from current span
                    continue

            # Extract metadata for usage metrics
            if current_span.name in TARGETED_USAGE_TRACE_NAMES:
                usage_meta = TraceUtils.__extract_usage_meta_data(current_span)
                for key, value in usage_meta.items():
                    trace_metadata[key].append(value)

            # Extract experiment run metadata
            run_metadata = TraceUtils.__get_run_metadata_from_span(
                current_span)
            for key, value in run_metadata.items():
                experiment_run_metadata[current_parent_context.get(
                    "name")][key].add(value)

            if current_span == root_span:
                # Add node to stack for processing
                node_stack = span_tree.children
            else:
                # Add children to stack for processing
                child_stack.extend(node.children)

            # Node process completed when all children are processed
            if not child_stack:
                if current_parent_context.get("span") == root_span:
                    # Add message duration metric
                    duration = (int(current_parent_context.get("span").end_time_unix_nano) -
                                int(current_parent_context.get("span").start_time_unix_nano)) / 1e9
                    metrics_from_traces.append(AgentMetricResult(
                        name="duration",
                        display_name="Duration",
                        value=duration,
                        group=MetricGroup.PERFORMANCE,
                        applies_to="message",
                        message_id=message_id,
                        conversation_id=conversation_id,
                    ))
                else:
                    TraceUtils._finalize_node_processing(
                        parent_context=current_parent_context,
                        conversation_id=conversation_id,
                        message_id=message_id,
                        node_execution_count=node_execution_count,
                        nodes_list=nodes_list,
                        nodes_data=nodes_data,
                        metrics_from_traces=metrics_from_traces,
                    )

    @staticmethod
    def _initialize_parent_context(node: SpanNode) -> Dict:
        """
        Initialize context for a parent node.
        """
        parent_span = node.span
        return {
            "span": parent_span,
            "txn_id": str(uuid.uuid4()),
            "execution_order": None,
            "name": None,
            "input": None,
            "output": None,
            "metrics_config": [],
            "code_id": "",
            "start_time": TraceUtils._timestamp_to_iso(parent_span.start_time_unix_nano),
            "end_time": TraceUtils._timestamp_to_iso(parent_span.end_time_unix_nano)
        }

    @staticmethod
    def _process_span_attributes(current_span: Span, is_parent: bool, parent_context: Dict, span_mapping_items: defaultdict[str, list[MappingItem]], metric_map_data: defaultdict
                                 ) -> None:
        """
        Process attributes of the current span for I/O data and metric mappings.
        """
        has_metric_mapping = current_span.name and current_span.name in span_mapping_items

        if is_parent or has_metric_mapping:
            for attr in current_span.attributes:
                key = attr.key
                value = attr.value

                if is_parent:
                    TraceUtils._process_parent_attribute(
                        key, value, parent_context)

                if has_metric_mapping:
                    TraceUtils._process_metric_mapping(
                        current_span.name, key, value,
                        span_mapping_items[current_span.name],
                        metric_map_data
                    )

    @staticmethod
    def _process_parent_attribute(key: str, value, parent_context: Dict) -> None:
        """
        Process an attribute for a parent node.
        """
        if key == "traceloop.entity.name":
            parent_context["name"] = value.string_value
        elif key == "gen_ai.runnable.code_id":
            parent_context["code_id"] = value.string_value
        elif key == "traceloop.association.properties.langgraph_step":
            parent_context["execution_order"] = int(
                value.int_value) if value else None
        elif key in ("traceloop.entity.input", "traceloop.entity.output"):
            try:
                processed_value = TraceUtils._safe_json_dumps(
                    value.string_value)
                if key.endswith("input"):
                    parent_context["input"] = processed_value
                else:
                    parent_context["output"] = processed_value
            except Exception as e:
                raise Exception(
                    "Unable to parse JSON string from attribute") from e

    @staticmethod
    def _process_metric_mapping(span_name: str, attr_key: str, attr_value, mapping_items: List[MappingItem], metric_map_data: defaultdict
                                ) -> None:
        """
        Process metric mapping for a span attribute.
        """
        for mapping_item in mapping_items:
            if attr_key == mapping_item.attribute_name:
                try:
                    content = json.loads(attr_value.string_value)

                    content = TraceUtils._parse_nested_json_fields(
                        content, ["inputs", "outputs"])

                    if mapping_item.json_path:
                        extracted_value = TraceUtils._extract_with_jsonpath(
                            content, mapping_item.json_path)
                    else:
                        extracted_value = content

                    metric_map_data[span_name][attr_key][mapping_item.json_path] = extracted_value

                except (json.JSONDecodeError, AttributeError):
                    # Fallback to string value if JSON parsing fails
                    metric_map_data[span_name][attr_key][mapping_item.json_path] = attr_value.string_value

    @staticmethod
    def _parse_nested_json_fields(content: Dict, fields: List[str]) -> Dict:
        """
        Parse nested JSON strings in specified fields.
        """
        result = content.copy()

        for field in fields:
            if field in result and isinstance(result[field], str):
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    # Leave as original string if not valid JSON
                    pass

        return result

    @staticmethod
    def _extract_with_jsonpath(content: Dict, json_path: str) -> Any:
        """
        Extract value from content using JSONPath expression.
        """
        try:
            jsonpath_expr = parse_jsonpath(json_path)
            matches = [match.value for match in jsonpath_expr.find(content)]

            if matches:
                return matches[0] if len(matches) == 1 else matches
            return None
        except Exception:
            return None

    @staticmethod
    def _finalize_node_processing(parent_context: Dict, conversation_id: str, message_id: str, node_execution_count: Dict[str, int], nodes_list: List[Node], nodes_data: List[NodeData],
                                  metrics_from_traces: List[AgentMetricResult]
                                  ) -> None:
        """
        Finalize processing for a completed node.
        """
        node_name = parent_context["name"]

        # Update execution count
        node_execution_count[node_name] = node_execution_count.get(
            node_name, 0) + 1

        # Add unique node to nodes list
        func_name = parent_context["code_id"].split(
            ":")[-1] if parent_context["code_id"] else node_name
        add_if_unique(
            Node(
                name=node_name,
                func_name=func_name
            ),
            nodes_list,
            ["name", "func_name"]
        )

        # Add node I/O data
        nodes_data.append(NodeData(
            message_id=message_id,
            message_ts=parent_context["end_time"],
            conversation_id=conversation_id,
            node_name=node_name,
            start_time=parent_context["start_time"],
            end_time=parent_context["end_time"],
            input=TraceUtils._string_to_bytes(parent_context["input"]),
            output=TraceUtils._string_to_bytes(parent_context["output"]),
            execution_order=parent_context["execution_order"],
            execution_count=node_execution_count[node_name],
            node_txn_id=parent_context["txn_id"],
            node_txn_timestamp=parent_context["end_time"]
        ))

        # Add node latency metric
        latency = (int(parent_context["span"].end_time_unix_nano) -
                   int(parent_context["span"].start_time_unix_nano)) / 1e9

        metrics_from_traces.append(AgentMetricResult(
            name="latency",
            display_name="Latency",
            value=latency,
            group=MetricGroup.PERFORMANCE,
            applies_to="node",
            message_id=message_id,
            conversation_id=conversation_id,
            node_name=node_name,
            execution_count=node_execution_count.get(node_name),
            execution_order=parent_context["execution_order"]
        ))

    @staticmethod
    async def __compute_metrics_from_maps(metrics_configuration: MetricsConfiguration, mapping_data: Dict, api_client: APIClient, message_id: str, conversation_id: str,
                                          node_execution_count: Dict, **kwargs) -> List[AgentMetricResult]:
        """
        Process all configured metrics by:
        1. Extracting required data from mapping data
        2. Computing metrics asynchronously
        """
        coros = []
        metric_results = []
        for metric in metrics_configuration.metrics:
            # Extract relevant data for this metric
            data = mapping_to_df(metric.mapping, mapping_data)
            coros.append(_evaluate_metrics_async(
                configuration=metrics_configuration.configuration,
                data=data,
                metrics=[metric],
                api_client=api_client,
                **kwargs))

        results = await gather_with_concurrency(coros, max_concurrency=kwargs.get("max_concurrency", 10))
        for i, metric_result in enumerate(results):
            metric = metrics_configuration.metrics[i]
            for mr in metric_result.to_dict():
                node_result = {
                    "applies_to": metric.applies_to,
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                    # TODO: Metric-to-node mapping unavailable - all metrics are configured at the agent level
                    # "node_name": "<node_name>",
                    # "execution_count": node_execution_count.get("<node_name>"),
                    # "execution_order": "<execution_order>",
                    **mr
                }
                metric_results.append(AgentMetricResult(**node_result))

        return metric_results

    @staticmethod
    async def compute_metrics_from_trace_async_v2(span_tree: SpanNode, metrics_configuration: MetricsConfiguration, api_client: APIClient = None, **kwargs
                                                  ) -> Tuple[List[AgentMetricResult], MessageData, List[NodeData], MetricsMappingData, List[Node]]:
        """
        Process span tree data to compute comprehensive metrics and extract execution artifacts.

        This method orchestrates the end-to-end metrics computation pipeline by:
        1. Extracting and processing raw data from span traces
        2. Computing metrics from the extracted trace data  
        3. Calculating additional metrics based on mapping configurations
        """

        metric_results = []
        # Assuming both the message and node level mappings are available in `agentic_app.metrics_configuration`
        metric_mappings = []
        for m in metrics_configuration.metrics:
            metric_mappings.append(MetricMapping(
                name=m.name, method=m.method, applies_to=m.applies_to, mapping=m.mapping))

        # Extract and process core data components from span tree
        message_data, node_data, metric_mapping_data, nodes, metrics_from_traces, experiment_run_metadata, node_execution_count = await TraceUtils.__process_span_and_extract_data(span_tree, metric_mappings, **kwargs)

        # Compute metrics using mapping configurations
        metrics_from_mapping = await TraceUtils.__compute_metrics_from_maps(metrics_configuration, metric_mapping_data.data, api_client, message_data.message_id, message_data.conversation_id, node_execution_count, **kwargs)

        # Add foundation model details to node
        for node in nodes:
            if node.name in experiment_run_metadata:
                node.foundation_models = list(
                    experiment_run_metadata[node.name]["foundation_models"])

        metric_results = metrics_from_traces + metrics_from_mapping

        return metric_results, message_data, node_data, metric_mapping_data, nodes
