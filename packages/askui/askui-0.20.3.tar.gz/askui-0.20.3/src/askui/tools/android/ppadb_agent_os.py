import io
import re
import shlex
import string
from typing import List, Optional, get_args

from PIL import Image
from ppadb.client import Client as AdbClient  # type: ignore[import-untyped]
from ppadb.device import Device as AndroidDevice  # type: ignore[import-untyped]

from askui.tools.android.agent_os import ANDROID_KEY, AndroidAgentOs, AndroidDisplay


class PpadbAgentOs(AndroidAgentOs):
    """
    This class is used to control the Android device.
    """

    def __init__(self) -> None:
        self._client: Optional[AdbClient] = None
        self._device: Optional[AndroidDevice] = None
        self._mouse_position: tuple[int, int] = (0, 0)
        self._displays: list[AndroidDisplay] = []
        self._selected_display: Optional[AndroidDisplay] = None

    def connect_adb_client(self) -> None:
        if self._client is not None:
            msg = "Adb client is already connected"
            raise RuntimeError(msg)
        try:
            self._client = AdbClient()
        except Exception as e:  # noqa: BLE001
            msg = f""" Failed to connect the adb client to the server.
            Make sure the adb server is running.
            IF you are using a real device, make sure the device is connected.
            And listed after executiing the 'adb devices' command.
            If you are using an emulator, make sure the emulator is running.
            The error message: {e}
            """
            raise RuntimeError(msg)  # noqa: B904

    def connect(self) -> None:
        self.connect_adb_client()
        self.set_device_by_index(0)
        assert self._device is not None
        self._device.wait_boot_complete()

    def disconnect(self) -> None:
        self._client = None
        self._device = None

    def _set_display(self, display: AndroidDisplay) -> None:
        self._selected_display = display
        self._mouse_position = (0, 0)

    def get_connected_displays(self) -> list[AndroidDisplay]:
        self._check_if_device_is_selected()
        assert self._device is not None
        displays: list[AndroidDisplay] = []
        output: str = self._device.shell(
            "dumpsys SurfaceFlinger --display-id",
        )

        index = 0
        for line in output.splitlines():
            if line.startswith("Display"):
                match = re.match(
                    r"Display (\d+) .* displayName=\"([^\"]*?)\"",
                    line,
                )
                if match:
                    unique_display_id: int = int(match.group(1))
                    display_name: str = match.group(2)
                    displays.append(
                        AndroidDisplay(unique_display_id, display_name, index)
                    )
                    index += 1
        if not displays:
            return [AndroidDisplay(0, "Default", 0)]
        return displays

    def set_display_by_index(self, display_index: int = 0) -> None:
        self._displays = self.get_connected_displays()
        if not self._displays:
            self._displays = [AndroidDisplay(0, "Default", 0)]
        if display_index >= len(self._displays):
            msg = (
                f"Display index {display_index} out of range it must be less than "
                f"{len(self._displays)}."
            )
            raise RuntimeError(msg)
        self._set_display(self._displays[display_index])

    def set_display_by_id(self, display_id: int) -> None:
        self._displays = self.get_connected_displays()
        if not self._displays:
            msg = "No displays connected"
            raise RuntimeError(msg)
        for display in self._displays:
            if display.unique_display_id == display_id:
                self._set_display(display)
                return
        msg = f"Display ID {display_id} not found"
        raise RuntimeError(msg)

    def set_display_by_name(self, display_name: str) -> None:
        self._displays = self.get_connected_displays()
        if not self._displays:
            msg = "No displays connected"
            raise RuntimeError(msg)
        for display in self._displays:
            if display.display_name == display_name:
                self._set_display(display)
                return
        msg = f"Display name {display_name} not found"
        raise RuntimeError(msg)

    def set_device_by_index(self, device_index: int = 0) -> None:
        devices = self._get_connected_devices()
        if device_index >= len(devices):
            msg = (
                f"Device index {device_index} out of range it must be less than "
                f"{len(devices)}."
            )
            raise RuntimeError(msg)
        self._device = devices[device_index]
        self.set_display_by_index(0)

    def set_device_by_serial_number(self, device_sn: str) -> None:
        devices = self._get_connected_devices()
        for device in devices:
            if device.serial == device_sn:
                self._device = device
                self.set_display_by_index(0)
                return
        msg = f"Device name {device_sn} not found"
        raise RuntimeError(msg)

    def screenshot(self) -> Image.Image:
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        connection_to_device = self._device.create_connection()
        selected_device_id = self._selected_display.unique_display_id
        connection_to_device.send(
            f"shell:/system/bin/screencap -p -d {selected_device_id}"
        )
        response = connection_to_device.read_all()
        if response and len(response) > 5 and response[5] == 0x0D:
            response = response.replace(b"\r\n", b"\n")
        return Image.open(io.BytesIO(response))

    def shell(self, command: str) -> str:
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        response: str = self._device.shell(command)
        return response

    def tap(self, x: int, y: int) -> None:
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        display_index: int = self._selected_display.display_index
        self._device.shell(f"input -d {display_index} tap {x} {y}")
        self._mouse_position = (x, y)

    def swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_in_ms: int = 1000,
    ) -> None:
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        display_index: int = self._selected_display.display_index
        self._device.shell(
            f"input -d {display_index} swipe {x1} {y1} {x2} {y2} {duration_in_ms}"
        )
        self._mouse_position = (x2, y2)

    def drag_and_drop(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_in_ms: int = 1000,
    ) -> None:
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        display_index: int = self._selected_display.display_index
        self._device.shell(
            f"input -d {display_index} draganddrop {x1} {y1} {x2} {y2} {duration_in_ms}"
        )
        self._mouse_position = (x2, y2)

    def type(self, text: str) -> None:
        if any(c not in string.printable or ord(c) < 32 or ord(c) > 126 for c in text):
            error_msg_nonprintable: str = (
                f"Text contains non-printable characters: {text} "
                + "or special characters which are not supported by the device"
            )
            raise RuntimeError(error_msg_nonprintable)
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        display_index: int = self._selected_display.display_index
        escaped_text = shlex.quote(text)
        shell_safe_text = escaped_text.replace(" ", "%s")
        self._device.shell(f"input -d {display_index} text {shell_safe_text}")

    def key_tap(self, key: ANDROID_KEY) -> None:
        if key not in get_args(ANDROID_KEY):
            error_msg_invalid_key: str = f"Invalid key: {key}"
            raise RuntimeError(error_msg_invalid_key)
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        display_index: int = self._selected_display.display_index
        self._device.shell(f"input -d {display_index} keyevent {key}")

    def key_combination(
        self, keys: List[ANDROID_KEY], duration_in_ms: int = 100
    ) -> None:
        if any(key not in get_args(ANDROID_KEY) for key in keys):
            error_msg_invalid_keys: str = f"Invalid key: {keys}"
            raise RuntimeError(error_msg_invalid_keys)

        if len(keys) < 2:
            error_msg_too_few: str = "Key combination must contain at least 2 keys"
            raise RuntimeError(error_msg_too_few)

        keys_string = " ".join(keys)
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        display_index: int = self._selected_display.display_index
        self._device.shell(
            f"input -d {display_index} keycombination -t {duration_in_ms} {keys_string}"
        )

    def _check_if_device_is_selected(self) -> None:
        devices: list[AndroidDevice] = self._get_connected_devices()

        if not self._device:
            msg = "No device is selected, did you call on of the set_device methods?"
            raise RuntimeError(msg)

        for device in devices:
            if device.serial == self._device.serial:
                return
        msg = f"Device {self._device.serial} not found in connected devices"
        raise RuntimeError(msg)

    def _check_if_display_is_selected(self) -> None:
        if self._selected_display is None:
            msg = "No display is selected, did you call on of  the set_display methods?"
            raise RuntimeError(msg)

    def _get_connected_devices(self) -> list[AndroidDevice]:
        """
        Get the connected devices.
        """
        if not self._client:
            msg = "No adb client is connected, did you call the connect method?"
            raise RuntimeError(msg)
        devices: list[AndroidDevice] = self._client.devices()
        if not devices:
            msg = """No devices are connected,
            If you are using an emulator, make sure the emulator is running.
            If you are using a real device, make sure the device is connected.
            """
            raise RuntimeError(msg)
        return devices

    def get_connected_devices_serial_numbers(self) -> list[str]:
        """
        Get the connected devices serial numbers.
        """
        devices: list[AndroidDevice] = self._get_connected_devices()
        return [device.serial for device in devices]

    def get_selected_device_infos(self) -> tuple[str, AndroidDisplay]:
        """
        Get the selected device infos.
        """
        self._check_if_device_is_selected()
        self._check_if_display_is_selected()
        assert self._device is not None
        assert self._selected_display is not None
        return (self._device.serial, self._selected_display)
