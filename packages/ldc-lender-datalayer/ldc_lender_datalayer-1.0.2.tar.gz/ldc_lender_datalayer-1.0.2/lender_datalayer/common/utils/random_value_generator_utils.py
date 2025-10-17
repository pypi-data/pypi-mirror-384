import binascii
import os
import random

from django.conf import settings

from ..constants import ServerType


def generate_otp_key(char_set="0123456789"):
    if settings.SERVER_TYPE == ServerType.DEVELOPMENT:
        otp_key = random.choice(["656539", "656590", "656511"])
    else:
        otp_key = "".join([random.choice(char_set) for _ in range(6)])
    return otp_key


def generate_token_for_mono():
    return binascii.hexlify(os.urandom(20)).decode()
