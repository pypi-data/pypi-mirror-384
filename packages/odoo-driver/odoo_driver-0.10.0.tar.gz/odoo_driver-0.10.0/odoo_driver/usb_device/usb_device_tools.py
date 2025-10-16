from . import usb_device_list


def get_device_id_vendor_id_product(device):
    if device:
        return (
            "{0:04x}".format(device.idVendor) + ":" + "{0:04x}".format(device.idProduct)
        )
    else:
        return "N/C"


def get_device_manufacturer(device):
    try:
        return device.manufacturer
    except ValueError:
        return ""


def get_device_serial_number(device):
    try:
        return device.serial_number and device.serial_number or ""
    except ValueError:
        return ""


def get_device_product(device):
    try:
        return device.product
    except ValueError:
        return ""


def get_device_type(device):
    try:
        (device_type, _extra_info) = usb_device_list.get_device_type(
            device.idVendor, device.idProduct
        )
        return device_type
    except ValueError:
        return False
