from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from app.models.entities import USBDevice
from app.ui.views.devices import DevicesView
from app.ui.widgets.common import ScrollableDetailText
from app.utils.datetime import utc_now


def test_scrollable_detail_text_keeps_scroll_when_content_is_unchanged() -> None:
    tkinter = pytest.importorskip("tkinter")

    try:
        root = tkinter.Tk()
    except tkinter.TclError as exc:
        pytest.skip(f"Tkinter indisponible pour ce test: {exc}")

    root.withdraw()
    try:
        widget = ScrollableDetailText(root, height=4)
        widget.pack(fill="both", expand=True)

        content = "\n".join(f"Ligne {index}" for index in range(60))
        widget.set_text(content)
        root.update_idletasks()
        widget.text.yview_moveto(1.0)
        before = widget.text.yview()

        widget.set_text(content)
        after = widget.text.yview()

        assert after == before
    finally:
        root.destroy()


def test_devices_view_preserves_selection_on_refresh() -> None:
    tkinter = pytest.importorskip("tkinter")

    try:
        root = tkinter.Tk()
    except tkinter.TclError as exc:
        pytest.skip(f"Tkinter indisponible pour ce test: {exc}")

    root.withdraw()
    try:
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
        )
        app = SimpleNamespace(set_status=lambda *args, **kwargs: None)

        view = DevicesView(root, controller, app)
        view.refresh_data()

        first_item = view.table.tree.get_children()[0]
        view.table.tree.selection_set(first_item)
        view.table.tree.focus(first_item)
        view._show_selected()

        assert view.values["name"].value_var.get() == "Logitech USB Receiver"

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

        assert view.values["name"].value_var.get() == "Logitech USB Receiver"
        assert view.values["vidpid"].value_var.get() == "046D:C539"
    finally:
        root.destroy()


def test_devices_view_search_refreshes_automatically() -> None:
    tkinter = pytest.importorskip("tkinter")

    try:
        root = tkinter.Tk()
    except tkinter.TclError as exc:
        pytest.skip(f"Tkinter indisponible pour ce test: {exc}")

    root.withdraw()
    try:
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
        )
        app = SimpleNamespace(set_status=lambda *args, **kwargs: None)

        view = DevicesView(root, controller, app)
        view.refresh_data()
        assert len(view.table.tree.get_children()) == 2

        view.search_var.set("logitech")
        time.sleep(0.35)
        root.update()

        rows = view.table.tree.get_children()
        assert len(rows) == 1
        assert view.table.tree.item(rows[0], "values")[1] == "Logitech USB Receiver"
    finally:
        root.destroy()
