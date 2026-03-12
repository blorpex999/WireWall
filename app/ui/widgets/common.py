from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.ui.theme import COLORS
from app.utils.ui import severity_color


def _pill_fg(level: str) -> str:
    upper = level.upper()
    if upper in {"WARNING", "MEDIUM"}:
        return COLORS["bg"]
    return "#FFFFFF"


class StatusPill(tk.Label):
    def __init__(self, master, text: str = "", level: str = "INFO") -> None:
        super().__init__(
            master,
            text=text,
            bg=severity_color(level),
            fg=_pill_fg(level),
            padx=10,
            pady=3,
            bd=0,
            relief="flat",
            font=("Segoe UI Semibold", 9),
        )
        self.level = level

    def set(self, text: str, level: str = "INFO") -> None:
        self.level = level
        self.configure(text=text, bg=severity_color(level), fg=_pill_fg(level))


class SeverityBadge(StatusPill):
    pass


class SectionHeader(ttk.Frame):
    def __init__(self, master, title: str, subtitle: str = "", tag_text: str = "", tag_level: str = "INFO") -> None:
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.title_var = tk.StringVar(value=title)
        self.subtitle_var = tk.StringVar(value=subtitle)
        ttk.Label(self, textvariable=self.title_var, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self, textvariable=self.subtitle_var, style="SubTitle.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.tag = StatusPill(self, tag_text, tag_level)
        if tag_text:
            self.tag.grid(row=0, column=1, rowspan=2, sticky="e")

    def set_tag(self, text: str, level: str = "INFO") -> None:
        if not self.tag.winfo_ismapped():
            self.tag.grid(row=0, column=1, rowspan=2, sticky="e")
        self.tag.set(text, level)


class KpiCard(ttk.Frame):
    def __init__(self, master, title: str, value: str = "-", subtitle: str = "") -> None:
        super().__init__(master, style="Card.TFrame", padding=0)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.top_bar = tk.Frame(self, bg=severity_color("INFO"), height=4)
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        body = ttk.Frame(self, style="CardInner.TFrame", padding=(16, 14))
        body.grid(row=1, column=0, columnspan=2, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=0)

        ttk.Label(body, text=title, style="CardMuted.TLabel").grid(row=0, column=0, sticky="w")
        self.badge = SeverityBadge(body, "", "INFO")
        self.badge.grid(row=0, column=1, sticky="e")
        self.badge.grid_remove()

        self.value_var = tk.StringVar(value=value)
        ttk.Label(body, textvariable=self.value_var, style="Metric.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 4))
        self.subtitle_var = tk.StringVar(value=subtitle)
        ttk.Label(body, textvariable=self.subtitle_var, style="CardMuted.TLabel").grid(row=2, column=0, columnspan=2, sticky="w")

    def set(self, value: str, subtitle: str = "", tone: str = "INFO", pill_text: str = "") -> None:
        self.value_var.set(value)
        self.subtitle_var.set(subtitle)
        self.top_bar.configure(bg=severity_color(tone))
        if pill_text:
            self.badge.set(pill_text, tone)
            if not self.badge.winfo_ismapped():
                self.badge.grid()
        elif self.badge.winfo_ismapped():
            self.badge.grid_remove()


class LabeledValue(ttk.Frame):
    def __init__(self, master, label: str, value: str = "-") -> None:
        super().__init__(master, style="CardInner.TFrame")
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text=label, style="ValueTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.value_var = tk.StringVar(value=value)
        ttk.Label(self, textvariable=self.value_var, style="ValueBody.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 0))

    def set(self, value: str) -> None:
        self.value_var.set(value)


class EmptyState(ttk.Frame):
    def __init__(self, master, title: str, detail: str) -> None:
        super().__init__(master, padding=20)
        ttk.Label(self, text=title, style="SectionTitle.TLabel").pack(anchor="center")
        ttk.Label(self, text=detail, style="Muted.TLabel", justify="center").pack(anchor="center", pady=(6, 0))


class ScrollablePage(ttk.Frame):
    def __init__(self, master) -> None:
        super().__init__(master)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0, bd=0, relief="flat")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.body = ttk.Frame(self.canvas)
        self.body.columnconfigure(0, weight=1)
        self._body_window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", self._on_body_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

    def _on_body_configure(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        try:
            self.canvas.itemconfigure(self._body_window, width=event.width)
        except Exception:
            return

    def _on_mousewheel(self, event: tk.Event) -> None:
        if not self.winfo_ismapped():
            return
        widget = event.widget
        if widget is None:
            return
        widget_path = str(widget)
        if not widget_path.startswith(str(self)):
            return
        if widget.winfo_class() in {"Text", "Treeview", "Listbox"}:
            return
        first, last = self.canvas.yview()
        if first == 0.0 and last == 1.0:
            return
        direction = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(direction, "units")

    def scroll_to_top(self) -> None:
        self.canvas.yview_moveto(0.0)


class InlineHelpPanel(ttk.Frame):
    def __init__(self, master, button_text: str, sections: list[tuple[str, str]]) -> None:
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self._expanded = False
        self._collapsed_text = button_text

        action_row = ttk.Frame(self)
        action_row.grid(row=0, column=0, sticky="ew")
        action_row.columnconfigure(0, weight=1)
        self.button = ttk.Button(
            action_row,
            text=self._collapsed_text,
            style="Subtle.TButton",
            command=self.toggle,
        )
        self.button.grid(row=0, column=1, sticky="e")

        self.body = ttk.Frame(self, style="Card.TFrame", padding=12)
        self.body.columnconfigure(0, weight=1)
        for index, (label, text) in enumerate(sections):
            row = ttk.Frame(self.body, style="CardInner.TFrame")
            row.grid(row=index, column=0, sticky="ew", pady=(0, 6 if index < len(sections) - 1 else 0))
            row.columnconfigure(1, weight=1)
            ttk.Label(row, text=f"{label} :", style="ValueTitle.TLabel").grid(row=0, column=0, sticky="nw", padx=(0, 8))
            ttk.Label(
                row,
                text=text,
                style="Muted.TLabel",
                wraplength=1120,
                justify="left",
            ).grid(row=0, column=1, sticky="ew")
        self.body.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.body.grid_remove()

    def toggle(self) -> None:
        self._expanded = not self._expanded
        if self._expanded:
            self.body.grid()
            self.button.configure(text="Masquer l'aide")
        else:
            self.body.grid_remove()
            self.button.configure(text=self._collapsed_text)


class StatusBar(ttk.Frame):
    def __init__(self, master) -> None:
        super().__init__(master, style="Card.TFrame", padding=(12, 8))
        self.columnconfigure(1, weight=1)
        self.message_var = tk.StringVar(value="Pret.")
        self.indicator = tk.Canvas(self, width=12, height=12, bg=COLORS["panel"], highlightthickness=0)
        self.indicator.grid(row=0, column=0, sticky="w")
        self.level_pill = StatusPill(self, "INFO", "INFO")
        self.level_pill.grid(row=0, column=2, sticky="e", padx=(12, 8))
        self.mode_pill = StatusPill(self, "MODE REEL", "INFO")
        self.mode_pill.grid(row=0, column=3, sticky="e")
        ttk.Label(self, textvariable=self.message_var).grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.set_status("Pret.", "INFO")

    def set_status(self, message: str, level: str = "INFO") -> None:
        self.message_var.set(message)
        self.indicator.delete("all")
        self.indicator.create_oval(2, 2, 10, 10, fill=severity_color(level), outline="")
        self.level_pill.set(level.upper(), level)

    def set_mode(self, demo_mode: bool) -> None:
        if demo_mode:
            self.mode_pill.set("MODE DEMO", "WARNING")
        else:
            self.mode_pill.set("MODE REEL", "INFO")


class DemoBanner(tk.Frame):
    def __init__(self, master, visible: bool) -> None:
        super().__init__(master, bg="#352513", highlightbackground=COLORS["warning"], highlightthickness=1, padx=14, pady=10)
        tk.Label(
            self,
            text="DEMO MODE",
            bg="#352513",
            fg=COLORS["warning"],
            font=("Segoe UI Semibold", 11),
        ).pack(anchor="w")
        tk.Label(
            self,
            text="Donnees simulees isolees. Les actions reelles de controle USB sont volontairement distinguees.",
            bg="#352513",
            fg=COLORS["text"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(4, 0))
        if not visible:
            self.grid_remove()


class DetailText(tk.Text):
    def __init__(self, master, **kwargs) -> None:
        super().__init__(
            master,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            highlightthickness=1,
            highlightbackground=COLORS["panel_border"],
            relief="flat",
            wrap="word",
            padx=10,
            pady=10,
            font=("Segoe UI", 10),
            spacing1=2,
            spacing2=2,
            spacing3=2,
            **kwargs,
        )

    def set_text(self, content: str) -> None:
        current = self.get("1.0", "end-1c")
        if current == content:
            return
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("1.0", content)
        self.configure(state="disabled")


class ScrollableDetailText(ttk.Frame):
    def __init__(self, master, **kwargs) -> None:
        super().__init__(master)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.text = DetailText(self, **kwargs)
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=scrollbar.set)

    def set_text(self, content: str) -> None:
        self.text.set_text(content)


class ScrollableTree(ttk.Frame):
    def __init__(self, master, columns: tuple[str, ...], height: int = 12) -> None:
        super().__init__(master)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=height)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.empty_var = tk.StringVar(value="")
        self.empty_label = ttk.Label(self, textvariable=self.empty_var, style="Muted.TLabel")
        self.empty_label.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.empty_label.grid_remove()

    def clear(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def set_empty(self, has_rows: bool, message: str) -> None:
        if has_rows:
            self.empty_label.grid_remove()
        else:
            self.empty_var.set(message)
            self.empty_label.grid()
