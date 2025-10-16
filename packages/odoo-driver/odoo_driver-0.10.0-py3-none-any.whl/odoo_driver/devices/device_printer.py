import base64
from io import BytesIO

from escpos.printer import Usb
from PIL import Image

from .models.device_abstract_with_queue import DeviceAbstractWithQueue


class DevicePrinter(DeviceAbstractWithQueue):
    device_type = "printer"

    def _process_task(self, task):
        printer = Usb(self._usb_device.idVendor, self._usb_device.idProduct, 0)
        (action, value) = task.data

        if action == "print":
            im = Image.open(BytesIO(base64.b64decode(value)))
            printer.image(im)
            printer.cut()

        elif action == "open_cashbox":
            printer.cashdraw(2)

        printer.close()
