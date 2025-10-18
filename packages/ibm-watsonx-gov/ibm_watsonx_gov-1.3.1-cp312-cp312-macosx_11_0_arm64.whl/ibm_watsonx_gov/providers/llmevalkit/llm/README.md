# LLM Client Library

This directory contains a flexible, extensible framework for working with any large-language-model (LLM) provider in a uniform way, including:

- **Unified interface** for multiple LLM providers (OpenAI, Azure OpenAI, IBM WatsonX, LiteLLM, RITS)
- **Tool calling support** across all providers with standardized response format
- **Structured output validation** with JSON Schema and Pydantic models
- **Optional dependencies** for each provider to keep installations lean
- **Robust error handling** and retry logic
- **Sync and async support** throughout
- **Observability hooks** for monitoring and debugging

```
llm/
├── __init__.py           # Main imports and provider registration
├── base.py              # Core LLMClient abstract base class
├── output_parser.py     # ValidatingLLMClient with schema enforcement
├── README.md           # This documentation
├── providers/
│   ├── openai/
│   │   └── openai.py    # OpenAI provider with structured output support
│   ├── ibm_watsonx_ai/
│   │   └── ibm_watsonx_ai.py  # IBM WatsonX provider with structured output
│   └── litellm/
│       ├── litellm.py   # LiteLLM base provider
│       ├── rits.py      # RITS-hosted models via LiteLLM
│       └── watsonx.py   # WatsonX-hosted models via LiteLLM
```

---

## Installation

Install the core library:
```bash
pip install llmevalkit
```

Install with specific provider dependencies:
```bash
# OpenAI support
pip install llmevalkit[openai]

# LiteLLM support  
pip install llmevalkit[litellm]

# IBM WatsonX support
pip install llmevalkit[ibm_watsonx_ai]
```

---

## Quick Start

```python
from llmevalkit.llm import get_llm

# Get any provider
WatsonXLiteLLMClient = get_llm("litellm.watsonx")

client = WatsonXLiteLLMClient(
    model_name="meta-llama/llama-3-3-70b-instruct"
)

# Generate text
response = client.generate("Explain quantum computing")
print(response)

# Use structured output
WatsonXLiteLLMClientOutputVal = get_llm("litellm.watsonx.output_val")
structured_client = WatsonXLiteLLMClientOutputVal(
    model_name="meta-llama/llama-3-3-70b-instruct",
    include_schema_in_system_prompt=True, # Whether to add the Json Schema to the system prompt, or not
)

from pydantic import BaseModel
class Person(BaseModel):
    name: str
    age: int

person = structured_client.generate(
    "Extract: John Doe, 30 years old",
    schema=Person,
    max_retries=2
)
print(f"Name: {person.name}, Age: {person.age}")
```

You can list all available registered llm clients with:

```python
from llmevalkit.llm import list_available_llms

print(f"Available LiteLLM providers: {list_available_llms()}")
```

Example output:

```python
"Available LiteLLM providers: ['litellm', 'litellm.output_val', 'litellm.rits', 'litellm.rits.output_val', 'litellm.watsonx', 'litellm.watsonx.output_val', 'openai.sync', 'openai.async', 'openai.sync.output_val', 'openai.async.output_val', 'azure_openai.sync', 'azure_openai.async', 'azure_openai.sync.output_val', 'azure_openai.async.output_val', 'watsonx', 'watsonx.output_val']"
```
---

## Examples

Comprehensive examples for each client are available in the `examples/llm` directory:

- **`azure_openai.py`** - Azure OpenAI client examples with Azure-specific configurations
- **`litellm_rits.py`** - LiteLLM RITS client examples with hosted models
- **`litellm_watsonx.py`** - LiteLLM WatsonX client examples with Granite models
- **`ibm_watsonx_ai.py`** - IBM WatsonX AI client examples with native IBM SDK

Each example file demonstrates:
- Basic text generation (with and without output validation)
- Tool calling functionality
- Async and sync usage patterns
- Error handling and observability hooks
- Structured output with Pydantic models and JSON schemas

To run an example:
```bash
python llmevalkit/examples/llm/azure_openai_example.py
```

---

## Core Components

### `base.py`

- **`LLMClient`**  
  The abstract foundation for any provider.  
  - Manages a registry of implementations (`register_llm`, `get_llm`).  
  - Handles initialization of the underlying SDK client.  
  - Exposes four main methods:  
    - `generate` (sync single)  
    - `generate_async` (async single)  
  - Emits observability hooks around every call (`before_generate`, `after_generate`, `error`).  
  - Requires subclasses to register their own `MethodConfig` entries (mapping "chat", "text", etc., to real SDK methods) and to implement a `_parse_llm_response(raw)` method to extract plain-text from the provider's raw response.

### `output_parser.py`

- **`ValidatingLLMClient`**  
  An extension of `LLMClient` that adds:  
  1. **Output enforcement** against a schema (JSON Schema dict, Pydantic model, or basic Python type).  
  2. Automatic **prompt injection** of system-level instructions ("Only output JSON matching this schema").  
  3. **Cleaning** of raw responses (stripping Markdown, extracting fenced JSON).  
  4. **Retries** for malformed outputs—only the bad items are retried.  
  5. Methods mirror `LLMClient` but return fully-parsed Python objects (or Pydantic instances) instead of raw text.

---

## Available Providers

All provider adapters live under `providers/`. They subclass either `LLMClient` (plain) or `ValidatingLLMClient` (with output validation), and register themselves with a name you can pass to `get_llm(...)`.

### OpenAI Adapter  
**Path:** `providers/openai/openai.py`  
**Registered names:**  
- `openai.sync` -> synchronous client
- `openai.async` -> asynchronous client
- `openai.sync.output_val` -> synchronous client with output validation
- `openai.async.output_val` -> asynchronous client with output validation

**Features:**  
- Wraps `openai.OpenAI` SDK.  
- Supports text & chat, sync & async.  
- Tool calling support with structured responses.
- Streaming support.

**Environment:**  
Set `OPENAI_API_KEY` in your environment, or pass it to the constructor.

**Example:**
```python
from llmevalkit.llm import get_llm

# Basic usage
client = get_llm("openai.sync")(api_key="your-key")
response = client.generate("Hello, world!", model="gpt-4o")

# With output validation
client = get_llm("openai.sync.output_val")(api_key="your-key")
from pydantic import BaseModel
class Person(BaseModel):
    name: str
    age: int

person = client.generate(
  "Create a person",
  model="gpt-4o",
  schema=Person,
  include_schema_in_system_prompt=True, # Whether to add the Json Schema to the system prompt, or not
)
```

### Azure OpenAI Adapter  
**Path:** `providers/openai/openai.py`  
**Registered names:**  
- `azure_openai.sync` -> synchronous client
- `azure_openai.async` -> asynchronous client
- `azure_openai.sync.output_val` -> synchronous client with output validation
- `azure_openai.async.output_val` -> asynchronous client with output validation

**Features:**  
- Wraps `openai.AzureOpenAI` SDK.  
- Supports Azure-specific configurations (endpoint, API version, deployment).  
- Tool calling support with structured responses.
- Streaming support.

**Example:**
```python
from llmevalkit.llm import get_llm

client = get_llm("azure_openai.sync")(
    api_key="your-key",
    azure_endpoint="https://your-resource.openai.azure.com/",
    api_version="2024-08-01-preview"
)
response = client.generate("Hello, world!", model="gpt-4o-2024-08-06")
```

### LiteLLM Adapter  
**Path:** `providers/litellm/litellm.py`  
**Registered names:**  
- `litellm` -> plain text adapter  
- `litellm.output_val` -> validating adapter

**Features:**  
- Wraps any model served by the `litellm` SDK.  
- Supports chat, text APIs, both sync & async.  
- The **plain** adapter returns raw strings; the **output-val** adapter enforces JSON schemas, Pydantic models, or basic types with retries.  
- Streaming support.

### RITS-Hosted LiteLLM Adapter  
**Path:** `providers/litellm/rits.py`
**Registered names:**  
- `litellm.rits` -> plain text adapter  
- `litellm.rits.output_val` -> validating adapter

**Features:**  
- Subclasses the **validating** LiteLLM adapter.  
- Automatically sets:  
  - `model_name="hosted_vllm/{model_name}"`  
  - `api_base="{RITS_API_URL}/{model_url}/v1"`  
  - `headers` with your `RITS_API_KEY`  
  - `guided_decoding_backend=XGRAMMAR`  

**Environment variables:**  
- `RITS_API_KEY` (your API key)
- `RITS_API_URL` (RITS API url)

**Example:**  
```python
from llmevalkit.llm import get_llm

client = get_llm("litellm.rits.output_val")(
    model_name="ibm-granite/granite-3.1-8b-instruct"
    model_url="granite-3-1-8b-instruct" # The short model name that is added to the url (if not given - uses rits api to get this name)
    include_schema_in_system_prompt=True, # Whether to add the Json Schema to the system prompt, or not (recommended in RITS - as the response_format in LiteLLM parameter is not working well with RITS)
)
result: int = client.generate("Compute 2+2", schema=int, max_retries=1)
```

### Watsonx-Hosted LiteLLM Adapter  
**Path:** `providers/litellm/watsonx.py`  
**Registered names:**  
- `litellm.watsonx` -> plain text adapter  
- `litellm.watsonx.output_val` -> validating adapter

**Features:**  
- Like RITS, but for IBM Watsonx.  
- Automatically prefixes `model_name="watsonx/{model_name}"`.  
- Inherits all the validation and retry logic from the validating LiteLLM base class.

**Environment variables:**  
- `WX_API_KEY`  
- `WX_PROJECT_ID`  
- `WX_URL`

**Example:**  
```python
from llmevalkit.llm import get_llm

client = get_llm("litellm.watsonx.output_val")(
    model_name="meta-llama/llama-3-3-70b-instruct"
)

class Weather(BaseModel):
    city: str
    temperature_c: float
    condition: str

weather = client.generate(
    "Return weather for Rome with 25C and sunny condition.",
    schema=Weather,
    max_retries=2,
    include_schema_in_system_prompt=True, # Whether to add the Json Schema to the system prompt, or not
)
```

### IBM WatsonX AI Adapter  
**Path:** `providers/ibm_watsonx_ai/ibm_watsonx_ai.py`  
**Registered names:**  
- `watsonx` -> plain text adapter  
- `watsonx.output_val` -> validating adapter

**Features:**  
- Wraps the native IBM WatsonX AI SDK. 
- Advanced generation parameters (temperature, etc.).

**Example:**
```python
from llmevalkit.llm import get_llm

client = get_llm("watsonx")(
    model_id="meta-llama/llama-3-3-70b-instruct",
    api_key=WATSONX_API_KEY,
    project_id=WATSONX_PROJECT_ID,
    url=WATSONX_URL,
)
response = client.generate("Explain quantum computing")
```

---

## Adding Your Own Provider

1. **Subclass** either `LLMClient` (for plain text) or `ValidatingLLMClient` (if you need schema enforcement).  
2. **Implement**  
   - `@classmethod provider_class() -> your SDK client class`  
   - `_register_methods()` to map `"chat"`, `"chat_async"`, (if available `"text"`, `"text_async"`).
   - `_parse_llm_response(raw)` to pull a single string out of the provider's raw response.

3. **Register** your class:  
   ```python
   @register_llm("myprovider")
   class MyClient(LLMClient):
       ...
   ```

4. **Use** it via the registry:  
   ```python
   from llmevalkit.llm import get_llm

   Client = get_llm("myprovider")
   client = Client(api_key="…", other_args=…)
   text = client.generate("Hello world")
   ```

---

## Tips & Best Practices

- **Hooks** let you tap into every call for logging, tracing, or metrics:  
  ```python
  client = MyClient(..., hooks=[lambda ev, data: print(ev, data)])
  ```
- **Retries** in validating mode help you guard against model hallucinations in structured outputs—set `max_retries=1` or `2` for quick corrections.
- **Keep schemas small**: only require the fields you care about to avoid brittle failures when the model adds extra metadata.
- **Tool calling** works consistently across all providers with the same interface.
- **Environment variables** can be used for API keys and configuration to keep secrets out of code.

---

## Supported Features by Provider

| Feature | OpenAI | Azure OpenAI | LiteLLM | LiteLLM RITS | LiteLLM WatsonX | IBM WatsonX AI |
|---------|---------|--------------|---------|--------------|-----------------|----------------|
| Basic Generation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Async Generation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tool Calling | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Structured Output | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Observability Hooks | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Retry Logic | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
