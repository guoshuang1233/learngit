import json
from urllib import error, request

from django.conf import settings

from .exceptions import AIRequestError


class AIClient:
    DEFAULT_PROVIDER = "openai_compatible"
    DEFAULT_BASE_URL = "https://api.deepseek.com/chat/completions"
    DEFAULT_TIMEOUT = 60
    DEFAULT_MAX_RETRIES = 1

    def __init__(
        self,
        *,
        provider=None,
        model=None,
        api_key=None,
        base_url=None,
        timeout=None,
        max_retries=None,
        transport=None,
    ):
        self.provider = provider or getattr(settings, "AI_PROVIDER", self.DEFAULT_PROVIDER)
        self.model = model or getattr(settings, "AI_MODEL", "")
        self.api_key = api_key or getattr(settings, "AI_API_KEY", "")
        self.base_url = base_url or getattr(settings, "AI_BASE_URL", self.DEFAULT_BASE_URL)
        self.timeout = timeout or getattr(settings, "AI_TIMEOUT", self.DEFAULT_TIMEOUT)
        self.max_retries = max_retries or getattr(settings, "AI_MAX_RETRIES", self.DEFAULT_MAX_RETRIES)
        self.transport = transport

    def generate_text(
        self,
        user_prompt,
        *,
        system_prompt="",
        temperature=0.2,
        max_tokens=None,
        response_format=None,
        extra_payload=None,
    ):
        payload = self._build_payload(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            extra_payload=extra_payload,
        )
        response_data = self._request_completion(payload)
        return self._extract_content(response_data)

    def _build_payload(
        self,
        *,
        user_prompt,
        system_prompt,
        temperature,
        max_tokens=None,
        response_format=None,
        extra_payload=None,
    ):
        if not self.model:
            raise AIRequestError("AI_MODEL is not configured")

        messages = []
        if system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": user_prompt.strip()})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if response_format:
            payload["response_format"] = response_format
        if extra_payload:
            payload.update(extra_payload)
        return payload

    def _request_completion(self, payload):
        if self.transport is not None:
            return self.transport(payload)
        if not self.api_key:
            raise AIRequestError("AI_API_KEY is not configured")

        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.base_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        last_error = None
        for _ in range(self.max_retries):
            try:
                with request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "ignore")
                last_error = AIRequestError(f"AI HTTP {exc.code}: {detail[:500]}")
            except error.URLError as exc:
                last_error = AIRequestError(f"AI network error: {exc}")
            except Exception as exc:
                last_error = AIRequestError(f"AI request failed: {exc}")

        raise last_error or AIRequestError("AI request failed")

    @staticmethod
    def _extract_content(response_data):
        try:
            return response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIRequestError("Invalid AI response format") from exc
