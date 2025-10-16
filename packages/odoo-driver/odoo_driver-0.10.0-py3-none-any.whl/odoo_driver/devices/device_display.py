from flask_babel import gettext as _
from loguru import logger

from .models.device_abstract_with_queue import DeviceAbstractWithQueue
from .tools.serial_code import FF, US


class DeviceDisplay(DeviceAbstractWithQueue):
    use_serial = True
    device_type = "display"

    @logger.catch
    def configure(self):
        with self._get_serial() as serial:
            # Note: letter looks to be encoded in ISO-8859-1
            # C:43 ; D: 44; T:54 ; U:55 ...

            logger.debug(
                "Display: Set Mode: ESC/POS with the message STX ENQ 05 C 31 ETX ..."
            )
            serial.write(b"\x02\x05\x43\x31\x03")

            logger.debug(
                "Display: Set Character: France with the message STX ENQ 05 T 01 ETX ..."
            )
            serial.write(b"\x02\x05\x54\x01\x03")

            logger.debug(
                "Display: Set Encoding: CP858 with the message STX ENQ 05 U 13 ETX ..."
            )
            serial.write(b"\x02\x05\x55\x13\x03")

    @logger.catch
    def _process_task_serial(self, serial, task):
        lines_ascii = self._convert_task_to_ascii_lines(task)

        self._clear_screen(serial)

        for row, text in enumerate(lines_ascii, 1):
            self._position_cursor(serial, 1, row)
            self._send_message(serial, [text])

    def _convert_task_to_ascii_lines(self, task):
        lines_ascii = []

        action = task.data["action"]

        if action == "display_lines":
            lines_ascii = task.data.get("text_lines", [])
            if type(lines_ascii) is str:
                lines_ascii = lines_ascii.split("\n")

        elif action in [
            "add_line",
            "update_quantity",
            "update_unit_price",
            "update_discount",
        ]:
            # First Line
            left_part = task.data.get("product_name")
            right_part = self._prepare_percent(task.data.get("discount"))
            line_1 = self._prepare_line(left_part, right_part)

            # Second Line Line
            left_part = (
                self._prepare_qty(task.data.get("quantity"))
                + "×"
                + self._prepare_price(task.data.get("unit_price"))
            )
            right_part = self._prepare_price(task.data.get("total"))
            line_2 = self._prepare_line(left_part, right_part)

            lines_ascii = [line_1, line_2]

        elif action == "remove_line":
            lines_ascii = [
                _("Deleting Line ..."),
                self._prepare_line(task.data.get("product_name")),
            ]

        elif action == "payment_balance":
            total = task.data.get("total")
            total_paid = task.data.get("total_paid")
            total_due = task.data.get("total_due")
            total_to_pay = total - total_paid
            line_1 = self._prepare_line(_("Total:"), self._prepare_price(total))
            line_2 = ""
            if total_paid != 0.0:
                if total_to_pay > 0:
                    line_2 = self._prepare_line(
                        _("To Pay:"), self._prepare_price(total_to_pay)
                    )
                elif total_due < 0:
                    line_2 = self._prepare_line(
                        _("Change:"), self._prepare_price(-total_due)
                    )
            lines_ascii = [line_1, line_2]

        else:
            raise NotImplementedError(
                f"{action} is not a valid action for the Display device."
            )

        return lines_ascii

    def _clear_screen(self, serial):
        self._send_message(serial, [FF], "Clear Screen")

    def _position_cursor(self, serial, col=1, row=1):
        self._send_message(
            serial, [US, chr(36), chr(col), chr(row)], f"Move to col {col} / row {row}"
        )

    def _send_message(self, serial, message_list, action_description=""):
        message_list = [x for x in message_list if x]
        if not message_list:
            return
        message = b"".join([x.encode("cp858", errors="ignore") for x in message_list])
        if action_description:
            logger.debug(
                f"Display: {action_description} with the message {message} ..."
            )

        serial.write(message)

    def _display_float(self, float_repr, reduce_txt=True, suffix=""):
        if reduce_txt:
            while float_repr:
                if float_repr[-1:] == "0":
                    float_repr = float_repr[:-1]
                else:
                    break
            if float_repr[-1:] == ".":
                float_repr = float_repr[:-1]
        return float_repr.replace(".", ",") + suffix

    def _prepare_percent(self, percent):
        try:
            percent = float(percent)
        except ValueError:
            return ""
        except TypeError:
            return ""
        if not percent:
            return ""
        return self._display_float("-{:.1f}".format(percent), suffix="%")

    def _prepare_qty(self, quantity):
        try:
            quantity = float(quantity)
        except ValueError:
            quantity = 0.0
        return self._display_float("{:.3f}".format(quantity))

    def _prepare_price(self, price):
        try:
            price = float(price)
        except ValueError:
            price = 0.0
        return self._display_float("{:.2f}".format(price), reduce_txt=False, suffix="€")

    def _prepare_line(self, left_part, right_part=""):
        result = left_part[:20].ljust(20, " ")
        if right_part:
            right_part = right_part[-20:]
            result = result[0 : (20 - 1 - len(right_part))]
            result += " " + right_part

        return result
