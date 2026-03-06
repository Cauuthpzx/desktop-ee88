"""
dialogs/update_dialog.py — Modern update dialog.

Shows update info (version, changelog), download progress with cancel,
hash verification status. Trusted Windows-style UX.

Usage:
    from dialogs.update_dialog import UpdateDialog

    dlg = UpdateDialog(parent, update_info)
    dlg.exec()  # handles everything: prompt → download → apply
"""
from __future__ import annotations

import logging

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QSizePolicy,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from core import theme
from core.base_widgets import hbox, vbox, divider
from core.i18n import t
from utils.thread_worker import Worker

logger = logging.getLogger(__name__)

# Dialog states
_STATE_PROMPT = "prompt"
_STATE_DOWNLOADING = "downloading"
_STATE_VERIFYING = "verifying"
_STATE_READY = "ready"
_STATE_ERROR = "error"


class UpdateDialog(QDialog):
    """
    All-in-one update dialog: prompt → download → verify → apply.

    Args:
        parent: Parent widget
        info: Update info dict from check_update()
            {version, update_url, sha256, changelog, force, file_size}
    """

    def __init__(self, parent: QWidget, info: dict) -> None:
        super().__init__(parent)
        self._info = info
        self._state = _STATE_PROMPT
        self._cancel_flag: list[bool] = [False]
        self._worker: Worker | None = None
        self._downloaded_path: str = ""

        self.setWindowTitle(t("update.title"))
        self.setMinimumWidth(480)
        self.setMaximumWidth(560)
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._build_ui()
        self._update_state(_STATE_PROMPT)

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(*theme.MARGIN_DIALOG)
        lay.setSpacing(theme.SPACING_LG)

        # ── Header — icon + version info ──────────────────────
        header = QHBoxLayout()
        header.setSpacing(theme.SPACING_LG)

        icon_lbl = QLabel()
        from core.icon import Icon
        icon_lbl.setPixmap(Icon.REFRESH.pixmap(40, 40))
        icon_lbl.setFixedSize(40, 40)
        header.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignTop)

        info_lay = QVBoxLayout()
        info_lay.setSpacing(theme.SPACING_XS)

        self._title_lbl = QLabel(
            t("update.available_title", version=self._info["version"])
        )
        self._title_lbl.setFont(theme.font(size=theme.FONT_SIZE_LG, bold=True))
        self._title_lbl.setWordWrap(True)
        info_lay.addWidget(self._title_lbl)

        from utils.updater import APP_VERSION
        self._subtitle_lbl = QLabel(
            t("update.version_info", current=APP_VERSION, new=self._info["version"])
        )
        self._subtitle_lbl.setFont(theme.font(size=theme.FONT_SIZE_SM))
        self._subtitle_lbl.setEnabled(False)
        info_lay.addWidget(self._subtitle_lbl)

        # File size if available
        file_size = self._info.get("file_size", 0)
        if file_size > 0:
            size_mb = file_size / (1024 * 1024)
            size_text = f"{size_mb:.1f} MB"
            self._size_lbl = QLabel(
                t("update.file_size", size=size_text)
            )
            self._size_lbl.setFont(theme.font(size=theme.FONT_SIZE_SM))
            self._size_lbl.setEnabled(False)
            info_lay.addWidget(self._size_lbl)

        header.addLayout(info_lay, 1)
        lay.addLayout(header)

        # ── Changelog ─────────────────────────────────────────
        changelog = self._info.get("changelog", "")
        if changelog:
            lay.addWidget(divider())
            cl_label = QLabel(t("update.changelog"))
            cl_label.setFont(theme.font(bold=True))
            lay.addWidget(cl_label)

            self._changelog = QTextEdit()
            self._changelog.setReadOnly(True)
            self._changelog.setPlainText(changelog)
            self._changelog.setMaximumHeight(140)
            self._changelog.setFont(theme.font(size=theme.FONT_SIZE_SM))
            lay.addWidget(self._changelog)

        # ── Progress section (hidden initially) ───────────────
        self._progress_widget = QWidget()
        p_lay = QVBoxLayout(self._progress_widget)
        p_lay.setContentsMargins(*theme.MARGIN_ZERO)
        p_lay.setSpacing(theme.SPACING_SM)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        p_lay.addWidget(self._progress_bar)

        self._status_lbl = QLabel()
        self._status_lbl.setFont(theme.font(size=theme.FONT_SIZE_SM))
        self._status_lbl.setEnabled(False)
        p_lay.addWidget(self._status_lbl)

        self._progress_widget.hide()
        lay.addWidget(self._progress_widget)

        # ── Buttons ───────────────────────────────────────────
        lay.addWidget(divider())
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(theme.SPACING_MD)

        # Force update warning
        if self._info.get("force"):
            force_lbl = QLabel(t("update.force_notice"))
            force_lbl.setFont(theme.font(size=theme.FONT_SIZE_SM))
            force_lbl.setStyleSheet("color: #e74c3c;")
            btn_lay.addWidget(force_lbl)

        btn_lay.addStretch()

        self._btn_later = QPushButton(t("update.later"))
        self._btn_later.clicked.connect(self._on_later)
        btn_lay.addWidget(self._btn_later)

        self._btn_action = QPushButton(t("update.download_install"))
        self._btn_action.setDefault(True)
        self._btn_action.clicked.connect(self._on_action)
        btn_lay.addWidget(self._btn_action)

        lay.addLayout(btn_lay)

    # ── State machine ────────────────────────────────────────

    def _update_state(self, state: str) -> None:
        self._state = state
        force = self._info.get("force", False)

        if state == _STATE_PROMPT:
            self._progress_widget.hide()
            self._btn_later.setVisible(not force)
            self._btn_later.setText(t("update.later"))
            self._btn_later.setEnabled(True)
            self._btn_action.setText(t("update.download_install"))
            self._btn_action.setEnabled(True)

        elif state == _STATE_DOWNLOADING:
            self._progress_widget.show()
            self._progress_bar.setValue(0)
            self._status_lbl.setText(t("update.downloading"))
            self._btn_later.setVisible(True)
            self._btn_later.setText(t("update.cancel"))
            self._btn_later.setEnabled(True)
            self._btn_action.setText(t("update.downloading"))
            self._btn_action.setEnabled(False)

        elif state == _STATE_VERIFYING:
            self._status_lbl.setText(t("update.verifying"))
            self._btn_later.setEnabled(False)
            self._btn_action.setEnabled(False)

        elif state == _STATE_READY:
            self._progress_bar.setValue(100)
            self._status_lbl.setText(t("update.ready"))
            self._btn_later.hide()
            self._btn_action.setText(t("update.install_restart"))
            self._btn_action.setEnabled(True)

        elif state == _STATE_ERROR:
            self._btn_later.setVisible(True)
            self._btn_later.setText(t("update.later"))
            self._btn_later.setEnabled(True)
            self._btn_action.setText(t("update.retry"))
            self._btn_action.setEnabled(True)

    # ── Actions ──────────────────────────────────────────────

    def _on_action(self) -> None:
        if self._state == _STATE_PROMPT:
            self._start_download()
        elif self._state == _STATE_READY:
            self._apply_and_restart()
        elif self._state == _STATE_ERROR:
            self._start_download()  # retry

    def _on_later(self) -> None:
        if self._state == _STATE_DOWNLOADING:
            self._cancel_download()
        else:
            self.reject()

    def _start_download(self) -> None:
        from utils.updater import download_update

        self._cancel_flag[0] = False
        self._update_state(_STATE_DOWNLOADING)

        url = self._info["update_url"]
        sha256 = self._info.get("sha256", "")

        self._worker = Worker(
            download_update,
            url,
            expected_sha256=sha256,
            cancel_flag=self._cancel_flag,
            use_progress=True,
        )
        self._worker.signals.progress.connect(self._on_progress)
        self._worker.signals.result.connect(self._on_download_done)
        self._worker.signals.error.connect(self._on_download_error)
        self._worker.start()

    def _cancel_download(self) -> None:
        self._cancel_flag[0] = True
        self._update_state(_STATE_PROMPT)

    def _on_progress(self, value: int) -> None:
        if self._state != _STATE_DOWNLOADING:
            return
        self._progress_bar.setValue(value)

        # Show percentage in status
        self._status_lbl.setText(
            t("update.downloading_pct", pct=value)
        )

    def _on_download_done(self, path: str) -> None:
        self._downloaded_path = path
        sha = self._info.get("sha256", "")
        if sha:
            self._status_lbl.setText(t("update.verified"))
        self._update_state(_STATE_READY)

    def _on_download_error(self, err: str) -> None:
        if "CANCELLED" in err:
            self._update_state(_STATE_PROMPT)
            return

        logger.error("Download failed: %s", err)
        self._status_lbl.setText(t("update.error_download"))
        self._update_state(_STATE_ERROR)

    def _apply_and_restart(self) -> None:
        if not self._downloaded_path:
            return
        from utils.updater import apply_update
        self.accept()
        apply_update(self._downloaded_path)

    # ── Overrides ────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        if self._state == _STATE_DOWNLOADING:
            self._cancel_flag[0] = True
        if self._info.get("force") and self._state != _STATE_READY:
            event.ignore()
            return
        super().closeEvent(event)

    def keyPressEvent(self, event) -> None:
        # Block Escape for force updates
        if event.key() == Qt.Key.Key_Escape and self._info.get("force"):
            return
        super().keyPressEvent(event)
