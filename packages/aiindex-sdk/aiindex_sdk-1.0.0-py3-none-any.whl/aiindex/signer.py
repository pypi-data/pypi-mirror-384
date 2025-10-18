"""
Cryptographic signature management using ECDSA and RSA.
"""

import base64
import hashlib
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa, padding
from cryptography.exceptions import InvalidSignature

from .types import Signature, SignatureAlgorithm


class SignatureManager:
    """
    Manage cryptographic signatures for AIIndex documents and receipts.

    Supports ES256 (ECDSA) and RS256 (RSA) algorithms.

    Example:
        >>> manager = SignatureManager()
        >>> private_key, public_key = manager.generate_keypair("ES256")
        >>> signature = manager.sign(data, private_key, "key_id_123", "ES256")
        >>> is_valid = manager.verify(data, signature, public_key)
    """

    def __init__(self):
        self.backend = default_backend()

    def generate_keypair(
        self, algorithm: str = "ES256"
    ) -> Tuple[bytes, bytes]:
        """
        Generate a new public/private keypair.

        Args:
            algorithm: Signature algorithm ("ES256" or "RS256")

        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        if algorithm == "ES256":
            private_key = ec.generate_private_key(ec.SECP256R1(), self.backend)
        elif algorithm == "RS256":
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=self.backend
            )
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Serialize public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return private_pem, public_pem

    def sign(
        self,
        data: Dict,
        private_key_pem: bytes,
        kid: str,
        algorithm: str = "ES256"
    ) -> Signature:
        """
        Sign data and create a signature object.

        Args:
            data: Data to sign (will be JSON serialized)
            private_key_pem: Private key in PEM format
            kid: Key identifier
            algorithm: Signature algorithm

        Returns:
            Signature object
        """
        # Serialize data
        if isinstance(data, dict):
            payload = json.dumps(data, sort_keys=True, separators=(',', ':'))
        else:
            payload = str(data)

        payload_bytes = payload.encode('utf-8')

        # Compute hash
        document_hash = hashlib.sha256(payload_bytes).hexdigest()

        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
            backend=self.backend
        )

        # Sign based on algorithm
        if algorithm == "ES256":
            signature_bytes = private_key.sign(
                payload_bytes,
                ec.ECDSA(hashes.SHA256())
            )
        elif algorithm == "RS256":
            signature_bytes = private_key.sign(
                payload_bytes,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        # Encode signature
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')

        return Signature(
            algorithm=SignatureAlgorithm(algorithm),
            kid=kid,
            signature=signature_b64,
            document_hash=document_hash,
            signed_at=datetime.utcnow()
        )

    def verify(
        self,
        data: Dict,
        signature: Signature,
        public_key_pem: bytes
    ) -> bool:
        """
        Verify a signature.

        Args:
            data: Original data that was signed
            signature: Signature object to verify
            public_key_pem: Public key in PEM format

        Returns:
            True if signature is valid
        """
        try:
            # Serialize data the same way
            if isinstance(data, dict):
                payload = json.dumps(data, sort_keys=True, separators=(',', ':'))
            else:
                payload = str(data)

            payload_bytes = payload.encode('utf-8')

            # Verify hash
            computed_hash = hashlib.sha256(payload_bytes).hexdigest()
            if computed_hash != signature.document_hash:
                return False

            # Decode signature
            signature_bytes = base64.b64decode(signature.signature)

            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem,
                backend=self.backend
            )

            # Verify based on algorithm
            if signature.algorithm == SignatureAlgorithm.ES256:
                public_key.verify(
                    signature_bytes,
                    payload_bytes,
                    ec.ECDSA(hashes.SHA256())
                )
            elif signature.algorithm == SignatureAlgorithm.RS256:
                public_key.verify(
                    signature_bytes,
                    payload_bytes,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
            else:
                return False

            return True

        except InvalidSignature:
            return False
        except Exception as e:
            print(f"Verification error: {e}")
            return False

    def sign_document(
        self,
        document: Dict,
        private_key_pem: bytes,
        kid: str,
        algorithm: str = "ES256"
    ) -> Dict:
        """
        Sign an AIIndex document and add signature field.

        Args:
            document: AIIndex document dictionary
            private_key_pem: Private key in PEM format
            kid: Key identifier
            algorithm: Signature algorithm

        Returns:
            Document with signature field added
        """
        # Create a copy without signature field
        doc_copy = document.copy()
        doc_copy.pop('signature', None)

        # Sign the document
        signature = self.sign(doc_copy, private_key_pem, kid, algorithm)

        # Add signature to document
        document['signature'] = signature.model_dump(mode='json')

        return document

    def verify_document(
        self,
        document: Dict,
        public_key_pem: bytes
    ) -> bool:
        """
        Verify a signed AIIndex document.

        Args:
            document: Signed AIIndex document
            public_key_pem: Public key in PEM format

        Returns:
            True if signature is valid
        """
        if 'signature' not in document:
            return False

        # Extract signature
        signature_data = document['signature']
        signature = Signature(**signature_data)

        # Create document without signature
        doc_copy = document.copy()
        doc_copy.pop('signature')

        # Verify
        return self.verify(doc_copy, signature, public_key_pem)

    def save_key(self, key_pem: bytes, filepath: str) -> None:
        """Save a key to file."""
        with open(filepath, 'wb') as f:
            f.write(key_pem)

    def load_key(self, filepath: str) -> bytes:
        """Load a key from file."""
        with open(filepath, 'rb') as f:
            return f.read()

    @staticmethod
    def hash_data(data: str) -> str:
        """Compute SHA-256 hash of data."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
