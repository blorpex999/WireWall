from __future__ import annotations

from types import SimpleNamespace

from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from app.models.entities import USBDevice
from app.ui.views.devices import DevicesView
from app.ui.widgets.common import ScrollableDetailText
from app.utils.datetime import utc_now


def test_scrollable_detail_text_keeps_scroll_when_content_is_unchanged(qapp) -> None:
    widget = ScrollableDetailText(height=4)
    widget.resize(420, 180)
    widget.show()
    qapp.processEvents()
    try:
        content = "\n".join(f"Ligne {index}" for index in range(60))
        widget.set_text(content)
        qapp.processEvents()
        widget.text.yview_moveto(1.0)
        qapp.processEvents()
        before = widget.text.yview()

        widget.set_text(content)
        qapp.processEvents()
        after = widget.text.yview()

        assert after == before
    finally:
        widget.close()


def test_devices_view_preserves_selection_on_refresh(qapp) -> None:
    tracked = USBDevice(
        device_key="046D:C539",
        vid=0x046D,
        pid=0xC539,
        vendor_name="Logitech",
        product_name="USB Receiver",
        category="hid",
        status="connected",
        risk_level="MEDIUM",
        risk_score=30,
        first_seen=utc_now(),
        last_seen=utc_now(),
    )
    older = USBDevice(
        device_key="8087:0026",
        vid=0x8087,
        pid=0x0026,
        vendor_name="Intel",
        product_name="Wireless",
        category="communication",
        status="connected",
        risk_level="LOW",
        risk_score=5,
        first_seen=utc_now(),
        last_seen=utc_now(),
    )

    controller = SimpleNamespace(
        demo_mode=False,
        devices=[tracked, older],
        list_devices=lambda **kwargs: controller.devices,
        refresh_monitor=lambda: None,
        get_device_history=lambda device_key, limit=8: [],
    )
    app = SimpleNamespace(set_status=lambda *args, **kwargs: None)

    host = QWidget()
    host_layout = QVBoxLayout(host)
    view = DevicesView(host, controller, app)
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

        assert view.values["name"].value_label.text() == "Logitech USB Receiver"

        newest = USBDevice(
            device_key="04F2:B64F",
            vid=0x04F2,
            pid=0xB64F,
            vendor_name="Generic",
            product_name="Camera",
            category="imaging",
            status="connected",
            risk_level="LOW",
            risk_score=5,
            first_seen=utc_now(),
            last_seen=utc_now(),
        )
        controller.devices = [newest, tracked, older]

        view.refresh_data()

        assert view.values["name"].value_label.text() == "Logitech USB Receiver"
        assert view.values["vidpid"].value_label.text() == "046D:C539"
    finally:
        host.close()


def test_devices_view_search_refreshes_automatically(qapp) -> None:
    devices = [
        USBDevice(
            device_key="046D:C539",
            vid=0x046D,
            pid=0xC539,
            vendor_name="Logitech",
            product_name="USB Receiver",
            category="hid",
            status="connected",
            risk_level="MEDIUM",
            risk_score=30,
            first_seen=utc_now(),
            last_seen=utc_now(),
        ),
        USBDevice(
            device_key="8087:0026",
            vid=0x8087,
            pid=0x0026,
            vendor_name="Intel",
            product_name="Wireless",
            category="communication",
            status="connected",
            risk_level="LOW",
            risk_score=5,
            first_seen=utc_now(),
            last_seen=utc_now(),
        ),
    ]

    def list_devices(*, search="", category="", status=""):
        result = devices
        if search:
            lowered = search.lower()
            result = [device for device in result if lowered in device.display_name.lower() or lowered in device.vid_pid.lower()]
        return result

    controller = SimpleNamespace(
        demo_mode=False,
        list_devices=list_devices,
        refresh_monitor=lambda: None,
        get_device_history=lambda device_key, limit=8: [],
    )
    app = SimpleNamespace(set_status=lambda *args, **kwargs: None)

    host = QWidget()
    host_layout = QVBoxLayout(host)
    view = DevicesView(host, controller, app)
    host_layout.addWidget(view)
    host.resize(1400, 900)
    host.show()
    qapp.processEvents()
    try:
        view.refresh_data()
        assert len(view.table.tree.get_children()) == 2

        view.search_entry.setText("logitech")
        QTest.qWait(350)
        qapp.processEvents()

        rows = view.table.tree.get_children()
        assert len(rows) == 1
        assert view.table.tree.item(rows[0], "values")[1] == "Logitech USB Receiver"
    finally:
        host.close()
