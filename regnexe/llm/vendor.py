from enum import Enum


class Vendor(Enum):
    """LLM vendors aligned with regnexe-agent and j-langchain."""
    ALIYUN   = "aliyun"
    DEEPSEEK = "deepseek"
    DOUBAO   = "doubao"
    HUNYUAN  = "hunyuan"
    LINGYI   = "lingyi"
    MINIMAX  = "minimax"
    MOONSHOT = "moonshot"
    OLLAMA   = "ollama"
    OPENAI   = "openai"
    QIANFAN  = "qianfan"
    STEPFUN  = "stepfun"
    ZHIPU    = "zhipu"
