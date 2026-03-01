from __future__ import annotations

import os
from pathlib import Path
import webbrowser

import addonHandler
import gui
import wx
from gui.settingsDialogs import SettingsPanel
from logHandler import log

from .configuration import (
    API_URL_PRESETS,
    LANGUAGE_CUSTOM,
    LANGUAGE_PRESETS,
    MODEL_CUSTOM,
    MODEL_PRESETS,
    PROVIDER_CUSTOM,
    PROVIDER_NOUS,
    PROVIDER_OPENAI,
    PROVIDER_OPENROUTER,
    get_default_model_for_provider,
    get_language_choice,
    get_model_choice_for_provider,
    get_provider_for_url,
    get_settings,
    save_settings,
)


addonHandler.initTranslation()


class AITranslatorSettingsPanel(SettingsPanel):
    title = _("AI Translator")

    def makeSettings(self, settingsSizer):
        try:
            self._buildSettings(settingsSizer)
        except Exception:
            log.exception("AI Translator: failed to build settings panel")
            settingsSizer.Add(
                wx.StaticText(
                    self,
                    label=_(
                        "AI Translator settings could not be loaded. See NVDA log for details."
                    ),
                ),
                flag=wx.EXPAND | wx.ALL,
                border=8,
            )

    def _buildSettings(self, settingsSizer):
        settings = get_settings()
        self._providerChoices = [
            (PROVIDER_OPENAI, _("OpenAI")),
            (PROVIDER_OPENROUTER, _("OpenRouter")),
            (PROVIDER_NOUS, _("Nous")),
            (PROVIDER_CUSTOM, _("Custom")),
        ]
        self._languageChoices = [(value, _(label)) for value, label in LANGUAGE_PRESETS]
        self._customLabel = _("Custom")

        sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)

        helpLabel = wx.StaticText(self, label=_("Documentation:"))
        sHelper.addItem(helpLabel)
        self.helpButton = wx.Button(self, label=_("Open AI Translator help"))
        self.helpButton.Bind(wx.EVT_BUTTON, self._onOpenHelp)
        sHelper.addItem(self.helpButton)

        self.providerChoice = sHelper.addLabeledControl(
            _("API provider:"),
            wx.Choice,
            choices=[label for _, label in self._providerChoices],
        )
        self.apiUrlEdit = sHelper.addLabeledControl(
            _("Chat Completions API URL:"),
            wx.TextCtrl,
            value=settings.api_url,
        )
        self.apiKeyEdit = sHelper.addLabeledControl(
            _("API key:"),
            wx.TextCtrl,
            value=settings.api_key,
            style=wx.TE_PASSWORD,
        )
        self.modelChoice = sHelper.addLabeledControl(
            _("Model:"),
            wx.Choice,
            choices=[],
        )
        self.modelEdit = sHelper.addLabeledControl(
            _("Custom model:"),
            wx.TextCtrl,
            value=settings.model,
        )
        self.targetLanguageChoice = sHelper.addLabeledControl(
            _("Target language:"),
            wx.Choice,
            choices=[label for _, label in self._languageChoices] + [self._customLabel],
        )
        self.targetLanguageEdit = sHelper.addLabeledControl(
            _("Custom target language:"),
            wx.TextCtrl,
            value=settings.target_language,
        )
        self.reverseLanguageChoice = sHelper.addLabeledControl(
            _("When text is already in target language, translate into:"),
            wx.Choice,
            choices=[label for _, label in self._languageChoices] + [self._customLabel],
        )
        self.reverseLanguageEdit = sHelper.addLabeledControl(
            _("Custom reverse language:"),
            wx.TextCtrl,
            value=settings.reverse_target_language,
        )
        self.timeoutEdit = sHelper.addLabeledControl(
            _("Timeout in seconds:"),
            wx.SpinCtrl,
            min=5,
            max=300,
            initial=settings.timeout_seconds,
        )

        self.providerChoice.Bind(wx.EVT_CHOICE, self._on_provider_changed)
        self.modelChoice.Bind(wx.EVT_CHOICE, self._on_model_changed)
        self.targetLanguageChoice.Bind(wx.EVT_CHOICE, self._on_target_language_changed)
        self.reverseLanguageChoice.Bind(wx.EVT_CHOICE, self._on_reverse_language_changed)

        self.providerChoice.SetSelection(
            self._provider_index(get_provider_for_url(settings.api_url))
        )
        self._refresh_api_url()
        self._refresh_model_choices(settings.model)
        self._set_language_selection(
            self.targetLanguageChoice,
            self.targetLanguageEdit,
            settings.target_language,
        )
        self._set_language_selection(
            self.reverseLanguageChoice,
            self.reverseLanguageEdit,
            settings.reverse_target_language,
        )
        self._update_dynamic_states()

    def postInit(self):
        if hasattr(self, "providerChoice"):
            self.providerChoice.SetFocus()

    def onSave(self):
        provider = self._get_selected_provider()
        api_url = (
            self.apiUrlEdit.GetValue().strip()
            if provider == PROVIDER_CUSTOM
            else API_URL_PRESETS[provider]
        )
        save_settings(
            api_url=api_url,
            api_key=self.apiKeyEdit.GetValue(),
            model=self._get_current_model_value(),
            target_language=self._get_language_value(
                self.targetLanguageChoice,
                self.targetLanguageEdit,
            ),
            reverse_target_language=self._get_language_value(
                self.reverseLanguageChoice,
                self.reverseLanguageEdit,
            ),
            timeout_seconds=self.timeoutEdit.GetValue(),
        )

    def _provider_index(self, provider_id):
        for index, (candidate, _) in enumerate(self._providerChoices):
            if candidate == provider_id:
                return index
        return len(self._providerChoices) - 1

    def _get_selected_provider(self):
        selection = self.providerChoice.GetSelection()
        if selection == wx.NOT_FOUND:
            return PROVIDER_CUSTOM
        return self._providerChoices[selection][0]

    def _refresh_api_url(self):
        provider = self._get_selected_provider()
        if provider != PROVIDER_CUSTOM:
            self.apiUrlEdit.SetValue(API_URL_PRESETS[provider])

    def _refresh_model_choices(self, current_model):
        provider = self._get_selected_provider()
        self._modelChoices = list(MODEL_PRESETS.get(provider, []))
        self.modelChoice.Clear()
        for _, label in self._modelChoices:
            self.modelChoice.Append(label)
        self.modelChoice.Append(self._customLabel)

        model_choice = get_model_choice_for_provider(provider, current_model)
        if model_choice == MODEL_CUSTOM:
            self.modelChoice.SetStringSelection(self._customLabel)
            self.modelEdit.SetValue(current_model)
        else:
            for index, (model_id, _) in enumerate(self._modelChoices):
                if model_id == model_choice:
                    self.modelChoice.SetSelection(index)
                    break
        if self.modelChoice.GetSelection() == wx.NOT_FOUND:
            self.modelChoice.SetStringSelection(self._customLabel)
            self.modelEdit.SetValue(current_model)

    def _get_selected_model_choice(self):
        selection = self.modelChoice.GetSelection()
        if selection == wx.NOT_FOUND or selection >= len(self._modelChoices):
            return MODEL_CUSTOM
        return self._modelChoices[selection][0]

    def _get_current_model_value(self):
        selected_model = self._get_selected_model_choice()
        if selected_model == MODEL_CUSTOM:
            return self.modelEdit.GetValue().strip()
        return selected_model

    def _set_language_selection(self, choiceControl, textControl, current_value):
        choice = get_language_choice(current_value)
        if choice == LANGUAGE_CUSTOM:
            choiceControl.SetStringSelection(self._customLabel)
            textControl.SetValue(current_value)
            return
        for index, (language_value, _) in enumerate(self._languageChoices):
            if language_value == choice:
                choiceControl.SetSelection(index)
                return
        choiceControl.SetStringSelection(self._customLabel)
        textControl.SetValue(current_value)

    def _get_language_choice_value(self, choiceControl):
        selection = choiceControl.GetSelection()
        if selection == wx.NOT_FOUND or selection >= len(self._languageChoices):
            return LANGUAGE_CUSTOM
        return self._languageChoices[selection][0]

    def _get_language_value(self, choiceControl, textControl):
        choice = self._get_language_choice_value(choiceControl)
        if choice == LANGUAGE_CUSTOM:
            return textControl.GetValue().strip()
        return choice

    def _update_dynamic_states(self):
        provider = self._get_selected_provider()
        self.apiUrlEdit.Enable(provider == PROVIDER_CUSTOM)
        self.modelEdit.Enable(self._get_selected_model_choice() == MODEL_CUSTOM)
        self.targetLanguageEdit.Enable(
            self._get_language_choice_value(self.targetLanguageChoice) == LANGUAGE_CUSTOM
        )
        self.reverseLanguageEdit.Enable(
            self._get_language_choice_value(self.reverseLanguageChoice) == LANGUAGE_CUSTOM
        )

    def _on_provider_changed(self, event):
        current_model = self._get_current_model_value()
        if (
            self._get_selected_provider() != PROVIDER_CUSTOM
            and self._get_selected_model_choice() != MODEL_CUSTOM
        ):
            current_model = get_default_model_for_provider(self._get_selected_provider())
        self._refresh_api_url()
        self._refresh_model_choices(current_model)
        self._update_dynamic_states()
        event.Skip()

    def _on_model_changed(self, event):
        self._update_dynamic_states()
        event.Skip()

    def _on_target_language_changed(self, event):
        self._update_dynamic_states()
        event.Skip()

    def _on_reverse_language_changed(self, event):
        self._update_dynamic_states()
        event.Skip()

    def _build_help_path(self) -> Path:
        addon_root = Path(__file__).resolve().parents[2]
        return addon_root / "doc" / "en" / "readme.html"

    def _onOpenHelp(self, event):
        helpPath = self._build_help_path()
        try:
            os.startfile(str(helpPath))
        except Exception:
            try:
                webbrowser.open(helpPath.as_uri())
            except Exception:
                log.exception("AI Translator: failed to open help")
        event.Skip()
