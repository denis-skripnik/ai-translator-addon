from __future__ import annotations

from dataclasses import dataclass

import config


CONFIG_SECTION = "aiTranslator"

PROVIDER_OPENAI = "openai"
PROVIDER_OPENROUTER = "openrouter"
PROVIDER_NOUS = "nous"
PROVIDER_CUSTOM = "custom"

MODEL_CUSTOM = "__custom__"
LANGUAGE_CUSTOM = "__custom__"

API_URL_PRESETS = {
    PROVIDER_OPENAI: "https://api.openai.com/v1/chat/completions",
    PROVIDER_OPENROUTER: "https://openrouter.ai/api/v1/chat/completions",
    PROVIDER_NOUS: "https://inference-api.nousresearch.com/v1/chat/completions",
}

MODEL_PRESETS = {
    PROVIDER_OPENAI: [
        ("gpt-5.2", "GPT-5.2"),
        ("gpt-5-mini", "GPT-5 mini"),
        ("gpt-5-nano", "GPT-5 nano"),
        ("gpt-4.1-mini", "GPT-4.1 mini"),
    ],
    PROVIDER_OPENROUTER: [
        ("minimax/minimax-m2.5", "MiniMax M2.5"),
        ("openrouter/auto", "OpenRouter Auto"),
        ("anthropic/claude-sonnet-4.5", "Claude Sonnet 4.5"),
        ("openai/gpt-5.1", "OpenAI GPT-5.1"),
    ],
    PROVIDER_NOUS: [
        ("Hermes-4-70B", "Hermes-4-70B"),
        ("Hermes-4-405B", "Hermes-4-405B"),
    ],
}

LANGUAGE_PRESETS = [
    ("English", "English"),
    ("Russian", "Russian"),
    ("Ukrainian", "Ukrainian"),
    ("Belarusian", "Belarusian"),
    ("Polish", "Polish"),
    ("German", "German"),
    ("French", "French"),
    ("Spanish", "Spanish"),
    ("Italian", "Italian"),
    ("Portuguese", "Portuguese"),
    ("Arabic", "Arabic"),
    ("Chinese", "Chinese"),
    ("Japanese", "Japanese"),
    ("Korean", "Korean"),
]

DEFAULTS = {
    "apiUrl": API_URL_PRESETS[PROVIDER_OPENAI],
    "apiKey": "",
    "model": MODEL_PRESETS[PROVIDER_OPENAI][0][0],
    "targetLanguage": "Russian",
    "reverseTargetLanguage": "English",
    "timeoutSeconds": 45,
}

CONFIG_SPEC = {
    "apiUrl": "string(default='https://api.openai.com/v1/chat/completions')",
    "apiKey": "string(default='')",
    "model": "string(default='gpt-5.2')",
    "targetLanguage": "string(default='Russian')",
    "reverseTargetLanguage": "string(default='English')",
    "timeoutSeconds": "integer(default=45,min=5,max=300)",
}


@dataclass
class AddonSettings:
    api_url: str
    api_key: str
    model: str
    target_language: str
    reverse_target_language: str
    timeout_seconds: int


def normalize_api_url(api_url: str) -> str:
    return api_url.strip().rstrip("/").lower()


def get_provider_for_url(api_url: str) -> str:
    normalized = normalize_api_url(api_url)
    for provider_id, preset_url in API_URL_PRESETS.items():
        if normalized == normalize_api_url(preset_url):
            return provider_id
    return PROVIDER_CUSTOM


def normalize_model_id(model_id: str) -> str:
    return (
        model_id.strip()
        .replace("\u2010", "-")
        .replace("\u2011", "-")
        .replace("\u2012", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .lower()
    )


def get_model_choice_for_provider(provider_id: str, model_id: str) -> str:
    normalized = normalize_model_id(model_id)
    for candidate_model_id, _ in MODEL_PRESETS.get(provider_id, []):
        if normalized == normalize_model_id(candidate_model_id):
            return candidate_model_id
    return MODEL_CUSTOM


def normalize_language_name(language_name: str) -> str:
    return " ".join(language_name.strip().lower().split())


def get_language_choice(language_name: str) -> str:
    normalized = normalize_language_name(language_name)
    for candidate_value, _ in LANGUAGE_PRESETS:
        if normalized == normalize_language_name(candidate_value):
            return candidate_value
    return LANGUAGE_CUSTOM


def get_default_model_for_provider(provider_id: str) -> str:
    presets = MODEL_PRESETS.get(provider_id, [])
    if presets:
        return presets[0][0]
    return DEFAULTS["model"]


def _get_section():
    if CONFIG_SECTION not in config.conf.spec:
        config.conf.spec[CONFIG_SECTION] = dict(CONFIG_SPEC)
    section = config.conf[CONFIG_SECTION]
    for key, default_value in DEFAULTS.items():
        if key not in section:
            section[key] = default_value
    return section


def get_settings() -> AddonSettings:
    section = _get_section()
    return AddonSettings(
        api_url=str(section.get("apiUrl", DEFAULTS["apiUrl"])).strip(),
        api_key=str(section.get("apiKey", DEFAULTS["apiKey"])).strip(),
        model=str(section.get("model", DEFAULTS["model"])).strip(),
        target_language=str(
            section.get("targetLanguage", DEFAULTS["targetLanguage"])
        ).strip(),
        reverse_target_language=str(
            section.get("reverseTargetLanguage", DEFAULTS["reverseTargetLanguage"])
        ).strip(),
        timeout_seconds=int(section.get("timeoutSeconds", DEFAULTS["timeoutSeconds"])),
    )


def save_settings(
    api_url: str,
    api_key: str,
    model: str,
    target_language: str,
    reverse_target_language: str,
    timeout_seconds: int,
) -> None:
    section = _get_section()
    section["apiUrl"] = api_url.strip() or DEFAULTS["apiUrl"]
    section["apiKey"] = api_key.strip()
    section["model"] = model.strip() or DEFAULTS["model"]
    section["targetLanguage"] = target_language.strip() or DEFAULTS["targetLanguage"]
    section["reverseTargetLanguage"] = (
        reverse_target_language.strip() or DEFAULTS["reverseTargetLanguage"]
    )
    section["timeoutSeconds"] = max(5, min(int(timeout_seconds), 300))
    config.conf.save()
