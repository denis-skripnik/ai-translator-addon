from __future__ import annotations

import json
import urllib.error
import urllib.request
from urllib.parse import urlparse

from .configuration import AddonSettings


class TranslationError(RuntimeError):
    pass


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_api_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def translate_text(text: str, settings: AddonSettings) -> str:
    _validate_api_url(settings.api_url)
    payload = {
        "model": settings.model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a translation engine. If the user's text is already "
                    f"primarily written in {settings.target_language}, translate it "
                    f"into {settings.reverse_target_language}. Otherwise translate "
                    f"it into {settings.target_language}. Preserve meaning, tone, "
                    "list structure, code blocks, inline code, URLs, and proper "
                    "names when appropriate. Return only the translated text."
                ),
            },
            {
                "role": "user",
                "content": text,
            },
        ],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.api_key}",
    }
    request = urllib.request.Request(
        settings.api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        opener = urllib.request.build_opener(_SafeRedirectHandler)
        with opener.open(request, timeout=settings.timeout_seconds) as response:
            charset = response.headers.get_content_charset("utf-8")
            response_data = json.loads(response.read().decode(charset))
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", "replace")
        raise TranslationError(_extract_http_error(details) or f"HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise TranslationError(str(error.reason)) from error
    except Exception as error:
        raise TranslationError(str(error)) from error

    try:
        content = response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise TranslationError("The API response does not contain translated text.") from error

    translated = _normalize_content(content)
    if not translated:
        raise TranslationError("The model returned an empty response.")
    return translated


def _validate_api_url(api_url: str) -> None:
    parsed = urlparse(api_url)
    if parsed.scheme == "https":
        return
    if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}:
        return
    raise TranslationError(
        "The API URL must use HTTPS, or HTTP only for localhost."
    )


def _extract_http_error(details: str) -> str:
    try:
        payload = json.loads(details)
    except Exception:
        return details.strip()
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if message:
            return str(message)
    if isinstance(error, str):
        return error
    return details.strip()


def _normalize_content(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "".join(parts).strip()
    return str(content).strip()
