"""
Cryptographic utilities for IAIndex SDK

Provides ECDSA signing, verification, and key generation utilities.
"""

import hashlib
import json
from typing import Tuple, Optional
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError
from ecdsa.util import sigencode_der, sigdecode_der
import base64


class CryptoUtils:
    """Cryptographic utilities for signing and verification"""

    @staticmethod
    def generate_keypair() -> Tuple[str, str]:
        """
        Generate a new ECDSA keypair

        Returns:
            Tuple of (private_key, public_key) as base64-encoded strings
        """
        sk = SigningKey.generate(curve=SECP256k1)
        vk = sk.get_verifying_key()

        private_key = base64.b64encode(sk.to_string()).decode('utf-8')
        public_key = base64.b64encode(vk.to_string()).decode('utf-8')

        return private_key, public_key

    @staticmethod
    def sign_data(data: dict, private_key: str) -> str:
        """
        Sign a data dictionary with ECDSA

        Args:
            data: Dictionary to sign
            private_key: Base64-encoded private key

        Returns:
            Base64-encoded signature
        """
        # Convert data to canonical JSON string
        canonical_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
        data_bytes = canonical_data.encode('utf-8')

        # Decode private key
        sk_bytes = base64.b64decode(private_key)
        sk = SigningKey.from_string(sk_bytes, curve=SECP256k1)

        # Sign the data
        signature = sk.sign(data_bytes, hashfunc=hashlib.sha256, sigencode=sigencode_der)

        # Return base64-encoded signature
        return base64.b64encode(signature).decode('utf-8')

    @staticmethod
    def verify_signature(data: dict, signature: str, public_key: str) -> bool:
        """
        Verify a signature on a data dictionary

        Args:
            data: Dictionary that was signed
            signature: Base64-encoded signature
            public_key: Base64-encoded public key

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Convert data to canonical JSON string
            canonical_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
            data_bytes = canonical_data.encode('utf-8')

            # Decode public key and signature
            vk_bytes = base64.b64decode(public_key)
            vk = VerifyingKey.from_string(vk_bytes, curve=SECP256k1)
            sig_bytes = base64.b64decode(signature)

            # Verify the signature
            vk.verify(sig_bytes, data_bytes, hashfunc=hashlib.sha256, sigdecode=sigdecode_der)
            return True
        except (BadSignatureError, Exception):
            return False

    @staticmethod
    def hash_data(data: dict) -> str:
        """
        Generate SHA-256 hash of data

        Args:
            data: Dictionary to hash

        Returns:
            Hex-encoded hash
        """
        canonical_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
        data_bytes = canonical_data.encode('utf-8')
        return hashlib.sha256(data_bytes).hexdigest()


def generate_keypair() -> Tuple[str, str]:
    """
    Convenience function to generate a new ECDSA keypair

    Returns:
        Tuple of (private_key, public_key) as base64-encoded strings
    """
    return CryptoUtils.generate_keypair()
