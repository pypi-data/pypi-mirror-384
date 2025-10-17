from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64
import os

class CryptoManager:
    def __init__(self, str_key):
        """
        Initializes a new instance of the CryptoManager class.

        Args:
            str_key (str): The base64-encoded key used for encryption and decryption.

        Returns:
            None

        Raises:
            None

        Notes:
            - The `str_key` parameter is expected to be a base64-encoded string.
            - The `key` attribute is set to the decoded value of `str_key`.
            - The `backend` attribute is set to the default backend provided by the cryptography library.
        """
        self.key = base64.urlsafe_b64decode(str_key.encode('utf-8'))
        self.backend = default_backend()

    def encrypt(self, plaintext):
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(plaintext.encode()) + padder.finalize()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(iv + ciphertext).decode('utf-8')

    def decrypt(self, ciphertext):
        data = base64.b64decode(ciphertext)
        iv = data[:16]
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(data[16:]) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()
        return plaintext.decode('utf-8')
