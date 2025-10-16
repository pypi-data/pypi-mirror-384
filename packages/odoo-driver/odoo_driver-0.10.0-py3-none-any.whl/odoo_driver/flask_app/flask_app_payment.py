import simplejson
from flask import jsonify, request
from loguru import logger

from ..app import app
from ..interface import interface


@app.route("/hw_proxy/payment_terminal_transaction_start", methods=["POST", "PUT"])
@logger.catch
def payment_terminal_transaction_start():
    logger.trace("payment_terminal_transaction_start()")
    data = request.json.get("params", {}).get("payment_info", {})
    interface.log_data(data, "payment", "DEBUG")

    if type(data) is str:
        data = simplejson.loads(data)

    amount = float(data.get("amount"))
    currency_iso = data.get("currency_iso")

    result = interface.device_payment_push_amount(amount, currency_iso)
    return jsonify(jsonrpc="2.0", result=result)
