from __future__ import annotations

from types import SimpleNamespace

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from app.config.defaults import build_default_settings
from app.models.entities import AIAnalysis, HealthStatus
from app.ui.views.ai_analysis import AIAnalysisView
from app.utils.datetime import utc_now


def test_ai_analysis_view_preserves_selection_on_refresh(qapp) -> None:
    settings = build_default_settings()
    settings.ollama_model = "qwen2.5:14b"

    selected = AIAnalysis(
        id=1,
        created_at="2026-03-11T12:16:51+00:00",
        model="qwen2.5:14b",
        global_level="HIGH",
        summary="Resume selectionne",
        threats=["Menace A"],
        recommendations=["Action A"],
        success=True,
    )
    older = AIAnalysis(
        id=2,
        created_at="2026-03-11T11:53:28+00:00",
        model="qwen2.5:7b",
        global_level="UNKNOWN",
        summary="Ancienne analyse",
        success=False,
    )

    controller = SimpleNamespace(
        settings=settings,
        analyses=[selected, older],
        list_ai_analyses=lambda: controller.analyses,
        get_ollama_health_status=lambda: HealthStatus("ollama", "ok", "ready", utc_now()),
        is_task_running=lambda name: False,
        request_ai_analysis=lambda: True,
    )
    app = SimpleNamespace(set_status=lambda *args, **kwargs: None)

    host = QWidget()
    host_layout = QVBoxLayout(host)
    view = AIAnalysisView(host, controller, app)
    host_layout.addWidget(view)
    host.resize(1400, 900)
    host.show()
    qapp.processEvents()
    try:
        view.refresh_data()

        first_item = view.table.tree.get_children()[0]
        view.table.tree.selection_set(first_item)
        view.table.tree.focus(first_item)
        view._show_selected()

        assert view.values["model"].value_label.text() == "qwen2.5:14b"
        assert "Resume selectionne" in view.summary_text.text.get("1.0", "end-1c")

        newest = AIAnalysis(
            id=3,
            created_at="2026-03-11T12:20:00+00:00",
            model="qwen2.5:14b",
            global_level="MEDIUM",
            summary="Nouvelle analyse",
            success=True,
        )
        controller.analyses = [newest, selected, older]

        view.refresh_data()

        assert view.values["model"].value_label.text() == "qwen2.5:14b"
        assert view.values["level"].value_label.text() == "HIGH"
        assert "Resume selectionne" in view.summary_text.text.get("1.0", "end-1c")
    finally:
        host.close()
