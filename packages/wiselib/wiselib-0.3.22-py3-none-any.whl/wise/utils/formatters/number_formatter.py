from typing import TypedDict
import re


def add_comma(number=None):
    if number is None:
        return 0
    return f"{number:,}"


def resolve_power(number):
    str_number = str(number)
    match = re.search(r"(e|E).+$", str_number)
    e_position = match.start() if match else -1
    if e_position == -1:
        return str_number
    positive_float_length = len(str_number[: e_position - 1].replace(".", ""))
    e_power = 0 if e_position == -1 else int(str_number[e_position + 1 :])
    if e_power < 0:
        return f"{number:.{abs(e_power) + positive_float_length}f}"
    return f"{number:,}".replace(",", "")


def compress_by_label(number):
    label = ""
    value = ""
    positive_number = abs(number)
    if positive_number > 1e3 - 1:
        sectors = [
            {"label": "K", "max": 1e6, "divide": 1e3},
            {"label": "M", "max": 1e9, "divide": 1e6},
            {"label": "B", "max": 1e12, "divide": 1e9},
            {"label": "T", "max": 1e15, "divide": 1e12},
            {"label": "Qa", "max": 1e18, "divide": 1e15},
            {"label": "Qi", "max": 1e21, "divide": 1e18},
            {"label": "Sx", "max": 1e24, "divide": 1e21},
            {"label": "Sp", "max": 1e27, "divide": 1e24},
            {"label": "Oc", "max": float("inf"), "divide": 1e27},
        ]
        for sector in sectors:
            if positive_number < sector["max"]:
                int_part, dec_part = resolve_power(number / sector["divide"]).split(".")
                label = sector["label"]
                value = f"{int_part}{'.' + dec_part if dec_part else ''}"
                break
    return {"value": value or resolve_power(number), "label": label}


def cut_end_of_number(decimal_str, length):
    value = decimal_str
    if not length or not decimal_str:
        return value
    if length < float("inf"):
        num_strs = list(decimal_str)
        first_non_zero_index = next(
            (i for i, num_str in enumerate(num_strs) if num_str != "0"), len(num_strs)
        )
        value = decimal_str[: first_non_zero_index + length]
    return re.sub(r"0*$", "", value)


def minify_number_repeats(numb_str):
    zero_length = 0
    output = ""
    for char in numb_str:
        if char == "0":
            zero_length += 1
        else:
            if zero_length > 0:
                if zero_length <= 2:
                    output += "0" * zero_length
                else:
                    output += f"0₍{str(zero_length).translate(str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉'))}₎"
                zero_length = 0
            output += char
    return output


class FormatNumberOptions(TypedDict):
    compact_integer: bool | None  # If true: 1520000 => 1.52M
    separate_by_comma: bool | None  # If true: 1234 => 1,234
    decimal_length: int | None  # If 2: 2.001234 => 2.0012, 2.120 => 2.12, 2.100 => 2.1
    minify_decimal_repeats: bool | None  # If true: 1.1000002 => 1.10₍₅₎2


def format_number(
    input,
    options: FormatNumberOptions = {
        "compact_integer": True,
        "separate_by_comma": True,
        "decimal_length": 3,
        "minify_decimal_repeats": True,
    },
):
    output = {"integerPart": "", "decimalPart": "", "label": ""}

    if options.get("compact_integer"):
        label_value = compress_by_label(input)
        label, value = label_value["label"], label_value["value"]
        integer_part, decimal_part = value.split(".")
        output = {
            "label": label,
            "integerPart": integer_part,
            "decimalPart": decimal_part,
        }
    else:
        integer_part, decimal_part = resolve_power(input).split(".")
        output = {
            "label": "",
            "integerPart": integer_part,
            "decimalPart": decimal_part,
        }

    if options.get("separate_by_comma"):
        output["integerPart"] = re.sub(
            r"\B(?=(\d{3})+(?!\d))", ",", output["integerPart"]
        )

    output["decimalPart"] = cut_end_of_number(
        output["decimalPart"], options.get("decimal_length")
    )

    if options.get("minify_decimal_repeats"):
        output["decimalPart"] = minify_number_repeats(output["decimalPart"])

    return "".join(
        filter(
            None,
            [
                f"{output['integerPart']}.{output['decimalPart']}"
                if output["decimalPart"]
                else output["integerPart"],
                output["label"],
            ],
        )
    )
