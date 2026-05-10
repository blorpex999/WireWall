from __future__ import annotations

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from app.ui.widgets.common import ScrollableTree


def test_scrollable_tree_preserves_user_resized_first_column_after_refresh(qapp) -> None:
    host = QWidget()
    layout = QVBoxLayout(host)
    tree = ScrollableTree(host, ("date", "model", "level"), height=4)
    layout.addWidget(tree)
    tree.tree.heading("date", text="Date")
    tree.tree.heading("model", text="Modele")
    tree.tree.heading("level", text="Niveau")
    tree.tree.column("date", width=150, anchor="w")
    tree.tree.column("model", width=140, anchor="w")
    tree.tree.column("level", width=90, anchor="w")

    host.resize(420, 220)
    host.show()
    qapp.processEvents()
    qapp.processEvents()
    try:
        table = tree.tree.widget
        table.setColumnWidth(0, 230)
        qapp.processEvents()

        assert table.columnWidth(0) == 230

        tree.clear()
        tree.tree.insert("", "end", values=("10/05/2026 17:36", "qwen2.5:3b", "CRITICAL"))
        tree.set_empty(True, "Aucune ligne.")
        qapp.processEvents()
        qapp.processEvents()

        assert table.columnWidth(0) == 230
    finally:
        host.close()
