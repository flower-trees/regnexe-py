"""LLM vendor routing — OpenAI-compatible API for all China vendors."""

from __future__ import annotations

import os
from typing import Any

from langchain_core.language_models import BaseChatModel

from .vendor import Vendor

# API key env var and base_url for each OpenAI-compatible vendor.
# Ollama is handled separately (no key, local endpoint).
_VENDOR_CONFIG: dict[Vendor, dict[str, str | None]] = {
    Vendor.ALIYUN:   {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "key_env": "ALIYUN_KEY"},
    Vendor.DEEPSEEK: {"base_url": "https://api.deepseek.com/v1",                        "key_env": "DEEPSEEK_KEY"},
    Vendor.DOUBAO:   {"base_url": "https://ark.cn-beijing.volces.com/api/v3",            "key_env": "DOUBAO_KEY"},
    Vendor.HUNYUAN:  {"base_url": "https://api.hunyuan.cloud.tencent.com/v1",           "key_env": "HUNYUAN_KEY"},
    Vendor.LINGYI:   {"base_url": "https://api.lingyiwanwu.com/v1",                     "key_env": "LINGYI_KEY"},
    Vendor.MINIMAX:  {"base_url": "https://api.minimax.chat/v1",                        "key_env": "MINIMAX_KEY"},
    Vendor.MOONSHOT: {"base_url": "https://api.moonshot.cn/v1",                         "key_env": "MOONSHOT_KEY"},
    Vendor.OPENAI:   {"base_url": None,                                                  "key_env": "OPENAI_API_KEY"},
    Vendor.QIANFAN:  {"base_url": "https://qianfan.baidubce.com/v2",                    "key_env": "QIANFAN_KEY"},
    Vendor.STEPFUN:  {"base_url": "https://api.stepfun.com/v1",                         "key_env": "STEPFUN_KEY"},
    Vendor.ZHIPU:    {"base_url": "https://open.bigmodel.cn/api/paas/v4",               "key_env": "ZHIPU_KEY"},
}


class ModelProvider:
    """Resolves (vendor, model_name) pairs to LangChain BaseChatModel instances."""

    def resolve(self, vendor: Vendor, model_name: str) -> BaseChatModel:
        if vendor == Vendor.OLLAMA:
            from langchain_ollama import ChatOllama
            return ChatOllama(model=model_name)

        config = _VENDOR_CONFIG[vendor]
        api_key = os.getenv(config["key_env"])  # type: ignore[arg-type]

        from langchain_openai import ChatOpenAI
        kwargs: dict = {"model": model_name, "api_key": api_key}
        if config["base_url"]:
            kwargs["base_url"] = config["base_url"]
        return ChatOpenAI(**kwargs)

    def resolve_from_spec(self, spec: str) -> BaseChatModel:
        """Parse a ``vendor:model_name`` string and resolve it.

        Example::

            provider.resolve_from_spec("aliyun:qwen-max")
        """
        vendor_str, _, model_name = spec.partition(":")
        if not _:
            raise ValueError(f"Invalid model spec '{spec}': expected 'vendor:model_name'")
        vendor = Vendor(vendor_str)
        return self.resolve(vendor, model_name)


def resolve_sub_agent_model(sub_agent: dict[str, Any]) -> dict[str, Any]:
    """Resolve a sub_agent["model"] of "vendor:model_name" (regnexe's own Vendor
    namespace, e.g. "aliyun:qwen-plus") to a BaseChatModel.

    deepagents accepts a bare string for "model" too, but resolves it itself via
    LangChain's init_chat_model, which uses a different provider namespace and does
    not know regnexe vendors like "aliyun"/"doubao"/etc. Resolving here keeps vendor
    routing consistent with with_default_model()/with_model_spec().

    Returns the same dict unchanged if "model" is absent or already a BaseChatModel.
    """
    model = sub_agent.get("model")
    if isinstance(model, str):
        return {**sub_agent, "model": ModelProvider().resolve_from_spec(model)}
    return sub_agent
