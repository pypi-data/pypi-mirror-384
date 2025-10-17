"""
Data Layer Encryption Utilities Module

This module contains encryption utility classes used by data layer mappers.
Only includes utilities that are actually used in the data layer.
"""

import base64
import hashlib

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from django.conf import settings


class EncryptDecryptAES256:
    """
    AES256 encryption and decryption utility class.
    Used for encrypting and decrypting sensitive data in the data layer.
    """

    def __init__(self):
        """Initialize the encryption utility with default settings."""
        self.key = self._get_encryption_key()
        self.block_size = AES.block_size

    def _get_encryption_key(self):
        """
        Get encryption key from settings or generate a default one.

        Returns:
            bytes: 32-byte encryption key for AES256
        """
        if hasattr(settings, "ENCRYPTION_KEY"):
            key = settings.ENCRYPTION_KEY.encode("utf-8")
            return hashlib.sha256(key).digest()
        else:
            # Default key - should be overridden in production
            default_key = "default_encryption_key_change_in_production"
            return hashlib.sha256(default_key.encode("utf-8")).digest()

    def encrypt_data(self, plain_text, encrypt=True):
        """
        Encrypt plain text data.

        Args:
            plain_text (str): Text to encrypt
            encrypt (bool): Whether to perform encryption (allows conditional encryption)

        Returns:
            str: Base64 encoded encrypted data or original text if encrypt=False
        """
        if not encrypt or not plain_text:
            return plain_text

        try:
            # Convert to bytes if string
            if isinstance(plain_text, str):
                plain_text = plain_text.encode("utf-8")

            # Generate random IV
            iv = get_random_bytes(self.block_size)

            # Create cipher
            cipher = AES.new(self.key, AES.MODE_CBC, iv)

            # Pad and encrypt
            padded_data = pad(plain_text, self.block_size)
            encrypted_data = cipher.encrypt(padded_data)

            # Combine IV and encrypted data
            encrypted_with_iv = iv + encrypted_data

            # Return base64 encoded result
            return base64.b64encode(encrypted_with_iv).decode("utf-8")

        except Exception as e:
            # Log error in production
            return plain_text

    def decrypt_data(self, encrypted_text, decrypt=True):
        """
        Decrypt encrypted text data.

        Args:
            encrypted_text (str): Base64 encoded encrypted text
            decrypt (bool): Whether to perform decryption (allows conditional decryption)

        Returns:
            str: Decrypted plain text or original text if decrypt=False
        """
        if not decrypt or not encrypted_text:
            return encrypted_text

        try:
            # Decode from base64
            encrypted_with_iv = base64.b64decode(encrypted_text.encode("utf-8"))

            # Extract IV and encrypted data
            iv = encrypted_with_iv[: self.block_size]
            encrypted_data = encrypted_with_iv[self.block_size :]

            # Create cipher
            cipher = AES.new(self.key, AES.MODE_CBC, iv)

            # Decrypt and unpad
            decrypted_padded = cipher.decrypt(encrypted_data)
            decrypted_data = unpad(decrypted_padded, self.block_size)

            # Return as string
            return decrypted_data.decode("utf-8")

        except Exception as e:
            # Log error in production
            return encrypted_text

    def update_encoded_value(self, key, user_data, encoded_column_key):
        if key in user_data:
            if encoded_column_key in user_data:
                decrypted_existing_value = self.decrypt_data(
                    user_data[encoded_column_key]
                )
                if decrypted_existing_value != user_data[key]:
                    user_data[encoded_column_key] = self.encrypt_data(user_data[key])
            else:
                user_data[encoded_column_key] = self.encrypt_data(user_data[key])
