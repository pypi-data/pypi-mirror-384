from flask import jsonify, request
from loguru import logger

from ..app import app
from ..interface import interface


@app.route("/hw_proxy/scale_read", methods=["POST", "PUT"])
@logger.catch
def scale_read():
    logger.trace("scale_read()")
    data = request.json.get("params", {}).get("data", {})
    interface.log_data(data, "scale", "DEBUG")

    try:
        unit_price = float(data.get("unit_price", 0.0))
    except ValueError:
        unit_price = 0.0
    try:
        tare = float(data.get("tare", 0.0))
    except ValueError:
        tare = 0.0

    result = interface.device_scale_read_weight(unit_price, tare)

    return jsonify(jsonrpc="2.0", result=result)
