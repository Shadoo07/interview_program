from typing import Any

MODEL_PRESETS: dict[str, dict[str, Any]] = {
    "deepseek-v4-pro": {
        "label": "DeepSeek V4 Pro",
        "provider": "openai",
        "model_name": "deepseek-v4-pro",
        "base_url": "https://api.deepseek.com",
        "api_key_fields": ["DEEPSEEK_API_KEY", "LLM_API_KEY"],
    },
    "deepseek-v4-flash": {
        "label": "DeepSeek V4 Flash",
        "provider": "openai",
        "model_name": "deepseek-v4-flash",
        "base_url": "https://api.deepseek.com",
        "api_key_fields": ["DEEPSEEK_API_KEY", "LLM_API_KEY"],
    },
    "gemini-3.0-pro": {
        "label": "Gemini 3.0 Pro",
        "provider": "openai",
        "model_name": "gemini-3.0-pro",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_fields": ["GEMINI_API_KEY", "LLM_API_KEY"],
    },
    "gpt-5.5": {
        "label": "GPT-5.5",
        "provider": "openai",
        "model_name": "gpt-5.5",
        "base_url": "https://api.openai.com/v1",
        "api_key_fields": ["OPENAI_API_KEY", "LLM_API_KEY"],
    },
    "qwen3.6-plus": {
        "label": "Qwen 3.6 Plus",
        "provider": "openai",
        "model_name": "qwen3.6-plus",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_fields": ["QWEN_API_KEY", "DASHSCOPE_API_KEY", "LLM_API_KEY"],
    },
    "qwen3.8-max": {
        "label": "Qwen 3.8 Max",
        "provider": "openai",
        "model_name": "qwen3.8-max",
        # Public DashScope endpoint. A private MaaS instance should be wired up
        # through LLM_API_BASE in .env rather than hard-coded here.
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        # LLM_API_KEY first: a workspace-private MaaS instance uses its own key,
        # while a machine-wide DASHSCOPE_API_KEY (a real environment variable)
        # would otherwise take precedence over the value stored in .env.
        "api_key_fields": ["LLM_API_KEY", "QWEN_API_KEY", "DASHSCOPE_API_KEY"],
    },
    "glm-5.1": {
        "label": "GLM-5.1",
        "provider": "openai",
        "model_name": "glm-5.1",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "api_key_fields": ["GLM_API_KEY", "ZHIPU_API_KEY", "LLM_API_KEY"],
    },
}


MODEL_ALIASES = {
    "deepseek_v4_pro": "deepseek-v4-pro",
    "deepseekv4pro": "deepseek-v4-pro",
    "deepseek_v4_flash": "deepseek-v4-flash",
    "deepseekv4flash": "deepseek-v4-flash",
    "gemini3.0pro": "gemini-3.0-pro",
    "gemini_3_0_pro": "gemini-3.0-pro",
    "gpt5.5": "gpt-5.5",
    "gpt_5_5": "gpt-5.5",
    "qwen3.6plus": "qwen3.6-plus",
    "qwen_3_6_plus": "qwen3.6-plus",
    "qwen3.8max": "qwen3.8-max",
    "qwen_3_8_max": "qwen3.8-max",
    "glm5.1": "glm-5.1",
    "glm_5_1": "glm-5.1",
}


def normalize_model_preset(value: str | None) -> str:
    if not value:
        return "deepseek-v4-pro"
    normalized = value.strip().lower().replace(" ", "-")
    return MODEL_ALIASES.get(normalized, normalized)


def get_model_preset(value: str | None) -> dict[str, Any]:
    preset_id = normalize_model_preset(value)
    return MODEL_PRESETS.get(preset_id, MODEL_PRESETS["deepseek-v4-pro"])


def list_model_presets() -> list[dict[str, str]]:
    return [
        {
            "id": preset_id,
            "label": preset["label"],
            "model_name": preset["model_name"],
            "base_url": preset["base_url"],
        }
        for preset_id, preset in MODEL_PRESETS.items()
    ]
