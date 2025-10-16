import simplejson
from flask import jsonify, request
from loguru import logger

from ..app import app
from ..interface import interface


@app.route("/hw_proxy/display_configure", methods=["POST", "PUT"])
@logger.catch
def display_configure():
    logger.trace("display_configure()")
    interface.device_display_configure()
    return jsonify(jsonrpc="2.0", result=True)


@app.route("/hw_proxy/display_show", methods=["POST", "PUT"])
@logger.catch
def display_show():
    logger.trace("display_show()")
    data = request.json.get("params", {}).get("data", {})
    interface.log_data(data, "display", "DEBUG")

    if type(data) is str:
        data = simplejson.loads(data)

    interface.device_display_task_show(data)
    return jsonify(jsonrpc="2.0", result=True)
