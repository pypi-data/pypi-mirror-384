from telium import Telium, TeliumAsk

from .models.device_abstract import DeviceAbstract


class DevicePayment(DeviceAbstract):
    device_type = "payment"

    def push_amount(self, amount, currency_iso):
        if not self.terminal_file:
            return False
        telium = Telium(self.terminal_file)
        payment = TeliumAsk.new_payment(
            amount,
            payment_mode="debit",
            target_currency=currency_iso,
        )
        result = telium.ask(payment)
        telium.close()
        return result
