import serial.tools.list_ports
from flask_babel import gettext as _
from loguru import logger
from serial import Serial

from ...usb_device import usb_device_tools


class DeviceAbstract:
    has_queue = False
    use_serial = False
    device_type = False

    def __init__(self, interface, options):
        self._interface = interface
        self._usb_device = False
        self.usb_device_name = False
        self.terminal_file = False
        self._usb_image_name = False
        self._options = options

    def get_option(self, option_name, option_type, required=False):
        option = self._options.get(option_name, False)
        if required and not option:
            raise Exception(
                f"{option_name} is required for the device {self.device_type}."
            )
        return option_type(option)

    @property
    def name(self):
        if self.device_type == "display":
            return _("Display")
        elif self.device_type == "printer":
            return _("Printer")
        elif self.device_type == "payment":
            return _("Payment Terminal")
        elif self.device_type == "scale":
            return _("Scale")
        return "N/C"

    @property
    def usb_vendor_product_code(self):
        return usb_device_tools.get_device_id_vendor_id_product(self._usb_device)

    @property
    def usb_serial_number(self):
        return usb_device_tools.get_device_serial_number(self._usb_device)

    @property
    def usb_manufacturer(self):
        return usb_device_tools.get_device_manufacturer(self._usb_device)

    @property
    def usb_product_name(self):
        return usb_device_tools.get_device_product(self._usb_device)

    @property
    def is_connected(self):
        return bool(self._usb_device)

    @property
    def disconnections(self):
        return self._interface.disconnections.get(self.usb_vendor_product_code, [])

    @property
    def disconnections_qty(self):
        return len(self.disconnections)

    @property
    def usb_image_name(self):
        return self._usb_image_name or f"{self.device_type}.png"

    # ###########################
    # Device Section
    # ###########################
    def set_usb_device(self, usb_device, extra_info):
        self._usb_device = usb_device
        self.usb_device_name = extra_info.get("name", False)
        self._usb_image_name = extra_info.get("image")
        connected_comports = [x for x in serial.tools.list_ports.comports()]
        for port in connected_comports:
            if (port.vid, port.pid) == (
                usb_device.idVendor,
                usb_device.idProduct,
            ):
                self.terminal_file = port.device
                self._logger("DEBUG", f"Terminal File found: {self.terminal_file}.")
                break
        if not self.terminal_file:
            self._logger("DEBUG", "Terminal File not found.")

    def remove_usb_device(self):
        self._usb_device = False
        self.usb_device_name = False
        self._usb_image_name = False
        self.terminal_file = False

    def _get_serial(self):
        if not self.terminal_file:
            raise Exception(
                "Unable to open a Serial connexion,"
                " because terminal_file is not defined."
            )
        return Serial(self.terminal_file, 9600, timeout=0.05)

    # ###########################
    # Loggging Section
    # ###########################
    def _logger(self, level, message):
        if self._usb_device:
            extra_info = f" ({self.usb_device_name} - {self.usb_vendor_product_code})"
        else:
            extra_info = ""
        logger.log(level, f"Device '{self.device_type}'{extra_info}: {message}")
