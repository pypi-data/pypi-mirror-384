"""
AIIndex SDK for Python

A Python SDK for the AIIndex Protocol - enabling AI-readable website metadata,
access control, and cryptographic verification.
"""

from .generator import AIIndexGenerator
from .signer import SignatureManager
from .receipts import ReceiptHandler
from .validator import Validator
from .types import (
    AIIndexDocument,
    Publisher,
    Entity,
    Page,
    FAQ,
    AccessPolicy,
    Signature,
    Receipt,
    Access,
    Purpose,
    Attribution,
)
from .publisher import IAIndexPublisher
from .client import IAIndexClient
from .crypto import CryptoUtils, generate_keypair

__version__ = "1.0.0"
__all__ = [
    # Core generator and validator
    "AIIndexGenerator",
    "SignatureManager",
    "ReceiptHandler",
    "Validator",
    # Type definitions
    "AIIndexDocument",
    "Publisher",
    "Entity",
    "Page",
    "FAQ",
    "AccessPolicy",
    "Signature",
    "Receipt",
    "Access",
    "Purpose",
    "Attribution",
    # API integration classes
    "IAIndexPublisher",
    "IAIndexClient",
    # Crypto utilities
    "CryptoUtils",
    "generate_keypair",
]
