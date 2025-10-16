import random

from loguru import logger

from ..tools.serial_code import ENQ, EOT, ESC, ETX, STX
from .scale_answer import ScaleAnswer


# ##################################################
# Write Orders
# ##################################################
def send_info(device, unit_price, tare, extra_text):
    unit_price_txt = str(int(unit_price * 100)).rjust(6, "0")
    tare_txt = str(int(tare * 1000)).rjust(4, "0")
    extra_text_txt = extra_text.rjust(13, " ")

    message = [EOT, STX]

    if not tare and not extra_text:
        message += ["01", ESC, unit_price_txt, ESC, ETX]
        description = "Send Unit Price"

    elif not tare and extra_text:
        message += ["04", ESC, unit_price_txt, ESC, extra_text_txt, ETX]
        description = "Send Unit Price and Extra Text"

    elif tare and not extra_text:
        message += ["03", ESC, unit_price_txt, ESC, tare_txt, ETX]
        description = "Send Unit Price and Tare"

    else:
        message += ["05", ESC, unit_price_txt, ESC, tare_txt, ESC, extra_text_txt, ETX]
        description = "Send Unit Price, Tare and Extra Text"

    _send_message(device, message, description)

    return get_answer(device)


def send_checksums(device, polynomial, checksums_d0, checksums_z):
    checksums_cs, checksums_kw = _compute_cs_kw(polynomial, checksums_d0, checksums_z)
    _send_message(
        device,
        [EOT, STX, "10", ESC, checksums_cs, checksums_kw, ETX],
        "Send CS and KW computed values",
    )
    return get_answer(device)


def send_ask_weight(device):
    _send_message(device, [EOT, ENQ], "Ask weight")
    return get_answer(device)


def send_ask_status(device):
    _send_message(device, [EOT, STX, "08", ETX], "Ask Scale Status")
    return get_answer(device)


def _send_EOT(device):
    _send_message(device, [EOT], False)


def _send_message(device, message_list, action_description):
    message = b"".join([x.encode("utf-8") for x in message_list])
    if action_description:
        logger.debug(f"Scale: {action_description} with the message {message} ...")
    device.write(message)


# ##################################################
# Read Orders
# ##################################################


def get_answer(device):
    raw_answer = _get_raw_answer(device)
    answer = ScaleAnswer(raw_answer)
    logger.debug(f"Scale: interprated answer received: {answer.answer_type}.")
    return answer


def _get_raw_answer(device):
    char_list = []
    while True:
        char = device.read(1)  # may return `bytes` or `str`
        if not char:
            break
        else:
            char_list.append(bytes(char))
    result = b"".join(char_list)
    logger.debug(f"Scale: Raw answer received: {result}")
    _send_EOT(device)
    return result


# ##################################################
# Checksums Functions
# ##################################################


def _compute_cs_kw(polynomial, checksums_d0, checksums_z):
    cs = _generate_random_hex_code()
    cs_size = len(cs) * 4
    cs_bin = bin(int(cs, 16))[2:].zfill(cs_size)

    # apply first bit of z on checksum
    cs_bin_encoded = _rotate_left(cs_bin, int(checksums_z[0], 16))
    cs_hex_ascii_encoded = "{:04X}".format(int(cs_bin_encoded, 2))

    # generate kw
    kw = _get_kw_value(polynomial, int(cs, 16))
    kw_size = len(kw) * 4
    kw_bin = bin(int(kw, 16))[2:].zfill(kw_size)

    # apply second bit of z on kw
    kw_bin_encoded = _rotate_right(kw_bin, int(checksums_z[1], 16))
    # kw_hex_ascii_encoded = "{:04X}".format(int(kw_bin_encoded, 2), "X")
    kw_hex_ascii_encoded = "{:04X}".format(int(kw_bin_encoded, 2))

    return cs_hex_ascii_encoded, kw_hex_ascii_encoded


def _get_kw_value(udw_generator, uw_checksum):
    ub_shifts = 0
    if not udw_generator:
        return 0
    udw_kw = uw_checksum << 16
    while not (udw_generator & 0x80000000):
        udw_generator <<= 1
    udw_kw ^= udw_generator
    while not (udw_kw & 0x80000000):
        udw_kw <<= 1
        ub_shifts += 1
        if ub_shifts == 16:
            break
    while ub_shifts < 16:
        udw_kw ^= udw_generator
        while not (udw_kw & 0x80000000):
            udw_kw <<= 1
            ub_shifts += 1
            if ub_shifts == 16:
                break
    udw_kw >>= 16
    return format(udw_kw, "04x")


def _generate_random_hex_code():
    return "".join([random.choice("0123456789ABCDEF") for x in range(4)])


def _rotate_left(num, bits):
    """
    The encoding of the CS-values has to be made
    by rotating them to the left for n bits
    """
    debut = num[0:bits]
    fin = num[bits:16]
    return "".join(fin + debut)


def _rotate_right(num, bits):
    """
    The encoding of the KW-values has to be made
    by rotating them to the right for n bits
    """
    debut = num[16 - bits : 16]
    fin = num[0 : 16 - bits]
    return "".join(debut + fin)
