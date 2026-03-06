"""
tabs/settings_tab.py — Tab cài đặt ứng dụng.
Chứa: language selector, theme toggle, và các tuỳ chọn chung khác.
"""
from PyQt6.QtWidgets import QComboBox, QLabel, QCheckBox
from core.base_widgets import BaseTab, group, label, divider, form_layout
from core import theme
from core.i18n import t, set_language, get_language, get_languages
from core.theme import theme_signals


class SettingsTab(BaseTab):
    def _build(self, layout):
        self._title_lbl = label(t("settings.title"), bold=True, size=theme.FONT_SIZE_LG)
        layout.addWidget(self._title_lbl)
        layout.addWidget(divider())

        self._grp, g = group(t("settings.general"))
        form = form_layout()

        # Language selector
        self._lang_combo = QComboBox()
        languages = get_languages()
        self._lang_codes = list(languages.keys())
        self._lang_combo.addItems(list(languages.values()))

        current_idx = self._lang_codes.index(get_language()) if get_language() in self._lang_codes else 0
        self._lang_combo.setCurrentIndex(current_idx)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)

        self._lbl_lang = QLabel(t("settings.language"))
        form.addRow(self._lbl_lang, self._lang_combo)

        self._lang_hint = QLabel(t("settings.language_restart"))
        self._lang_hint.setFont(theme.font(size=theme.FONT_SIZE_SM))
        form.addRow("", self._lang_hint)

        # Theme toggle
        self._theme_check = QCheckBox(t("settings.dark_mode"))
        self._theme_check.setChecked(theme.is_dark())
        self._theme_check.toggled.connect(self._on_theme_changed)
        self._lbl_theme = QLabel(t("settings.theme"))
        form.addRow(self._lbl_theme, self._theme_check)

        theme_signals.changed.connect(self._on_theme_signal)

        g.addLayout(form)
        layout.addWidget(self._grp)

        layout.addStretch()

    def retranslate(self) -> None:
        self._title_lbl.setText(t("settings.title"))
        self._grp.setTitle(t("settings.general"))
        self._lbl_lang.setText(t("settings.language"))
        self._lang_hint.setText(t("settings.language_restart"))
        self._lbl_theme.setText(t("settings.theme"))
        self._theme_check.setText(t("settings.dark_mode"))

    def _on_language_changed(self, index: int) -> None:
        lang = self._lang_codes[index]
        set_language(lang)

    def _on_theme_changed(self, checked: bool) -> None:
        theme.set_theme(checked)

    def _on_theme_signal(self, dark: bool) -> None:
        self._theme_check.blockSignals(True)
        self._theme_check.setChecked(dark)
        self._theme_check.blockSignals(False)
