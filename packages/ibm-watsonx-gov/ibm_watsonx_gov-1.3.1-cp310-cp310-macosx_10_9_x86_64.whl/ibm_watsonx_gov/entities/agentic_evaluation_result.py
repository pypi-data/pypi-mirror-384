# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------

import copy
import pandas as pd

from typing import Annotated, List, Literal, Optional
from pydantic import BaseModel, Field
from ibm_watsonx_gov.entities.agentic_app import Node

from ibm_watsonx_gov.entities.evaluation_result import AgentMetricResult, AggregateAgentMetricResult, MessageData, NodeData, MetricsMappingData

AGENTIC_RESULT_COMPONENTS = ["conversation", "message", "node"]


class AgenticEvaluationResult(BaseModel):
    metrics_results: Annotated[List[AgentMetricResult],
                               Field(title="Metrics result",
                                     description="The list of metrics result.")]
    aggregated_metrics_results: Annotated[List[AggregateAgentMetricResult],
                                          Field(title="Aggregated metrics result",
                                                description="The list of aggregated metrics result. The metrics are aggregated for each node in the agent.")]
    messages_data: Annotated[List[MessageData],
                             Field(title="Messages",
                                   description="The list of agent messages data.",
                                   default=[])]
    nodes_data: Annotated[List[NodeData],
                          Field(title="Node messages",
                                description="The list of nodes data.",
                                default=[])]
    metrics_mapping_data: Annotated[List[MetricsMappingData],
                                    Field(title="Metrics mapping data",
                                          description="The mapping data used to compute the metric.",
                                          default=[])]
    nodes: Annotated[list[Node],
                     Field(title="Nodes",
                           description="The list of nodes details",
                           default=[])]
    edges: Annotated[list[dict],
                     Field(title="Nodes",
                           description="The list of nodes details",
                           default=[])]

    def get_aggregated_metrics_results(self,
                                       applies_to: list[str] = AGENTIC_RESULT_COMPONENTS,
                                       node_name: Optional[str] = None,
                                       include_individual_results: bool = True,
                                       format: Literal["json",
                                                       "object"] = "json",
                                       **kwargs) -> list[AggregateAgentMetricResult] | list[dict]:
        """
        Get the aggregated agentic metrics results based on the specified arguments.

        Args:
            applies_to (AGENTIC_RESULT_COMPONENTS, optional): The type of component the metric result applies to. Defaults to ["conversation", "message", "node"].
            node_name (str, optional): The name of the node to get the aggregated results for. Defaults to None.
            include_individual_results (bool, optional): Whether to return the individual metrics results. Defaults to False.
            format (Literal["json", "object"], optional): The format of the output. Defaults to "json".
        Return:
            returns: list[AggregateAgentMetricResult] | list [dict]
        """

        aggregated_results = []
        for amr in self.aggregated_metrics_results:
            if amr.applies_to in applies_to and (not node_name or amr.node_name == node_name):
                if format == "json":
                    if kwargs.get("exclude_unset") is None:
                        kwargs["exclude_unset"] = True
                    if kwargs.get("exclude_none") is None:
                        kwargs["exclude_none"] = True
                    if include_individual_results:
                        aggregated_results.append(
                            amr.model_dump(mode="json", **kwargs))
                    else:
                        aggregated_results.append(
                            amr.model_dump(mode="json", exclude=["individual_results"], **kwargs))
                else:
                    aggregated_results.append(copy.deepcopy(amr))

        return aggregated_results

    def get_metrics_results(self,
                            applies_to: list[str] = AGENTIC_RESULT_COMPONENTS,
                            node_name: Optional[str] = None,
                            format: Literal["json", "object"] = "json",
                            **kwargs) -> list[AgentMetricResult] | list[dict]:
        """
        Get the agentic metrics results based on the specified arguments.

        Args:
            applies_to (AGENTIC_RESULT_COMPONENTS, optional): The type of component the metrics results applies to. Defaults to ["conversation", "message", "node"].
            node_name (str, optional): The name of the node to get the metrics results for. Defaults to None.
            format (Literal["json", "object"], optional): The format of the output. Defaults to "json".
        Return:
            returns: list[AgentMetricResult] | list [dict]
        """

        metrics_results = []
        for amr in self.metrics_results:
            if amr.applies_to in applies_to and (not node_name or amr.node_name == node_name):
                if format == "json":
                    if kwargs.get("exclude_unset") is None:
                        kwargs["exclude_unset"] = True
                    if kwargs.get("exclude_none") is None:
                        kwargs["exclude_none"] = True
                    metrics_results.append(
                        amr.model_dump(mode="json", **kwargs))
                else:
                    metrics_results.append(copy.deepcopy(amr))

        return metrics_results

    def to_json(self, **kwargs) -> dict:
        """
        Get the AgenticEvaluationResult as json

        Returns:
            dict: The AgenticEvaluationResult
        """

        if kwargs.get("exclude_unset") is None:
            kwargs["exclude_unset"] = True

        if kwargs.get("exclude_none") is None:
            kwargs["exclude_none"] = True

        return self.model_dump(mode="json", **kwargs)

    def to_df(self, input_data: Optional[pd.DataFrame] = None,
              message_id_field: str = "message_id",  wide_format: bool = True) -> pd.DataFrame:
        """
        Get individual metrics dataframe.

        If the input dataframe is provided, it will be merged with the metrics dataframe.

        Args:
            input_data (Optional[pd.DataFrame], optional): Input data to merge with metrics dataframe. Defaults to None.
            message_id_field (str, optional): Field to use for merging input data and metrics dataframe. Defaults to "message_id".
            wide_format (bool): Determines whether to display the results in a pivot table format. Defaults to True

        Returns:
            pd.DataFrame: Metrics dataframe.
        """

        def converter(m): return m.model_dump(
            exclude={"provider"}, exclude_none=True)

        metrics_df = pd.DataFrame(list(map(converter, self.metrics_results)))
        if input_data is not None:
            metrics_df = input_data.merge(metrics_df, on=message_id_field)

        # Return the metric result dataframe
        # if the wide_format is False
        if not wide_format:
            return metrics_df

        # Prepare the dataframe for pivot table view
        def col_name(row):
            if row["applies_to"] == "node":
                return f"{row['node_name']}.{row['name']}"
            if row["applies_to"] == "message":
                return f"message.{row['name']}"
            # TODO support other types

        metrics_df["idx"] = metrics_df.apply(col_name, axis=1)

        # Pivot the table
        metrics_df_wide = metrics_df.pivot_table(
            index="message_id",
            columns="idx",
            values="value"
        ).reset_index().rename_axis("", axis=1)

        # if input_data is provided add
        # it to the pivot table
        if input_data is not None:
            metrics_df_wide = input_data.merge(
                metrics_df_wide, on=message_id_field)
        return metrics_df_wide
