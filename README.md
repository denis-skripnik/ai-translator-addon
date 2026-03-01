# AI Translator

AI Translator is an NVDA add-on that translates selected text or clipboard text
through an OpenAI-compatible Chat Completions API.

Author: [denis-skripnik](https://github.com/denis-skripnik)

## Features

- OpenAI-compatible translation requests over `chat/completions`
- API provider presets for OpenAI, OpenRouter, and Nous
- Custom API URL and custom model support
- Target language and reverse-translation language selection
- Translation of selected text and clipboard text

## Structure

- `addon/globalPlugins/aiTranslator/`: global plugin source
- `addon/doc/en/`: bundled add-on documentation
- `buildVars.py`: add-on metadata
- `manifest.ini.tpl`: manifest template
- `build_addon.py`: packaging script
- `dist/`: generated `.nvda-addon` packages

## Build

Run from this directory:

```bash
python build_addon.py
```

The build script outputs the `.nvda-addon` file to `dist/`.

## Notes

- `__pycache__` folders are not part of the source tree and are ignored.
- Build artifacts are written to `aiTranslator/dist/`.
