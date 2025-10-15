from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field, create_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BaseStructuredOutput(BaseModel):
    confidence: ConfidenceLevel = Field(description="Confidence level in the output")
    reasoning: str = Field(description="Brief reasoning for the output")

    class Config:
        use_enum_values = True


def validate_json_schema(schema: Dict[str, Any]) -> bool:
    try:
        if "properties" not in schema:
            raise ValueError("JSON schema must contain 'properties'")
        if not isinstance(schema["properties"], dict):
            raise ValueError("'properties' must be a dictionary")

        valid_types = {"string", "integer", "number", "boolean", "array", "object"}
        for field_name, field_schema in schema["properties"].items():
            if not isinstance(field_schema, dict):
                raise ValueError(f"Property '{field_name}' must be a dictionary")
            if "type" not in field_schema:
                raise ValueError(f"Property '{field_name}' must have a 'type' field")
            if field_schema["type"] not in valid_types:
                raise ValueError(
                    f"Property '{field_name}' has invalid type: {field_schema['type']}"
                )
            if field_schema["type"] == "array" and "items" in field_schema:
                items_schema = field_schema["items"]
                if not isinstance(items_schema, dict):
                    raise ValueError(
                        f"Array items for '{field_name}' must be a dictionary"
                    )
                if "type" not in items_schema:
                    raise ValueError(
                        f"Array items for '{field_name}' must have a 'type' field"
                    )
        return True
    except Exception:
        return False


def _add_additional_properties(schema: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(schema, dict):
        return schema
    s = dict(schema)
    if s.get("type") == "object":
        s["additionalProperties"] = False
    if "properties" in s and isinstance(s["properties"], dict):
        s["properties"] = {
            k: _add_additional_properties(v) for k, v in s["properties"].items()
        }
    if "items" in s:
        s["items"] = _add_additional_properties(s["items"])  # type: ignore
    return s


def preprocess_json_schema(
    json_schema: Dict[str, Any], enforce_all_required: bool = False
) -> Dict[str, Any]:
    s = _add_additional_properties(json_schema)
    if not enforce_all_required:
        return s

    def enforce(schema: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(schema, dict):
            return schema
        x = dict(schema)
        if x.get("type") == "object" and isinstance(x.get("properties"), dict):
            props: Dict[str, Any] = x.get("properties", {})
            original_required = set(x.get("required", []))
            x["required"] = list(props.keys())
            for name, ps in list(props.items()):
                if name not in original_required and isinstance(ps, dict):
                    ps = dict(ps)
                    ps.setdefault("nullable", True)
                    props[name] = ps
                props[name] = enforce(props[name])
        if "items" in x:
            x["items"] = enforce(x["items"])  # type: ignore
        return x

    return enforce(s)


def build_model_from_schema(
    schema_name: str,
    json_schema: Dict[str, Any],
    base: Type[BaseModel] | None = None,
) -> Type[BaseModel]:
    base = base or BaseStructuredOutput

    class StrictBase(base):  # type: ignore
        class Config:
            extra = "forbid"

    def _py_type(t: str):
        return {"string": str, "integer": int, "number": float, "boolean": bool}.get(t, Any)

    def _build(node_name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
        props = schema.get("properties", {}) or {}
        required = set(schema.get("required", []))
        fields: Dict[str, tuple] = {}
        for fname, fs in props.items():
            ftype = fs.get("type")
            ann: Any
            default = ... if fname in required else None
            desc = fs.get("description", f"Field: {fname}")

            if ftype == "object":
                sub = _build(f"{node_name}_{fname.capitalize()}", fs)
                ann = sub if fname in required else Optional[sub]  # type: ignore
            elif ftype == "array":
                items = fs.get("items", {}) or {}
                if items.get("type") == "object":
                    sub = _build(f"{node_name}_{fname.capitalize()}Item", items)
                    ann = list[sub]  # type: ignore
                elif "type" in items:
                    ann = list[_py_type(items["type"])]  # type: ignore
                else:
                    ann = list[Any]
                if fname not in required:
                    from typing import Optional as Opt

                    ann = Opt[ann]  # type: ignore
            else:
                ann = _py_type(ftype)
                if fname not in required:
                    from typing import Optional as Opt

                    ann = Opt[ann]  # type: ignore
            fields[fname] = (ann, Field(default=default, description=desc))

        return create_model(node_name, __base__=StrictBase, **fields)

    payload = _build(f"{schema_name}Payload", json_schema)
    # Inline payload fields on output model so they appear at top-level
    out_fields: Dict[str, tuple] = {}
    for field_name, f in payload.model_fields.items():
        out_fields[field_name] = (
            f.annotation,
            Field(default=(... if f.is_required() else None)),
        )
    return create_model(schema_name, __base__=StrictBase, **out_fields)


def create_dynamic_schema(schema_name: str, json_schema: Dict[str, Any]) -> Type[BaseModel]:
    """Back-compat helper that mirrors existing services' API.

    Builds a strict Pydantic model from the given JSON schema that extends
    BaseStructuredOutput and forbids extra properties.
    """
    pre = preprocess_json_schema(json_schema)
    return build_model_from_schema(schema_name, pre, base=BaseStructuredOutput)


class StructuredOutputGenerator:
    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self._llm = ChatOpenAI(
            model=model or "gpt-4.1-mini",
            temperature=0,
            api_key=api_key,
            use_responses_api=True,
            output_version="responses/v1",
        )

    async def generate_from_model(
        self, prompt: str, schema_model: Type[BaseModel], system: Optional[str] = None
    ) -> BaseModel:
        tmpl = ChatPromptTemplate.from_messages(
            [
                ("system", system or "You output ONLY valid JSON for the given schema."),
                ("human", "{input}"),
            ]
        )
        chain = tmpl | self._llm.with_structured_output(schema_model)
        return await chain.ainvoke({"input": prompt})

    async def generate_from_json_schema(
        self,
        prompt: str,
        json_schema: Dict[str, Any],
        schema_name: str = "StructuredOutput",
        system: Optional[str] = None,
        enforce_all_required: bool = False,
        base: Type[BaseModel] | None = None,
    ) -> BaseModel:
        pre = preprocess_json_schema(json_schema, enforce_all_required=enforce_all_required)
        model = build_model_from_schema(schema_name, pre, base=base)
        return await self.generate_from_model(prompt, model, system=system)


async def extract_structured(
    *,
    text: str,
    json_schema: Dict[str, Any],
    schema_name: str = "DynamicSchema",
    prompt: Optional[str] = None,
    system: Optional[str] = None,
    enforce_all_required: bool = False,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> BaseModel:
    """High-level helper: from text + JSON Schema to structured model in one call.

    - Builds a strict Pydantic model (extras=forbid) from the JSON Schema.
    - Uses a default system instruction if not provided.
    - Concatenates optional `prompt` after the text for extra guidance.
    """
    gen = StructuredOutputGenerator(model=model, api_key=api_key)
    pre = preprocess_json_schema(json_schema, enforce_all_required=enforce_all_required)
    model_cls = build_model_from_schema(schema_name, pre)
    sys_msg = system or (
        "You are a helpful AI assistant that extracts information from text based on a provided JSON schema. "
        "You produce only valid JSON per the bound schema. If a field is not found, omit it when optional or set null if allowed. Do not invent values."
    )
    user = f"Text to analyze:\n{text}\n\n{prompt or ''}"
    return await gen.generate_from_model(prompt=user, schema_model=model_cls, system=sys_msg)
