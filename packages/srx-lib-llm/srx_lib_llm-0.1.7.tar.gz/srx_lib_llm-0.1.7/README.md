# srx-lib-llm

LLM helpers for SRX services built on LangChain.

What it includes:
- `responses_chat(prompt, cache=False)`: simple text chat via OpenAI Responses API
- Tool strategy base and registry
- Tavily search tool strategy
- Structured output helpers: build Pydantic model from JSON Schema and generate structured outputs via LLM
- Request models, e.g. `DynamicStructuredOutputRequest`

Designed to work with official OpenAI only.

## Install

PyPI (public):

- `pip install srx-lib-llm`

uv (pyproject):
```
[project]
dependencies = ["srx-lib-llm>=0.1.0"]
```

## Usage

```
from srx_lib_llm import responses_chat
text = await responses_chat("Hello there", cache=True)
```

Structured output from JSON Schema:
```
from srx_lib_llm import StructuredOutputGenerator, build_model_from_schema, preprocess_json_schema

json_schema = {
  "type": "object",
  "properties": {
    "title": {"type": "string"},
    "score": {"type": "number"}
  },
  "required": ["title"]
}

gen = StructuredOutputGenerator()
model = build_model_from_schema("MyOutput", preprocess_json_schema(json_schema))
result = await gen.generate_from_model("Give me a title and score", model)
print(result.model_dump())
```

All-in-one extraction:
```
from srx_lib_llm import extract_structured

result = await extract_structured(
    text="Analyze this text...", json_schema=my_schema, schema_name="MyOutput"
)
print(result.model_dump())
```

Back-compat helpers and request models:
```
from srx_lib_llm import create_dynamic_schema, DynamicStructuredOutputRequest

schema_model = create_dynamic_schema("MyOutput", json_schema)
payload = DynamicStructuredOutputRequest(text="...", json_schema=json_schema)
```

Tools:
```
from srx_lib_llm.tools import ToolStrategyBase, register_strategy, get_strategies
from srx_lib_llm.tools.tavily import TavilyToolStrategy

register_strategy(TavilyToolStrategy())
strategies = get_strategies()
```

## Environment Variables

- `OPENAI_API_KEY` (required)
- `OPENAI_MODEL` (optional, default: `gpt-4.1-nano`)
- `TAVILY_API_KEY` (optional, for the Tavily tool)

## Release

Tag `vX.Y.Z` to publish to GitHub Packages via Actions.

## License

Proprietary © SRX
