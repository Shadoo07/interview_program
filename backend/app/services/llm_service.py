import time

from langchain.chat_models import init_chat_model

from app.core.config import settings
from app.core.logging import get_logger
from app.core.model_presets import get_model_preset, list_model_presets, normalize_model_preset

logger = get_logger(__name__)


class LLMService:
    def __init__(self):
        self.preset_id = normalize_model_preset(settings.LLM_MODEL_PRESET)
        self.preset = get_model_preset(self.preset_id)
        self.provider = settings.LLM_PROVIDER or self.preset["provider"]
        self.api_key, self.api_key_source = self._resolve_api_key()
        self.base_url = settings.LLM_API_BASE or self.preset["base_url"] or settings.OPENAI_API_BASE
        self.model_name = settings.LLM_MODEL_NAME or self.preset["model_name"] or settings.OPENAI_MODEL_NAME
        self.timeout = settings.LLM_TIMEOUT
        self.max_retries = settings.LLM_MAX_RETRIES
        self.stats = {
            "calls": 0,
            "success": 0,
            "failures": 0,
            "fallbacks": 0,
            "last_latency_ms": None,
            "last_error": None,
        }

    def is_available(self) -> bool:
        """检查大模型是否可用"""
        return bool(settings.LLM_ENABLE_REMOTE and self.api_key and self.api_key.strip())

    def _extra_request_kwargs(self) -> dict:
        """Provider-specific request body overrides for the configured model.

        Reasoning models (e.g. qwen3.8-max) emit reasoning_content that shares
        the max_tokens budget with the actual answer, which truncates the JSON
        this app relies on. DashScope's OpenAI-compatible mode accepts
        enable_thinking=false; the switch stays off by default so models that do
        not understand the field are never sent it.
        """
        if settings.LLM_DISABLE_THINKING:
            return {"extra_body": {"enable_thinking": False}}
        return {}

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str | None:
        """
        统一的聊天接口
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数
        Returns:
            模型回复内容，失败返回None
        """
        if not self.is_available():
            self.stats["fallbacks"] += 1
            return None

        started_at = time.perf_counter()
        self.stats["calls"] += 1
        try:
            model = init_chat_model(
                model=self.model_name,
                model_provider=self.provider,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout,
                max_retries=self.max_retries,
                **self._extra_request_kwargs(),
            )
            response = model.invoke(messages)
            content = getattr(response, "content", response)
            if isinstance(content, list):
                content = "".join(str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in content)
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            self.stats["success"] += 1
            self.stats["last_latency_ms"] = latency_ms
            self.stats["last_error"] = None
            logger.info(
                "llm_call_success",
                extra={
                    "event": "llm_call",
                    "provider": self.provider,
                    "model": self.model_name,
                    "ok": True,
                    "latency_ms": latency_ms,
                },
            )
            return self._clean_content(str(content))
        except Exception as e:
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            self.stats["failures"] += 1
            self.stats["fallbacks"] += 1
            self.stats["last_latency_ms"] = latency_ms
            self.stats["last_error"] = str(e)
            logger.warning(
                "llm_call_failed",
                extra={
                    "event": "llm_call",
                    "provider": self.provider,
                    "model": self.model_name,
                    "ok": False,
                    "latency_ms": latency_ms,
                    "error": str(e),
                },
            )
            return None

    def test_connection(self) -> dict:
        """Run a small model call to verify the configured provider."""
        if not self.is_available():
            return {
                "ok": False,
                "message": "LLM remote call is disabled or API key is not configured",
                "latency_ms": None,
            }

        import time

        started_at = time.perf_counter()
        response = self.chat(
            [
                {"role": "system", "content": "You are a connection test endpoint."},
                {"role": "user", "content": "Reply with exactly: ok"},
            ],
            temperature=0,
            # Reasoning models (e.g. qwen3.8-max) spend the budget on
            # reasoning_content before emitting content, so a tiny cap like 8
            # can come back with an empty message and look like a failure.
            max_tokens=1024,
        )
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        if response:
            return {
                "ok": True,
                "message": response,
                "latency_ms": latency_ms,
            }
        return {
            "ok": False,
            "message": "Model call failed; see backend logs for provider error details",
            "latency_ms": latency_ms,
        }

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        流式聊天接口，逐块返回模型输出。
        如果模型不可用，降级为一次性返回 chat() 结果。
        """
        if not self.is_available():
            self.stats["fallbacks"] += 1
            result = self.chat(messages, temperature, max_tokens)
            if result:
                yield result
            return

        started_at = time.perf_counter()
        self.stats["calls"] += 1
        try:
            model = init_chat_model(
                model=self.model_name,
                model_provider=self.provider,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout,
                max_retries=self.max_retries,
                **self._extra_request_kwargs(),
            )
            for chunk in model.stream(messages):
                text = getattr(chunk, "content", "")
                if text:
                    yield str(text)
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            self.stats["success"] += 1
            self.stats["last_latency_ms"] = latency_ms
            self.stats["last_error"] = None
            logger.info(
                "llm_stream_success",
                extra={
                    "event": "llm_call",
                    "provider": self.provider,
                    "model": self.model_name,
                    "ok": True,
                    "latency_ms": latency_ms,
                    "streaming": True,
                },
            )
        except Exception as e:
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            self.stats["failures"] += 1
            self.stats["fallbacks"] += 1
            self.stats["last_latency_ms"] = latency_ms
            self.stats["last_error"] = str(e)
            logger.warning(
                "llm_stream_failed",
                extra={
                    "event": "llm_call",
                    "provider": self.provider,
                    "model": self.model_name,
                    "ok": False,
                    "latency_ms": latency_ms,
                    "error": str(e),
                    "streaming": True,
                },
            )

    def _clean_content(self, content: str) -> str:
        """清洗AI返回内容"""
        if not content:
            return ""
        content = content.strip()
        if content.startswith("```") and content.endswith("```"):
            lines = content.split("\n")
            if len(lines) > 2:
                content = "\n".join(lines[1:-1])
        return content

    def get_config_info(self) -> dict:
        """获取配置信息（不暴露完整API Key）"""
        return {
            "configured": self.is_available(),
            "remote_enabled": settings.LLM_ENABLE_REMOTE,
            "preset": self.preset_id,
            "preset_label": self.preset["label"],
            "provider": self.provider,
            "model_name": self.model_name,
            "base_url": self.base_url,
            "api_key_preview": self._mask_api_key(self.api_key) if self.api_key else None,
            "api_key_source": self.api_key_source,
            "available_models": list_model_presets(),
            "stats": self.stats,
        }

    def _resolve_api_key(self) -> tuple[str, str | None]:
        for field_name in self.preset.get("api_key_fields", []):
            value = getattr(settings, field_name, "")
            if value:
                return value, field_name
        if settings.LLM_API_KEY:
            return settings.LLM_API_KEY, "LLM_API_KEY"
        if settings.OPENAI_API_KEY:
            return settings.OPENAI_API_KEY, "OPENAI_API_KEY"
        return "", None

    def _mask_api_key(self, key: str) -> str:
        """隐藏API Key中间部分"""
        if not key or len(key) < 8:
            return "***"
        return f"{key[:4]}...{key[-4:]}"


llm_service = LLMService()
