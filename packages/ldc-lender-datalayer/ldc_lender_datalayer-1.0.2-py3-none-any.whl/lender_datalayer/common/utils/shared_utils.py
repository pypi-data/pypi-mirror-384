"""
Data Layer Shared Utilities Module

This module contains shared utility functions used by data layer mappers.
Only includes utilities that are actually used in the data layer.
"""

from ..constants import MaskingConstants


def mask_text(data, masking_format=None, masking_char='*', start_visible=4,
              end_visible=4):
    """Masks data according to the provided format.
    Args:
    data: The data to be masked (string).
    mask_format: A constant defining the masking format (MASK_BETWEEN,
    MASK_LEFT, MASK_RIGHT).
    Returns:
    The masked data (string).
    """
    if not data:
        return data
    if not masking_format:
        # Mask all characters by default
        return masking_char * len(data)
    else:
        # Apply masking based on format
        if masking_format == MaskingConstants.MASK_BETWEEN:
            if "@" in data:
                at_index = data.find("@")
                masked_data = (
                    f"{data[:start_visible]}"
                    f"{masking_char * (at_index - start_visible)}"
                    f"{data[at_index:]}"
                )
            else:
                masked_data = (f"{data[:start_visible]}"
                               f"{masking_char * (len(data) - 2 * start_visible)}"
                               f"{data[-end_visible:]}")

        elif masking_format == MaskingConstants.MASK_LEFT:
            masked_data = (f"{masking_char * (max(len(data) - start_visible, 0))}"
                           f"{data[-start_visible:]}")

        elif masking_format == MaskingConstants.MASK_RIGHT:
            masked_data = (f"{data[:start_visible]}"
                           f"{masking_char * (max(len(data) - start_visible, 0))}")
        else:
            masked_data = masking_char * len(data)

        return masked_data



def mask_pan(pan, source):
    """
    Masks pan according to the provided source's format.

    If the source is LDC, the pan will be masked using the specified
    format and masking character, leaving a specified number of characters
    visible at the beginning. For other sources, the pan will be
    returned unmasked.

    Args:
        pan (str): The pan to be masked.
        source (str): The source for which masking is to be done.

    Returns:
        str: The masked pan if the source is LDC, otherwise the original pan.
    """
    if source in MaskingConstants.MASK_SOURCE_LIST:
        return mask_text(
            data=pan,
            masking_format=MaskingConstants.PAN['masking_format'],
            masking_char=MaskingConstants.PAN['masking_char'],
        )

    return pan


def mask_aadhar(aadhar, source):
    """
    Masks aadhar according to the provided source's format.

    If the source is LDC, the aadhar will be masked using the specified
    format and masking character, leaving a specified number of characters
    visible at the beginning. For other sources, the aadhar will be
    returned unmasked.

    Args:
        aadhar (str): The aadhar to be masked.
        source (str): The source for which masking is to be done.

    Returns:
        str: The masked aadhar if the source is LDC, otherwise the original
        aadhar.
    """
    if source in MaskingConstants.MASK_SOURCE_LIST:
        return mask_text(
            data=aadhar,
            masking_format=MaskingConstants.AADHAR['masking_format'],
            masking_char=MaskingConstants.AADHAR['masking_char'],
        )

    return aadhar


def mask_mobile(mobile_number, source):
    """
    Masks mobile number according to the provided source's format.

    If the source is LDC, the mobile number will be masked using the specified
    format and masking character, leaving a specified number of characters
    visible at the beginning. For other sources, the mobile number will be
    returned unmasked.

    Args:
        mobile_number (str): The mobile number to be masked.
        source (str): The source for which masking is to be done.

    Returns:
        str: The masked mobile number if the source is LDC, otherwise the
        original mobile number.
    """
    if source in MaskingConstants.MASK_SOURCE_LIST:
        return mask_text(
            data=mobile_number,
            masking_format=MaskingConstants.MOBILE['masking_format'],
            masking_char=MaskingConstants.MOBILE['masking_char'],
        )

    return mobile_number


def mask_email(email, source):
    """
    Masks an email address according to the provided source's format.

    If the source is LDC, the email address will be masked using the specified
    format and masking character, leaving a specified number of characters
    visible at the beginning. For other sources, the email address will be
    returned unmasked.

    Args:
        email (str): The email address to be masked.
        source (str): The source for which masking is to be done.

    Returns:
        str: The masked email address if the source is LDC,
        otherwise the original email address.
    """
    if source in MaskingConstants.MASK_SOURCE_LIST:
        return mask_text(
            data=email,
            masking_format=MaskingConstants.EMAIL['masking_format'],
            masking_char=MaskingConstants.EMAIL['masking_char'],
            start_visible=3,
            end_visible=3
        )

    return email

