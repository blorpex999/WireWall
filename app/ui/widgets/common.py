from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.theme import COLORS
from app.utils.ui import severity_color


def _surface_bg(surface: str) -> str:
    return {
        "page": COLORS["bg"],
        "panel": COLORS["panel"],
        "panel_alt": COLORS["panel_alt"],
    }.get(surface, COLORS["panel"])


def _pill_fg(level: str) -> str:
    if level.upper() in {"WARNING", "MEDIUM"}:
        return COLORS["bg"]
    return "#FFFFFF"


def _anchor_alignment(anchor: str) -> Qt.AlignmentFlag:
    if anchor == "center":
        return Qt.AlignmentFlag.AlignCenter
    if anchor == "e":
        return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
    return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter


class StatusPill(QLabel):
    def __init__(self, parent: QWidget | None = None, text: str = "", level: str = "INFO") -> None:
        super().__init__(text, parent)
        self.setObjectName("pill")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.set(level.upper() if text == "" and level else text, level)

    def _update_style(self, level: str) -> None:
        self.setStyleSheet(
            "background:{bg};color:{fg};border-radius:4px;padding:2px 8px;font-size:9pt;font-weight:600;".format(
                bg=severity_color(level),
                fg=_pill_fg(level),
            )
        )

    def set(self, text: str, level: str = "INFO") -> None:
        self.setText(text)
        self._update_style(level)
        self.adjustSize()


class SeverityBadge(StatusPill):
    pass


class SectionHeader(QWidget):
    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        subtitle: str = "",
        tag_text: str = "",
        tag_level: str = "INFO",
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(12)
        layout.addLayout(top_row)

        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("title")
        top_row.addWidget(self.title_label, 1)

        self.tag = StatusPill(self, tag_text, tag_level)
        top_row.addWidget(self.tag, 0, Qt.AlignmentFlag.AlignRight)
        if not tag_text:
            self.tag.hide()

        self.subtitle_label = QLabel(subtitle, self)
        self.subtitle_label.setObjectName("subtitle")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

    def set_tag(self, text: str, level: str = "INFO") -> None:
        self.tag.show()
        self.tag.set(text, level)


class KpiCard(QFrame):
    def __init__(self, parent: QWidget | None = None, title: str = "", value: str = "-", subtitle: str = "") -> None:
        super().__init__(parent)
        self.setObjectName("card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.top_bar = QFrame(self)
        self.top_bar.setFixedHeight(4)
        outer.addWidget(self.top_bar)

        body = QWidget(self)
        body_layout = QGridLayout(body)
        body_layout.setContentsMargins(16, 14, 16, 14)
        body_layout.setHorizontalSpacing(10)
        body_layout.setVerticalSpacing(4)
        body_layout.setColumnStretch(0, 1)
        outer.addWidget(body)

        self.title_label = QLabel(title, body)
        self.title_label.setObjectName("muted")
        body_layout.addWidget(self.title_label, 0, 0)

        self.badge = SeverityBadge(body, "", "INFO")
        self.badge.hide()
        body_layout.addWidget(self.badge, 0, 1, alignment=Qt.AlignmentFlag.AlignRight)

        self.value_label = QLabel(value, body)
        self.value_label.setStyleSheet("font-size:24pt;font-weight:600;")
        body_layout.addWidget(self.value_label, 1, 0, 1, 2)

        self.subtitle_label = QLabel(subtitle, body)
        self.subtitle_label.setObjectName("muted")
        self.subtitle_label.setWordWrap(True)
        body_layout.addWidget(self.subtitle_label, 2, 0, 1, 2)

        self.set(value, subtitle, tone="INFO", pill_text="")

    def set(self, value: str, subtitle: str = "", tone: str = "INFO", pill_text: str = "") -> None:
        self.value_label.setText(value)
        self.subtitle_label.setText(subtitle)
        self.top_bar.setStyleSheet(f"background-color: {severity_color(tone)}; border-radius: 0;")
        if pill_text:
            self.badge.set(pill_text, tone)
            self.badge.show()
        else:
            self.badge.hide()


class LabeledValue(QWidget):
    def __init__(self, parent: QWidget | None, label: str, value: str = "-", surface: str = "panel") -> None:
        super().__init__(parent)
        bg = _surface_bg(surface)
        self.setStyleSheet(f"background-color: {bg};")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setMinimumHeight(56)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)
        self.label = QLabel(label, self)
        self.label.setObjectName("muted")
        layout.addWidget(self.label)
        self.value_label = QLabel(value, self)
        self.value_label.setStyleSheet("font-size:11pt;font-weight:600;")
        self.value_label.setWordWrap(True)
        layout.addWidget(self.value_label)

    def set(self, value: str) -> None:
        self.value_label.setText(value)


class ScrollablePage(QScrollArea):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.body = QWidget()
        self.body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)
        self.setWidget(self.body)

    def force_layout(self) -> None:
        self.body_layout.activate()
        self.body.adjustSize()
        self.body.updateGeometry()
        self.updateGeometry()
        self.viewport().update()

    def scroll_to_top(self) -> None:
        self.verticalScrollBar().setValue(0)


class InlineHelpPanel(QWidget):
    def __init__(self, parent: QWidget | None, button_text: str, sections: list[tuple[str, str]]) -> None:
        super().__init__(parent)
        self._expanded = False
        self._collapsed_text = button_text

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        action_row = QHBoxLayout()
        action_row.addStretch(1)
        layout.addLayout(action_row)

        self.button = QPushButton(self._collapsed_text, self)
        self.button.setObjectName("subtle")
        self.button.clicked.connect(self.toggle)
        action_row.addWidget(self.button)

        self.body = QFrame(self)
        self.body.setObjectName("card")
        body_layout = QVBoxLayout(self.body)
        body_layout.setContentsMargins(12, 12, 12, 12)
        body_layout.setSpacing(6)
        for label, text in sections:
            row = QWidget(self.body)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            label_widget = QLabel(f"{label} :", row)
            label_widget.setObjectName("muted")
            row_layout.addWidget(label_widget, 0, Qt.AlignmentFlag.AlignTop)
            text_widget = QLabel(text, row)
            text_widget.setObjectName("muted")
            text_widget.setWordWrap(True)
            row_layout.addWidget(text_widget, 1)
            body_layout.addWidget(row)
        layout.addWidget(self.body)
        self.body.hide()

    def toggle(self) -> None:
        self._expanded = not self._expanded
        self.body.setVisible(self._expanded)
        self.button.setText("Masquer l'aide" if self._expanded else self._collapsed_text)


class StatusBar(QStatusBar):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizeGripEnabled(False)

        self.indicator = QLabel(self)
        self.indicator.setFixedSize(12, 12)
        self.message_label = QLabel("Pret.", self)
        self.level_pill = StatusPill(self, "INFO", "INFO")
        self.mode_pill = StatusPill(self, "MODE REEL", "INFO")

        self.addWidget(self.indicator)
        self.addWidget(self.message_label, 1)
        self.addPermanentWidget(self.level_pill)
        self.addPermanentWidget(self.mode_pill)
        self.set_status("Pret.", "INFO")

    def set_status(self, message: str, level: str = "INFO") -> None:
        self.message_label.setText(message)
        color = severity_color(level)
        self.indicator.setStyleSheet(f"background-color:{color}; border-radius:6px;")
        self.level_pill.set(level.upper(), level)

    def set_mode(self, demo_mode: bool) -> None:
        if demo_mode:
            self.mode_pill.set("MODE DEMO", "WARNING")
        else:
            self.mode_pill.set("MODE REEL", "INFO")


class DemoBanner(QFrame):
    def __init__(self, parent: QWidget | None = None, visible: bool = True) -> None:
        super().__init__(parent)
        self.setObjectName("demo_banner")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        title = QLabel("DEMO MODE", self)
        title.setStyleSheet(f"color:{COLORS['warning']}; font-size:11pt; font-weight:600;")
        layout.addWidget(title)

        body = QLabel(
            "Donnees simulees isolees. Les actions reelles de controle USB sont volontairement distinguees.",
            self,
        )
        body.setWordWrap(True)
        layout.addWidget(body)
        self.setVisible(visible)


class DetailText(QPlainTextEdit):
    def __init__(self, parent: QWidget | None = None, *, height: int | None = None, **_kwargs) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            "padding: 8px 10px; background-color: {bg}; color: {text}; border: 1px solid {border}; border-radius: 6px;".format(
                bg=COLORS["panel"],
                text=COLORS["text"],
                border=COLORS["panel_border"],
            )
        )
        if height is not None:
            line_height = self.fontMetrics().lineSpacing()
            visible_lines = max(height, 1)
            self.setMinimumHeight(max(116, (line_height * visible_lines) + 32))

    def set_text(self, content: str) -> None:
        if self.toPlainText() == content:
            return
        self.setPlainText(content)

    def get(self, *_args) -> str:
        return self.toPlainText()

    def yview_moveto(self, fraction: float) -> None:
        bar = self.verticalScrollBar()
        if bar.maximum() <= 0:
            return
        bar.setValue(int(bar.maximum() * max(0.0, min(1.0, fraction))))

    def yview(self) -> tuple[float, float]:
        bar = self.verticalScrollBar()
        maximum = bar.maximum()
        if maximum <= 0:
            return 0.0, 1.0
        first = bar.value() / maximum
        visible = bar.pageStep() / max(maximum + bar.pageStep(), 1)
        return first, min(1.0, first + visible)


class ScrollableDetailText(QFrame):
    def __init__(self, parent: QWidget | None = None, **kwargs) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.text = DetailText(self, **kwargs)
        layout.addWidget(self.text)

    def set_text(self, content: str) -> None:
        self.text.set_text(content)


@dataclass(slots=True)
class _TreeRow:
    item_id: str
    values: tuple[object, ...]
    tags: tuple[str, ...]


class _ResponsiveTableWidget(QTableWidget):
    def __init__(self, adapter: "_TreeAdapter", rows: int, columns: int, parent: QWidget | None = None) -> None:
        super().__init__(rows, columns, parent)
        self._adapter = adapter

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._adapter.schedule_width_sync()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._adapter.schedule_width_sync()


class _TreeAdapter:
    def __init__(self, owner: "ScrollableTree", columns: tuple[str, ...], height: int) -> None:
        self._owner = owner
        self._columns = columns
        self._preferred_widths = {column: 120 for column in columns}
        self._alignments = {column: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter for column in columns}
        self._width_sync_scheduled = False
        self._updates_suspended = False

        self._table = _ResponsiveTableWidget(self, 0, len(columns), owner)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setWordWrap(False)
        self._table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(32)
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.horizontalHeader().setMinimumSectionSize(60)
        self._table.setShowGrid(False)
        self._table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._table.setHorizontalHeaderLabels(list(columns))
        self._table.itemSelectionChanged.connect(self._emit_select)
        self._width_sync_timer = QTimer(self._table)
        self._width_sync_timer.setSingleShot(True)
        self._width_sync_timer.timeout.connect(self._apply_column_widths)
        self._row_index_by_id: dict[str, int] = {}
        self._rows: list[_TreeRow] = []
        self._tag_styles: dict[str, dict[str, str]] = {}
        self.configure(height=height)
        self.schedule_width_sync()

    @property
    def widget(self) -> QTableWidget:
        return self._table

    def heading(self, column: str, *, text: str) -> None:
        try:
            index = self._columns.index(column)
        except ValueError:
            return
        item = self._table.horizontalHeaderItem(index)
        if item is None:
            item = QTableWidgetItem(text)
            self._table.setHorizontalHeaderItem(index, item)
        item.setText(text)

    def column(self, column: str, *, width: int, anchor: str = "w") -> None:
        try:
            index = self._columns.index(column)
        except ValueError:
            return
        self._preferred_widths[column] = width
        self._alignments[column] = _anchor_alignment("e" if anchor == "e" else "w")
        self._refresh_row_styles()
        self.schedule_width_sync()

    def tag_configure(self, tag: str, *, foreground: str) -> None:
        self._tag_styles[tag] = {"foreground": foreground}
        self._refresh_row_styles()

    def insert(
        self,
        _parent: str,
        _index: str,
        *,
        values: tuple[object, ...],
        tags: tuple[str, ...] = (),
    ) -> str:
        item_id = f"row:{len(self._rows)}"
        row_index = self._table.rowCount()
        self._table.insertRow(row_index)
        normalized_values = tuple(values)
        row = _TreeRow(item_id=item_id, values=normalized_values, tags=tuple(tags))
        self._rows.append(row)
        self._row_index_by_id[item_id] = row_index

        foreground = self._foreground_for_tags(row.tags)
        for index, value in enumerate(normalized_values):
            item = QTableWidgetItem("" if value is None else str(value))
            item.setTextAlignment(int(self._alignments[self._columns[index]]))
            item.setToolTip("" if value is None else str(value))
            if foreground is not None:
                item.setForeground(QColor(foreground))
            item.setData(Qt.ItemDataRole.UserRole, item_id)
            self._table.setItem(row_index, index, item)
        self.schedule_width_sync()
        return item_id

    def selection(self) -> tuple[str, ...]:
        row = self._table.currentRow()
        if row < 0 or row >= len(self._rows):
            return ()
        return (self._rows[row].item_id,)

    def selection_set(self, item_id: str) -> None:
        row = self._row_index_by_id.get(item_id)
        if row is None:
            return
        self._table.selectRow(row)
        self._table.setCurrentCell(row, 0)

    def focus(self, item_id: str | None = None) -> str | None:
        if item_id is not None:
            self.selection_set(item_id)
            return item_id
        selection = self.selection()
        if not selection:
            return None
        return selection[0]

    def see(self, item_id: str) -> None:
        row = self._row_index_by_id.get(item_id)
        if row is None:
            return
        item = self._table.item(row, 0)
        if item is not None:
            self._table.scrollToItem(item)

    def get_children(self) -> tuple[str, ...]:
        return tuple(row.item_id for row in self._rows)

    def item(self, item_id: str, option: str = "values"):
        row_index = self._row_index_by_id.get(item_id)
        if row_index is None:
            return () if option == "values" else {}
        row = self._rows[row_index]
        if option == "values":
            return tuple("" if value is None else str(value) for value in row.values)
        return {"values": row.values, "tags": row.tags}

    def configure(self, *, height: int) -> None:
        row_height = self._table.verticalHeader().defaultSectionSize()
        header_height = self._table.horizontalHeader().height() or 28
        total_height = header_height + 4 + (max(height, 1) * row_height)
        self._table.setMinimumHeight(total_height)

    def bind(self, event_name: str, callback: Callable[[object | None], None]) -> None:
        if event_name != "<<TreeviewSelect>>":
            return
        self._owner._select_callbacks.append(callback)

    def clear(self) -> None:
        self._updates_suspended = True
        self._table.setUpdatesEnabled(False)
        self._table.clearSelection()
        self._table.setRowCount(0)
        self._row_index_by_id.clear()
        self._rows.clear()
        self.schedule_width_sync()

    def finish_update(self) -> None:
        self._updates_suspended = False
        self._table.setUpdatesEnabled(True)
        self.schedule_width_sync()
        self._table.viewport().update()

    def _emit_select(self) -> None:
        self._owner._emit_select()

    def _foreground_for_tags(self, tags: tuple[str, ...]) -> str | None:
        foreground = None
        for tag in tags:
            style = self._tag_styles.get(tag)
            if style is not None and "foreground" in style:
                foreground = style["foreground"]
        return foreground

    def _refresh_row_styles(self) -> None:
        for row_index, row in enumerate(self._rows):
            foreground = self._foreground_for_tags(row.tags)
            for column_index, column in enumerate(self._columns):
                item = self._table.item(row_index, column_index)
                if item is None:
                    continue
                item.setTextAlignment(int(self._alignments[column]))
                if foreground is not None:
                    item.setForeground(QColor(foreground))

    def schedule_width_sync(self) -> None:
        if self._width_sync_scheduled:
            return
        self._width_sync_scheduled = True
        self._width_sync_timer.start(0)

    def _apply_column_widths(self) -> None:
        self._width_sync_scheduled = False
        if not self._columns:
            return

        available = max(0, self._table.viewport().width() - 4)
        if available <= 0:
            return

        minimums = {column: self._minimum_width(self._preferred_widths[column]) for column in self._columns}
        total_minimum = sum(minimums.values())
        total_preferred = sum(self._preferred_widths.values())
        computed_widths = dict(minimums)

        if available > total_minimum and total_preferred > total_minimum:
            extra_room = available - total_minimum
            expandable = {
                column: max(0, self._preferred_widths[column] - minimums[column])
                for column in self._columns
            }
            total_expandable = sum(expandable.values())
            if total_expandable > 0:
                distributed = 0
                for column in self._columns[:-1]:
                    share = int(extra_room * (expandable[column] / total_expandable))
                    computed_widths[column] += share
                    distributed += share
                computed_widths[self._columns[-1]] += max(0, extra_room - distributed)
            else:
                even_extra = extra_room // len(self._columns)
                for column in self._columns[:-1]:
                    computed_widths[column] += even_extra
                computed_widths[self._columns[-1]] += extra_room - (even_extra * (len(self._columns) - 1))

        for index, column in enumerate(self._columns):
            self._table.setColumnWidth(index, computed_widths[column])

    def _minimum_width(self, preferred: int) -> int:
        if preferred <= 120:
            return max(72, int(preferred * 0.8))
        if preferred <= 220:
            return max(84, int(preferred * 0.68))
        return max(96, min(220, int(preferred * 0.42)))


class ScrollableTree(QFrame):
    def __init__(self, parent: QWidget | None, columns: tuple[str, ...], height: int = 12) -> None:
        super().__init__(parent)
        self._select_callbacks: list[Callable[[object | None], None]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.tree = _TreeAdapter(self, columns, height)
        layout.addWidget(self.tree.widget)

        self.empty_label = QLabel("", self)
        self.empty_label.setObjectName("muted")
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

    def clear(self) -> None:
        self.tree.clear()

    def set_empty(self, has_rows: bool, message: str) -> None:
        if self.tree._updates_suspended:
            self.tree.finish_update()
        self.empty_label.setVisible(not has_rows)
        if not has_rows:
            self.empty_label.setText(message)

    def _emit_select(self) -> None:
        for callback in list(self._select_callbacks):
            callback(None)
