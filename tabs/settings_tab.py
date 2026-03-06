"""
tabs/settings_tab.py — Tab cài đặt ứng dụng.
Bố cục 2x2 grid ExpandCard: Appearance, Language, Notifications, About.
"""
from PyQt6.QtWidgets import QComboBox, QLabel, QCheckBox
from PyQt6.QtCore import Qt
from core.base_widgets import BaseTab, hbox, vbox, label, divider, form_layout
from core import theme
from core.i18n import t, set_language, get_language, get_languages
from core.theme import theme_signals
from widgets.expand_card import ExpandCard


class SettingsTab(BaseTab):
    def _build(self, layout):
        self._title_lbl = label(t("settings.title"), bold=True, size=theme.FONT_SIZE_LG)
        layout.addWidget(self._title_lbl)
        layout.addWidget(divider())

        # ── Two independent columns ─────────────────────────
        # Each column is a QVBoxLayout with AlignTop — expanding a card
        # in one column only pushes cards below it, not the adjacent column.
        columns = hbox(spacing=theme.SPACING_LG, margins=theme.MARGIN_ZERO)

        col_left = vbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        col_left.setAlignment(Qt.AlignmentFlag.AlignTop)
        col_right = vbox(spacing=theme.SPACING_MD, margins=theme.MARGIN_ZERO)
        col_right.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Card 1: Appearance (left col)
        self._card_appearance = ExpandCard(
            icon="icons/layui/template.svg",
            title=t("settings.appearance"),
            description=t("settings.appearance_desc"),
        )
        form_a = form_layout()
        self._lbl_theme = QLabel(t("settings.theme"))
        self._theme_check = QCheckBox(t("settings.dark_mode"))
        self._theme_check.setChecked(theme.is_dark())
        self._theme_check.toggled.connect(self._on_theme_changed)
        form_a.addRow(self._lbl_theme, self._theme_check)
        theme_signals.changed.connect(self._on_theme_signal)
        self._card_appearance.add_layout(form_a)
        col_left.addWidget(self._card_appearance)

        # Card 2: Notifications (left col)
        self._card_notif = ExpandCard(
            icon="icons/layui/notice.svg",
            title=t("settings.notifications"),
            description=t("settings.notifications_desc"),
        )
        form_n = form_layout()
        self._notify_check = QCheckBox(t("settings.notify_enabled"))
        self._notify_check.setChecked(True)
        form_n.addRow("", self._notify_check)
        self._notify_sound = QCheckBox(t("settings.notify_sound"))
        self._notify_sound.setChecked(True)
        form_n.addRow("", self._notify_sound)
        self._card_notif.add_layout(form_n)
        col_left.addWidget(self._card_notif)

        # Card 3: Language (right col)
        self._card_language = ExpandCard(
            icon="icons/layui/website.svg",
            title=t("settings.language_card"),
            description=t("settings.language_desc"),
        )
        form_l = form_layout()
        self._lbl_lang = QLabel(t("settings.language"))
        self._lang_combo = QComboBox()
        languages = get_languages()
        self._lang_codes = list(languages.keys())
        self._lang_combo.addItems(list(languages.values()))
        current_idx = self._lang_codes.index(get_language()) if get_language() in self._lang_codes else 0
        self._lang_combo.setCurrentIndex(current_idx)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        form_l.addRow(self._lbl_lang, self._lang_combo)
        self._lang_hint = QLabel(t("settings.language_restart"))
        self._lang_hint.setFont(theme.font(size=theme.FONT_SIZE_SM))
        form_l.addRow("", self._lang_hint)
        self._card_language.add_layout(form_l)
        col_right.addWidget(self._card_language)

        # Card 4: About (right col)
        self._card_about = ExpandCard(
            icon="icons/layui/about.svg",
            title=t("settings.about"),
            description=t("settings.about_desc"),
        )
        from utils.updater import APP_VERSION
        form_ab = form_layout()
        self._lbl_ver = QLabel(t("settings.version_label"))
        self._lbl_ver_val = QLabel(APP_VERSION)
        form_ab.addRow(self._lbl_ver, self._lbl_ver_val)
        self._lbl_author = QLabel(t("settings.author_label"))
        self._lbl_author_val = QLabel("MaxHUB Team")
        form_ab.addRow(self._lbl_author, self._lbl_author_val)
        self._lbl_license = QLabel(t("settings.license_label"))
        self._lbl_license_val = QLabel("MIT")
        form_ab.addRow(self._lbl_license, self._lbl_license_val)
        self._card_about.add_layout(form_ab)
        col_right.addWidget(self._card_about)

        columns.addLayout(col_left, 1)
        columns.addLayout(col_right, 1)
        layout.addLayout(columns)
        layout.addStretch()

    def retranslate(self) -> None:
        self._title_lbl.setText(t("settings.title"))

        # Card titles & descriptions
        self._card_appearance.set_title(t("settings.appearance"))
        self._card_appearance.set_description(t("settings.appearance_desc"))
        self._card_language.set_title(t("settings.language_card"))
        self._card_language.set_description(t("settings.language_desc"))
        self._card_notif.set_title(t("settings.notifications"))
        self._card_notif.set_description(t("settings.notifications_desc"))
        self._card_about.set_title(t("settings.about"))
        self._card_about.set_description(t("settings.about_desc"))

        # Card contents
        self._lbl_theme.setText(t("settings.theme"))
        self._theme_check.setText(t("settings.dark_mode"))
        self._lbl_lang.setText(t("settings.language"))
        self._lang_hint.setText(t("settings.language_restart"))
        self._notify_check.setText(t("settings.notify_enabled"))
        self._notify_sound.setText(t("settings.notify_sound"))
        self._lbl_ver.setText(t("settings.version_label"))
        self._lbl_author.setText(t("settings.author_label"))
        self._lbl_license.setText(t("settings.license_label"))

    def _on_language_changed(self, index: int) -> None:
        lang = self._lang_codes[index]
        set_language(lang)

    def _on_theme_changed(self, checked: bool) -> None:
        theme.set_theme(checked)

    def _on_theme_signal(self, dark: bool) -> None:
        self._theme_check.blockSignals(True)
        self._theme_check.setChecked(dark)
        self._theme_check.blockSignals(False)
