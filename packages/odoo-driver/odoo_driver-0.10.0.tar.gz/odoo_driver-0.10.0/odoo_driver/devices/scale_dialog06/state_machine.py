from statemachine import State, StateMachine

from .scale_command import send_ask_status, send_ask_weight, send_checksums, send_info


class Dialog06Machine(StateMachine):
    def __init__(self, device, polynomial, unit_price, tare=0.0, extra_text=""):
        # Device configuration
        self._device = device
        self.polynomial = polynomial

        # Data to send to the scale
        self.unit_price = unit_price
        self.tare = tare
        self.extra_text = extra_text

        # contain the last analyzed answer from the scale
        self.last_scale_answer = False

        return super().__init__()

    # #############################
    # Public Section
    # #############################

    def continue_communication(self):
        event_name = f"event_{self.last_scale_answer.answer_type}"
        self.send(event_name)

    # #############################
    # State Definition
    # #############################

    state_send_info = State(initial=True)

    state_send_checksums = State()

    state_ask_weight = State()

    state_ask_error = State()

    state_weight_recovered = State(final=True)

    state_error = State(final=True)

    state_unknown_error = State(final=True)

    # #############################
    # Event Definition
    # #############################

    event_record_ACK = state_send_info.to(state_ask_weight) | state_send_checksums.to(
        state_send_info
    )

    event_record_NAK = state_send_info.to(state_ask_error) | state_ask_weight.to(
        state_ask_error
    )

    event_record_11_checksums_valid = state_ask_weight.to(state_ask_weight)

    event_record_02_weight = state_ask_weight.to(state_weight_recovered)

    event_record_09_error = state_ask_error.to(state_error)

    event_record_09_no_error = state_ask_error.to(state_send_info)

    event_record_11_checksums_request = state_send_info.to(state_send_checksums)

    event_unknown_error = state_send_info.to(state_unknown_error)

    # #############################
    # State Section
    # #############################

    def on_enter_state_send_info(self):
        self.last_scale_answer = send_info(
            self._device, self.unit_price, self.tare, self.extra_text
        )

    def on_enter_state_send_checksums(self):
        self.last_scale_answer = send_checksums(
            self._device,
            self.polynomial,
            self.last_scale_answer.checksums_d0,
            self.last_scale_answer.checksums_z,
        )

    def on_enter_state_ask_weight(self):
        self.last_scale_answer = send_ask_weight(self._device)

    def on_enter_state_ask_error(self):
        self.last_scale_answer = send_ask_status(self._device)
