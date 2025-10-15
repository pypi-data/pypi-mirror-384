"""
JAN Code Generator

This module provides functions to generate random JAN (Japanese Article Number) codes,
including GTIN-13, GTIN-8, GTIN-14, UPC-12, and SSCC-18 formats.
All generated codes include valid check digits calculated using the standard algorithm.
"""

import random

GTIN13_PREFIX_LENGTH = 12
GTIN8_PREFIX_LENGTH = 7
GTIN14_PREFIX_LENGTH = 13
UPC12_PREFIX_LENGTH = 11
SSCC18_PREFIX_LENGTH = 17
GRAI14_PREFIX_LENGTH = 13


def _get_last_jan_digit(jan_code: str) -> int:
    """
    Calculate the check digit for a JAN code using the standard algorithm.

    Args:
        jan_code (str): The JAN code digits without the check digit.

    Returns:
        int: The calculated check digit (0-9).
    """
    i = len(jan_code) + 1
    sum = 0
    for digit in jan_code:
        if i % 2 == 0:
            sum += int(digit) * 3
        else:
            sum += int(digit)
        i -= 1
    last_digit = 10 - int(str(sum)[-1])
    if last_digit == 10:
        last_digit = 0
    return last_digit


def random_gtin_13(prefix: str = "") -> str:
    """
    Generate a random GTIN-13 (Global Trade Item Number) code.

    Args:
        prefix (str): Optional prefix (digits only, at most 12 characters).
                      If provided, the remaining digits will be randomized.

    Returns:
        str: A 13-digit GTIN-13 code with a valid check digit.
    """

    if prefix:
        if len(prefix) > GTIN13_PREFIX_LENGTH or not prefix.isdigit():
            raise ValueError(
                "Prefix must be digits and less than or equal %d characters."
                % GTIN13_PREFIX_LENGTH
            )
    length = GTIN13_PREFIX_LENGTH - len(prefix)
    random_jan = prefix + "".join(random.choices("0123456789", k=length))
    last_digit = _get_last_jan_digit(random_jan)
    return random_jan + str(last_digit)


def random_gtin_8(prefix: str = "") -> str:
    """
    Generate a random GTIN-8 (Global Trade Item Number) code.

    Args:
        prefix (str): Optional prefix (digits only, at most 7 characters).
                      If provided, the remaining digits will be randomized.

    Returns:
        str: An 8-digit GTIN-8 code with a valid check digit.
    """
    if prefix:
        if len(prefix) > GTIN8_PREFIX_LENGTH or not prefix.isdigit():
            raise ValueError(
                "Prefix must be digits and less than or equal %d characters."
                % GTIN8_PREFIX_LENGTH
            )
    length = GTIN8_PREFIX_LENGTH - len(prefix)
    random_jan = prefix + "".join(random.choices("0123456789", k=length))
    last_digit = _get_last_jan_digit(random_jan)
    return random_jan + str(last_digit)


def random_gtin_14(prefix: str = "") -> str:
    """
    Generate a random GTIN-14 (Global Trade Item Number) code.

    Args:
        prefix (str): Optional prefix (digits only, at most 13 characters).
                      If not provided, defaults to '1'. The remaining digits will be randomized.

    Returns:
        str: A 14-digit GTIN-14 code with a valid check digit.
    """
    if not prefix:
        prefix = "1"
    if len(prefix) > GTIN14_PREFIX_LENGTH or not prefix.isdigit():
        raise ValueError(
            "Prefix must be digits and less than or equal %d characters."
            % GTIN14_PREFIX_LENGTH
        )
    length = GTIN14_PREFIX_LENGTH - len(prefix)
    random_jan = prefix + "".join(random.choices("0123456789", k=length))
    last_digit = _get_last_jan_digit(random_jan)
    return random_jan + str(last_digit)


def random_upc_12(prefix: str = "") -> str:
    """
    Generate a random UPC-12 (Universal Product Code) code.

    Args:
        prefix (str): Optional prefix (digits only, at most 11 characters).
                      If provided, the remaining digits will be randomized.

    Returns:
        str: A 12-digit UPC-12 code with a valid check digit.
    """
    if prefix:
        if len(prefix) > UPC12_PREFIX_LENGTH or not prefix.isdigit():
            raise ValueError(
                "Prefix must be digits and less than or equal %d characters."
                % UPC12_PREFIX_LENGTH
            )
    length = UPC12_PREFIX_LENGTH - len(prefix)
    random_jan = prefix + "".join(random.choices("0123456789", k=length))
    last_digit = _get_last_jan_digit(random_jan)
    return random_jan + str(last_digit)


def random_sscc_18(prefix: str = "") -> str:
    """
    Generate a random SSCC-18 (Serial Shipping Container Code) code.

    Args:
        prefix (str): Optional prefix (digits only, at most 17 characters).
                      If not provided, defaults to '0'. The remaining digits will be randomized.

    Returns:
        str: An 18-digit SSCC-18 code with a valid check digit.
    """
    if not prefix:
        prefix = "0"
    if len(prefix) > SSCC18_PREFIX_LENGTH or not prefix.isdigit():
        raise ValueError(
            "Prefix must be digits and less than or equal %d characters."
            % SSCC18_PREFIX_LENGTH
        )
    length = SSCC18_PREFIX_LENGTH - len(prefix)
    random_jan = prefix + "".join(random.choices("0123456789", k=length))
    last_digit = _get_last_jan_digit(random_jan)
    return random_jan + str(last_digit)


def random_grai_14(prefix: str = "") -> str:
    """
    Generate a random GRAI-14 (Global Returnable Asset Identifier) code.

    Args:
        prefix (str): Optional prefix (digits only, at most 13 characters).
                      If not provided, defaults to '0'. The remaining digits will be randomized.

    Returns:
        str: A 14-digit GRAI-14 code with a valid check digit.
    """
    if not prefix:
        prefix = "0"
    if len(prefix) > GRAI14_PREFIX_LENGTH or not prefix.isdigit():
        raise ValueError(
            "Prefix must be digits and less than or equal %d characters."
            % GRAI14_PREFIX_LENGTH
        )
    length = GRAI14_PREFIX_LENGTH - len(prefix)
    random_jan = prefix + "".join(random.choices("0123456789", k=length))
    last_digit = _get_last_jan_digit(random_jan)
    return random_jan + str(last_digit)


def is_valid(jan_code: str) -> bool:
    """
    Validate a given JAN code by checking its length, digit composition, and check digit.

    Args:
        jan_code (str): The JAN code to validate.

    Returns:
        bool: True if the JAN code is valid, False otherwise.
    """
    if len(jan_code) < 4:
        return False
    if not jan_code.isdigit():
        return False
    base_code = jan_code[:-1]
    expected_check = _get_last_jan_digit(base_code)
    return int(jan_code[-1]) == expected_check


def random_jan_code(length: int, prefix: str = "") -> str:
    """
    Generate a random JAN code of specified length with a valid check digit.

    This function allows creating custom-length JAN codes for testing or specialized use cases.
    The generated code will have exactly the specified length, including the check digit.

    Args:
        length (int): The desired total length of the JAN code (including check digit).
                      Must be between 4 and 32 (inclusive).
        prefix (str): Optional prefix consisting only of digits. The prefix length must be
                      less than the total length to allow space for at least one random digit
                      and the check digit. If provided, the remaining digits will be randomized.

    Returns:
        str: A JAN code of the specified length with a valid check digit.

    Raises:
        ValueError: If length is not an integer between 4 and 32, or if prefix contains
                   non-digit characters or is too long for the given length.

    Examples:
        random_jan_code(8)      # Generate an 8-digit code
        random_jan_code(13, "45")  # Generate a 13-digit code starting with "45"
    """
    if not isinstance(length, int) or length < 4 or length > 32:
        raise ValueError("Length must be an integer between 4 and 32.")
    if prefix and (not prefix.isdigit() or len(prefix) >= length):
        raise ValueError(
            "Prefix must be digits and shorter than the total length (%d)." % length
        )
    remaining_length = length - len(prefix) - 1
    if remaining_length < 0:
        raise ValueError("Prefix is too long for the specified length.")
    random_jan = prefix + "".join(random.choices("0123456789", k=remaining_length))
    last_digit = _get_last_jan_digit(random_jan)
    return random_jan + str(last_digit)
