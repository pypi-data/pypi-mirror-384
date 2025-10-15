import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecureStorage:
    """Handles encryption and decryption of sensitive data like API keys."""
    
    def __init__(self):
        self._key = None
    
    def _get_machine_key(self) -> bytes:
        """Generate a machine-specific key for encryption."""
        # Use machine-specific information to generate a consistent key
        machine_info = f"{os.environ.get('USER', 'default')}{os.environ.get('HOME', 'default')}"
        salt = b'shell_genie_salt_2023'  # Fixed salt for consistency
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(machine_info.encode()))
        return key
    
    def _get_cipher(self) -> Fernet:
        """Get the Fernet cipher instance."""
        if self._key is None:
            self._key = self._get_machine_key()
        return Fernet(self._key)
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key for secure storage."""
        if not api_key:
            return api_key
        
        cipher = self._get_cipher()
        encrypted_bytes = cipher.encrypt(api_key.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt an API key from storage."""
        if not encrypted_key:
            return encrypted_key
        
        try:
            cipher = self._get_cipher()
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted_bytes = cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception:
            # If decryption fails, assume it's an unencrypted key (backward compatibility)
            return encrypted_key
    
    def is_encrypted(self, value: str) -> bool:
        """Check if a value appears to be encrypted."""
        if not value:
            return False
        
        try:
            # Try to decode as base64 - encrypted values should be base64 encoded
            base64.urlsafe_b64decode(value.encode())
            # If it decodes successfully and is long enough, it's probably encrypted
            # Encrypted values are typically much longer than API keys
            return len(value) > 50
        except Exception:
            return False


# Global instance for easy access
secure_storage = SecureStorage()