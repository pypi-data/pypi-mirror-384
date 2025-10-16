from .models.device_abstract import DeviceAbstract
from .scale_dialog06 import state_machine


class DeviceScale(DeviceAbstract):
    device_type = "scale"

    def __init__(self, interface, options):
        DeviceAbstract.__init__(self, interface, options)
        self.last_weight = 0.0

    def read_weight(self, unit_price, tare):
        with self._get_serial() as serial:
            sm = state_machine.Dialog06Machine(
                serial,
                self.get_option("polynomial", int, required=True),
                unit_price,
                tare,
            )

            while not sm.current_state.final:
                sm.continue_communication()

        # In a dialog06 context, if the scale return 21 (no change since the last weight)
        # The scale doesn't provide the weight.
        # in that 'valid use case', we return the last weight
        if sm.last_scale_answer.error_number != "21":
            self.last_weight = sm.last_scale_answer.weight

        return {
            "weight": self.last_weight,
            "error_number": sm.last_scale_answer.error_number,
            "error_description": sm.last_scale_answer.error_description,
        }
