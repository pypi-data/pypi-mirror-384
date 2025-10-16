from flask import jsonify, make_response
from loguru import logger

from ..app import app
from ..interface import interface


@app.route("/hw_proxy/hello")
@logger.catch
def hello():
    """
    hw_proxy/hello is called when the Point of Sale is launched,
    and when user clicks on the device icon.

    If the call to hello fails, Iot Box is considered offline
    and no other calls will be done."""
    logger.trace("hello()")
    return make_response("ping")


@app.route("/hw_proxy/handshake", methods=["POST"])
@logger.catch
def handshake():
    """hw_proxy/handshake is done just after 'hello' call,
    if the hello call succeeded.

    If the call to handshake fails, an error is raised
    in the Point of sale, and no other calls will be done.
    """
    logger.trace("handshake()")
    return jsonify(jsonrpc="2.0", result=True)


@app.route("/hw_proxy/status_json", methods=["POST", "PUT"])
@logger.catch
def status_json():
    """
    hw_proxy/status_json is called every 5 seconds by Odoo,
    if hello / handshake was correctly answered.

    it returns a dictionary with the following structure.
        {
            'DEVICE_TYPE_1': {'status': 'STATUS_1'},
            'DEVICE_TYPE_X': {'status': 'STATUS_X'},
        }

    If the call to status_json fails, an error is raised
    every each 5 seconds, that is quite annoying for the end user.
    """
    logger.trace("status_json()")
    status = {}

    for device_type in interface.device_types:
        device = interface.get_device(device_type)
        if device.is_connected:
            status[device_type] = {
                "status": "connected",
                "vendor_product_code": device.usb_vendor_product_code,
                "serial_number": device.usb_serial_number,
                "manufacturer": device.usb_manufacturer,
                "product_name": device.usb_product_name,
                "device_name": device.usb_device_name,
            }
        else:
            status[device_type] = {"status": "disconnected"}

    return jsonify(jsonrpc="2.0", result=status)
