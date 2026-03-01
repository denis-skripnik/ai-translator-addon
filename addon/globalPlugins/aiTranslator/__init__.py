from __future__ import annotations

import threading

import addonHandler
import api
import globalPluginHandler
import scriptHandler
import textInfos
import ui
import wx
from gui.settingsDialogs import NVDASettingsDialog
from logHandler import log

from .configuration import get_settings
from .settings import AITranslatorSettingsPanel
from .translator import TranslationError, translate_text


addonHandler.initTranslation()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("AI Translator")

    def __init__(self):
        super().__init__()
        self._translationLock = threading.Lock()
        self._register_settings_panel()

    def terminate(self):
        self._unregister_settings_panel()
        super().terminate()

    @scriptHandler.script(
        description=_("Translate the selected text with AI"),
        gesture="kb:nvda+shift+t",
        category=scriptCategory,
    )
    def script_translateSelection(self, gesture):
        text = self._get_selected_text()
        if not text:
            ui.message(_("No selected text."))
            return
        self._start_translation(text)

    @scriptHandler.script(
        description=_("Translate clipboard text with AI"),
        gesture="kb:nvda+shift+y",
        category=scriptCategory,
    )
    def script_translateClipboard(self, gesture):
        text = self._get_clipboard_text()
        if not text:
            ui.message(_("Clipboard is empty or does not contain text."))
            return
        self._start_translation(text)

    def _register_settings_panel(self):
        for panelClass in list(NVDASettingsDialog.categoryClasses):
            if panelClass is AITranslatorSettingsPanel:
                continue
            if getattr(panelClass, "title", None) == AITranslatorSettingsPanel.title:
                NVDASettingsDialog.categoryClasses.remove(panelClass)
        if AITranslatorSettingsPanel not in NVDASettingsDialog.categoryClasses:
            NVDASettingsDialog.categoryClasses.append(AITranslatorSettingsPanel)

    def _unregister_settings_panel(self):
        if AITranslatorSettingsPanel in NVDASettingsDialog.categoryClasses:
            NVDASettingsDialog.categoryClasses.remove(AITranslatorSettingsPanel)

    def _get_selected_text(self) -> str:
        focus = api.getFocusObject()
        if not focus:
            return ""
        try:
            info = focus.makeTextInfo(textInfos.POSITION_SELECTION)
        except Exception:
            log.exception("AI Translator: failed to read selected text")
            return ""
        return (info.text or "").strip()

    def _get_clipboard_text(self) -> str:
        data = wx.TextDataObject()
        if not wx.TheClipboard.Open():
            return ""
        try:
            if not wx.TheClipboard.GetData(data):
                return ""
            return data.GetText().strip()
        finally:
            wx.TheClipboard.Close()

    def _start_translation(self, text: str):
        settings = get_settings()
        if not settings.api_url:
            ui.message(_("Set the API URL in AI Translator settings first."))
            return
        if not settings.api_key:
            ui.message(_("Set the API key in AI Translator settings first."))
            return
        if not settings.model:
            ui.message(_("Set the model in AI Translator settings first."))
            return
        if not settings.target_language:
            ui.message(_("Set the target language in AI Translator settings first."))
            return
        if not settings.reverse_target_language:
            ui.message(_("Set the reverse translation language in AI Translator settings first."))
            return
        if not self._translationLock.acquire(blocking=False):
            ui.message(_("Another translation is still running."))
            return

        ui.message(_("Translating"))
        worker = threading.Thread(
            target=self._translate_in_background,
            args=(text, settings),
            daemon=True,
        )
        worker.start()

    def _translate_in_background(self, text, settings):
        try:
            translated = translate_text(text, settings)
            wx.CallAfter(self._finish_success, translated)
        except TranslationError as error:
            wx.CallAfter(ui.message, _("Translation failed: {error}").format(error=error))
        except Exception:
            log.exception("AI Translator: unexpected failure")
            wx.CallAfter(ui.message, _("Translation failed because of an unexpected error."))
        finally:
            self._translationLock.release()

    def _finish_success(self, translated: str):
        copied = api.copyToClip(translated)
        ui.message(translated)
        if not copied:
            ui.message(_("Translation was spoken but could not be copied to the clipboard."))
