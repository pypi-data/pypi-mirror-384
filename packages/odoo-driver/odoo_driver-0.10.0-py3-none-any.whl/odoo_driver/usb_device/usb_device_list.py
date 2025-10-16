_DISPLAY_DEVICES = {
    (0x0416, 0xF011): {
        "name": "Oxhoo - AF240",
        "image": "display__oxhoo__af240.png",
    },
    (0x0416, 0xF012): {
        "name": "Aures - OCD 300",
        "image": "display__aures__ocd_300.png",
    },
}

_PRINTER_DEVICES = {
    (0x04B8, 0x0E15): {
        "name": "Epson - TM-T20II",
        "image": "printer__epson__tm_t20.png",
    },
    (0x04B8, 0x0E28): {
        "name": "Epson - TM-T20III",
        "image": "printer__epson__tm_t20.png",
    },
    (0x04B8, 0x0202): {
        "name": "Epson - TM-T88V",
        "image": "printer__epson__tm_t88.png",
    },
}

_PAYMENT_DEVICES = {
    (0x079B, 0x0028): {
        "name": "Ingenico - Move/5000",
        "image": "payment__ingenico__move_5000.png",
    },
    (0x0B00, 0x0080): {
        "name": "Ingenico - Desk/5000",
        "image": "payment__ingenico__desk_5000.png",
    },
}

_SCALE_DEVICES = {
    (0x0EB8, 0x2200): {
        "name": "Mettler Toledo - Ariva S",
        "image": "scale__mettler_toledo__ariva_s.png",
    },
}


def get_device_type(vendor_code, product_code):
    """return the type of the device, depending on the
    vendor and product code;
    vendor_code: hexadecimal, example: 0x0416
    product_code: hexadecimal, example: 0xF012
    Return: value in ['display', 'printer', 'payment', 'scale', False]
    and extra data
    """
    vendor_product_code = (vendor_code, product_code)

    if vendor_product_code in _DISPLAY_DEVICES.keys():
        device_type = "display"
        extra_info = _DISPLAY_DEVICES.get(vendor_product_code)

    elif vendor_product_code in _PRINTER_DEVICES.keys():
        device_type = "printer"
        extra_info = _PRINTER_DEVICES.get(vendor_product_code)

    elif vendor_product_code in _PAYMENT_DEVICES.keys():
        device_type = "payment"
        extra_info = _PAYMENT_DEVICES.get(vendor_product_code)

    elif vendor_product_code in _SCALE_DEVICES.keys():
        device_type = "scale"
        extra_info = _SCALE_DEVICES.get(vendor_product_code)

    else:
        device_type = extra_info = False

    return (device_type, extra_info)
