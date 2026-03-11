from __future__ import annotations

import tkinter as tk
from tkinter import ttk


COLORS = {
    "bg": "#0F141B",
    "panel": "#161D27",
    "panel_alt": "#1C2430",
    "panel_alt_2": "#232D3B",
    "panel_border": "#2B3747",
    "text": "#EDF1F6",
    "muted": "#97A4B5",
    "accent": "#28A1FF",
    "accent_hover": "#4AB0FF",
    "success": "#67C587",
    "warning": "#F0BE52",
    "danger": "#FF657D",
    "info": "#4AB0FF",
    "selection": "#263344",
    "disabled": "#6D7785",
    "demo": "#E7A23C",
    "shadow": "#0C1117",
}


def apply_dark_theme(root: tk.Tk) -> None:
    root.configure(bg=COLORS["bg"])
    style = ttk.Style(root)
    style.theme_use("clam")

    base_font = ("Segoe UI", 10)
    small_font = ("Segoe UI", 9)
    title_font = ("Segoe UI Semibold", 11)
    section_font = ("Segoe UI Semibold", 13)
    large_font = ("Segoe UI Semibold", 18)
    hero_font = ("Segoe UI Semibold", 24)

    style.configure(".", background=COLORS["bg"], foreground=COLORS["text"], font=base_font)
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Card.TFrame", background=COLORS["panel"], relief="flat", borderwidth=1)
    style.configure("CardInner.TFrame", background=COLORS["panel"], relief="flat")
    style.configure("Inset.TFrame", background=COLORS["panel_alt"], relief="flat")
    style.configure("Sidebar.TFrame", background=COLORS["panel_alt"])
    style.configure("SidebarHeader.TFrame", background=COLORS["panel_alt"])
    style.configure("Toolbar.TFrame", background=COLORS["panel"])
    style.configure("Section.TLabelframe", background=COLORS["bg"], bordercolor=COLORS["panel_border"], relief="flat")
    style.configure(
        "Section.TLabelframe.Label",
        background=COLORS["bg"],
        foreground=COLORS["muted"],
        font=title_font,
    )
    style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=base_font)
    style.configure("Card.TLabel", background=COLORS["panel"], foreground=COLORS["text"], font=base_font)
    style.configure("CardMuted.TLabel", background=COLORS["panel"], foreground=COLORS["muted"], font=small_font)
    style.configure("Title.TLabel", font=large_font, foreground=COLORS["text"])
    style.configure("SubTitle.TLabel", font=title_font, foreground=COLORS["muted"])
    style.configure("SectionTitle.TLabel", font=section_font, foreground=COLORS["text"])
    style.configure("CardTitle.TLabel", background=COLORS["panel"], font=section_font, foreground=COLORS["text"])
    style.configure("NavTitle.TLabel", background=COLORS["panel_alt"], font=("Segoe UI Semibold", 18), foreground=COLORS["text"])
    style.configure("NavSubTitle.TLabel", background=COLORS["panel_alt"], font=small_font, foreground=COLORS["muted"])
    style.configure("SidebarLogo.TLabel", background=COLORS["panel_alt"])
    style.configure("Muted.TLabel", foreground=COLORS["muted"], font=small_font)
    style.configure("Hero.TLabel", font=hero_font, foreground=COLORS["text"])
    style.configure("Metric.TLabel", background=COLORS["panel"], foreground=COLORS["text"], font=hero_font)
    style.configure("ValueTitle.TLabel", background=COLORS["panel"], foreground=COLORS["muted"], font=small_font)
    style.configure("ValueBody.TLabel", background=COLORS["panel"], foreground=COLORS["text"], font=("Segoe UI Semibold", 11))

    style.configure(
        "Sidebar.TButton",
        background=COLORS["panel_alt"],
        foreground=COLORS["text"],
        borderwidth=0,
        padding=(14, 10),
        relief="flat",
    )
    style.map(
        "Sidebar.TButton",
        background=[("active", COLORS["selection"]), ("disabled", COLORS["panel_alt"])],
        foreground=[("disabled", COLORS["disabled"])],
    )
    style.configure(
        "SidebarActive.TButton",
        background=COLORS["selection"],
        foreground=COLORS["text"],
        borderwidth=0,
        padding=(14, 10),
        relief="flat",
    )
    style.map("SidebarActive.TButton", background=[("active", COLORS["selection"])])

    style.configure("TButton", background=COLORS["panel_alt"], foreground=COLORS["text"], padding=(10, 8), borderwidth=0)
    style.map(
        "TButton",
        background=[("active", COLORS["selection"]), ("disabled", COLORS["panel_alt"])],
        foreground=[("disabled", COLORS["disabled"])],
    )
    style.configure("Accent.TButton", background=COLORS["accent"], foreground="#FFFFFF", padding=(12, 8), borderwidth=0)
    style.map(
        "Accent.TButton",
        background=[("active", COLORS["accent_hover"]), ("disabled", COLORS["panel_alt_2"])],
        foreground=[("disabled", COLORS["disabled"])],
    )
    style.configure("Danger.TButton", background=COLORS["danger"], foreground="#FFFFFF", padding=(12, 8), borderwidth=0)
    style.map(
        "Danger.TButton",
        background=[("active", "#FF7D91"), ("disabled", COLORS["panel_alt_2"])],
        foreground=[("disabled", COLORS["disabled"])],
    )
    style.configure("Subtle.TButton", background=COLORS["panel_alt"], foreground=COLORS["muted"], padding=(10, 8), borderwidth=0)
    style.map(
        "Subtle.TButton",
        background=[("active", COLORS["selection"]), ("disabled", COLORS["panel_alt"])],
        foreground=[("active", COLORS["text"]), ("disabled", COLORS["disabled"])],
    )

    style.configure(
        "TEntry",
        fieldbackground=COLORS["panel"],
        foreground=COLORS["text"],
        insertcolor=COLORS["text"],
        bordercolor=COLORS["panel_border"],
        lightcolor=COLORS["panel_border"],
        darkcolor=COLORS["panel_border"],
        padding=(8, 6),
    )
    style.map("TEntry", fieldbackground=[("disabled", COLORS["panel_alt"])], foreground=[("disabled", COLORS["disabled"])])

    style.configure(
        "TCombobox",
        fieldbackground=COLORS["panel"],
        foreground=COLORS["text"],
        arrowsize=14,
        arrowcolor=COLORS["muted"],
        bordercolor=COLORS["panel_border"],
        lightcolor=COLORS["panel_border"],
        darkcolor=COLORS["panel_border"],
        padding=(6, 4),
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COLORS["panel"]), ("disabled", COLORS["panel_alt"])],
        foreground=[("readonly", COLORS["text"]), ("disabled", COLORS["disabled"])],
        arrowcolor=[("disabled", COLORS["disabled"])],
    )

    style.configure(
        "Treeview",
        background=COLORS["panel"],
        foreground=COLORS["text"],
        fieldbackground=COLORS["panel"],
        rowheight=31,
        bordercolor=COLORS["panel_border"],
        lightcolor=COLORS["panel_border"],
        darkcolor=COLORS["panel_border"],
    )
    style.configure(
        "Treeview.Heading",
        background=COLORS["panel_alt"],
        foreground=COLORS["muted"],
        relief="flat",
        font=title_font,
        padding=(8, 6),
    )
    style.map(
        "Treeview",
        background=[("selected", COLORS["selection"])],
        foreground=[("selected", COLORS["text"])],
    )

    style.configure("Vertical.TScrollbar", background=COLORS["panel_alt"], troughcolor=COLORS["bg"], bordercolor=COLORS["bg"])
    style.configure("Horizontal.TScrollbar", background=COLORS["panel_alt"], troughcolor=COLORS["bg"], bordercolor=COLORS["bg"])

    style.configure("TNotebook", background=COLORS["bg"], borderwidth=0, tabmargins=(0, 0, 0, 0))
    style.configure(
        "TNotebook.Tab",
        background=COLORS["panel_alt"],
        foreground=COLORS["muted"],
        padding=(16, 8),
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", COLORS["panel"]), ("active", COLORS["selection"])],
        foreground=[("selected", COLORS["text"]), ("active", COLORS["text"])],
    )

    root.option_add("*Text.background", COLORS["panel"])
    root.option_add("*Text.foreground", COLORS["text"])
    root.option_add("*Text.insertBackground", COLORS["text"])
    root.option_add("*Text.highlightBackground", COLORS["panel_border"])
    root.option_add("*Text.highlightColor", COLORS["accent"])
