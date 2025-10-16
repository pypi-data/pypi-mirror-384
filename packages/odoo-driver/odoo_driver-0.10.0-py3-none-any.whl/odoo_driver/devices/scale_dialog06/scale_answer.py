import re

from loguru import logger

from ..tools.serial_code import ACK, ESC, ETX, NAK, STX

error_regex__record_09 = re.compile(rf"{STX}09{ESC}(?P<error>\d+){ETX}")

checksums_request_regex__record_11 = re.compile(
    rf"{STX}11{ESC}(?P<checksums_d0>\d)(?P<checksums_z>\w\w){ETX}"
)
checksums_ok_regex__record_11 = re.compile(rf"{STX}11{ESC}1{ETX}")

weighing_result_regex__record_02 = re.compile(
    rf"{STX}02{ESC}(?P<status>\w){ESC}(?P<weight>\d+)"
    rf"{ESC}(?P<unit_price>\d+){ESC}(?P<total_price>\d+){ETX}"
)

_ERROR_DESCRIPTIONS = {
    "00": "no error",
    "01": "general error",
    "02": "parity error or buffer overflow",
    "10": "invalid record no.",
    "11": "invalid unit price",
    "12": "invalid tare value",
    "13": "invalid text",
    "20": "scale is still in motion (no standstill)",
    "21": "scale wasn't in motion since last operation",
    "22": "measurement is not yet finished",
    "30": "weight is less than minimum weight",
    "31": "scale is less than 0",
    "32": "scale is overloaded",
    "-1": "no response. Please reboot the scale",
    "-2": "unimplemented communication with scale",
}


class ScaleAnswer:
    answer_type = ""
    _byte_message = b""

    def __repr__(self):
        result = f"weight: {self.weight} - error_number: {self.error_number} - error_description: {self.error_description}"
        return result

    @property
    def error_description(self):
        if self.error_number:
            return _ERROR_DESCRIPTIONS.get(self.error_number, "Unknown Error")
        return ""

    def __init__(self, byte_answer):
        self.error_number = False
        self.weight = False

        self._byte_message = byte_answer
        self._message = byte_answer.decode("utf-8")

        if self._message == NAK:
            self.answer_type = "record_NAK"

        elif self._message == ACK:
            self.answer_type = "record_ACK"

        elif checksums_request_regex__record_11.search(self._message):
            self.answer_type = "record_11_checksums_request"
            result = checksums_request_regex__record_11.search(self._message)
            self.checksums_d0 = result.group("checksums_d0")
            self.checksums_z = result.group("checksums_z")

        elif checksums_ok_regex__record_11.search(self._message):
            self.answer_type = "record_11_checksums_valid"

        elif weighing_result_regex__record_02.search(self._message):
            self.answer_type = "record_02_weight"
            result = weighing_result_regex__record_02.search(self._message)
            self.weight = float(result.group("weight")) / 1000
            self.total_price = result.group("total_price")

        elif error_regex__record_09.search(self._message):
            self.error_number = error_regex__record_09.search(self._message).group(
                "error"
            )
            if self.error_number == "00":
                self.answer_type = "record_09_no_error"
            else:
                self.answer_type = "record_09_error"

        elif self._message == "":
            # In some very rare random cases, scale doesn't return nothing
            # In that case, we return an unknown error
            # Next communication will work correctly
            self.error_number = "-1"
            self.answer_type = "unknown_error"
            logger.error("No answer from scale")

        else:
            # This part should never occures
            self.error_number = "-2"
            self.answer_type = "unknown_error"
            logger.critical(f"Unimplemented Feature. Message: {self._byte_message}")
