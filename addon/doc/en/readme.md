# AI Translator

AI Translator is an NVDA add-on that translates selected text or clipboard text
through an OpenAI-compatible Chat Completions API.

Author: [denis-skripnik](https://github.com/denis-skripnik)

## Features

- `NVDA+Shift+T`: translate selected text.
- `NVDA+Shift+Y`: translate text from the clipboard.
- Speaks the translated text and copies it to the clipboard.
- Lets you choose OpenAI, OpenRouter, Nous, or a custom API URL.
- Lets you choose preset models for each provider or enter a custom model ID.
- Lets you choose target and reverse-translation languages from preset lists or enter custom values.
- Shows a help link at the top of the settings panel.
- If the input text is already in the target language, the add-on translates it into the reverse language.
- Lets you configure API key, model, target language, reverse language, and timeout.
- Supports gesture reassignment through NVDA Input Gestures.

## Setup

1. Install the add-on in NVDA.
2. Open `NVDA menu -> Preferences -> Settings -> AI Translator`.
3. Fill in:
   - `Chat Completions API URL`
   - `API key`
   - `Model`
   - `Target language`
   - `Reverse translation language`
   - `Timeout in seconds`

The default API URL is `https://api.openai.com/v1/chat/completions`.

## Usage

To translate selected text:

1. Select text in any accessible control.
2. Press `NVDA+Shift+T`.

To translate clipboard text:

1. Copy text to the clipboard.
2. Press `NVDA+Shift+Y`.

After a successful request, the add-on speaks the translation and places it in
the clipboard.

## Security Notes

- The add-on uses Python's standard library only. It does not bundle third-party
  packages.
- The API key is sent only to the configured Chat Completions endpoint.
- The add-on rejects non-HTTPS URLs, except `http://localhost`,
  `http://127.0.0.1`, and `http://[::1]` for local proxies or gateways.
- The API key is stored in NVDA configuration. Treat your NVDA user
  configuration as sensitive data.
- The selected text or clipboard text is sent to the configured API provider.
  Do not use the add-on for secrets unless you trust that provider.

## Limitations

- This package was syntax-checked and built, but not runtime-tested inside NVDA
  in this environment.
- Reading selected text depends on the focused control exposing a standard text
  selection through NVDA.
