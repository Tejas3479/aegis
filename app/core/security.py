import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings

class MedicalDataSecurity:
    """
    Core encryption layers for sensitive medical profile data using Fernet.
    """
    def __init__(self):
        # Derive a 32-byte key from the SECRET_KEY for Fernet compatibility
        key_material = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_material)
        self.fernet = Fernet(fernet_key)

    def encrypt_pii(self, data: str) -> str:
        """
        Encrypts sensitive patient data into a secure token.
        """
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_pii(self, token: str) -> str:
        """
        Decrypts a secure token back into raw patient data.
        """
        return self.fernet.decrypt(token.encode()).decode()

security_engine = MedicalDataSecurity()
