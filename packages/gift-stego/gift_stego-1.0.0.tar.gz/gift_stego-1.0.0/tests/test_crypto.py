"""Tests for the Crypto class"""
import unittest
from gift.core import Crypto


class TestCrypto(unittest.TestCase):
    """Test encryption and decryption functionality"""

    def test_encryption_decryption(self):
        """Test that encryption and decryption are reversible"""
        data = bytearray(b'test data here with some content')
        password = 'test_password_123'

        encrypted = Crypto.encrypt(data, password)
        decrypted = Crypto.decrypt(encrypted, password)

        self.assertEqual(data, decrypted)

    def test_wrong_password(self):
        """Test that wrong password produces different output"""
        data = bytearray(b'secret data')
        encrypted = Crypto.encrypt(data, 'password1')
        decrypted = Crypto.decrypt(encrypted, 'password2')

        self.assertNotEqual(data, decrypted)

    def test_encrypted_data_is_different(self):
        """Test that encrypted data differs from original"""
        data = bytearray(b'plaintext')
        password = 'mypassword'

        encrypted = Crypto.encrypt(data, password)

        # Encrypted should be longer (includes salt)
        self.assertGreater(len(encrypted), len(data))
        # Data should be different
        self.assertNotEqual(data, encrypted[16:])  # Skip salt

    def test_empty_data(self):
        """Test encryption of empty data"""
        data = bytearray(b'')
        password = 'password'

        encrypted = Crypto.encrypt(data, password)
        decrypted = Crypto.decrypt(encrypted, password)

        self.assertEqual(data, decrypted)

    def test_different_passwords_different_output(self):
        """Test that same data with different passwords produces different ciphertexts"""
        data = bytearray(b'same data')

        encrypted1 = Crypto.encrypt(data, 'password1')
        encrypted2 = Crypto.encrypt(data, 'password2')

        self.assertNotEqual(encrypted1, encrypted2)


if __name__ == '__main__':
    unittest.main()
