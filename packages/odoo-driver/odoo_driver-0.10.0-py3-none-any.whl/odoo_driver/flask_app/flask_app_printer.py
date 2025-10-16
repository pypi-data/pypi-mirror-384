from flask import jsonify, request
from loguru import logger

from ..app import app
from ..interface import interface


@app.route("/hw_proxy/default_printer_action", methods=["POST", "PUT"])
@logger.catch
def default_printer_action():
    logger.trace("default_printer_action()")
    data = request.json.get("params", {}).get("data", {})

    data_copy = data.copy()
    if data_copy.get("action") == "print_receipt":
        data_copy.pop("receipt")
    interface.log_data(data_copy, "printer", "DEBUG")

    if data.get("action") == "print_receipt":
        receipt = data["receipt"]
        interface.log_image(receipt, "DEBUG")
        interface.device_printer_task_print(receipt)

    elif data.get("action") == "cashbox":
        interface.device_printer_task_open_cashbox()

    else:
        raise Exception(f"Incorrect action value: '{data.get('action')}'")

    return jsonify(jsonrpc="2.0", result=True)
