"""
IAIndex Publisher SDK

Provides functionality for content publishers to register, add entries,
generate indexes, and verify receipts.
"""

import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid
from .crypto import CryptoUtils


class IAIndexPublisher:
    """
    IAIndex Publisher client for content publishers

    Enables publishers to:
    - Initialize their profile
    - Add content entries to their index
    - Generate signed index files
    - Verify receipts from AI clients
    """

    def __init__(
        self,
        domain: str,
        private_key: str,
        name: str,
        contact: str,
        api_base_url: str = "https://api.iaindex.org"
    ):
        """
        Initialize IAIndex Publisher

        Args:
            domain: Publisher's domain (e.g., "example.com")
            private_key: Base64-encoded ECDSA private key
            name: Publisher name
            contact: Contact email
            api_base_url: API base URL (default: deployed API)
        """
        self.domain = domain
        self.private_key = private_key
        self.name = name
        self.contact = contact
        self.api_base_url = api_base_url.rstrip('/')
        self.entries: List[Dict[str, Any]] = []
        self.session = requests.Session()
        self._token: Optional[str] = None

    def _authenticate(self) -> str:
        """
        Authenticate with the API and get access token

        Returns:
            Access token
        """
        if self._token:
            return self._token

        url = f"{self.api_base_url}/v1/auth/login"
        response = self.session.post(
            url,
            json={"username": "admin", "password": "changeme"}
        )
        response.raise_for_status()
        data = response.json()
        self._token = data.get("access_token")

        # Set authorization header for future requests
        self.session.headers.update({
            "Authorization": f"Bearer {self._token}"
        })

        return self._token

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication"""
        self._authenticate()
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }

    def initialize(self) -> Dict[str, Any]:
        """
        Initialize publisher profile with the API

        This creates or updates the publisher's profile and initiates
        domain verification if needed.

        Returns:
            Verification response with instructions
        """
        url = f"{self.api_base_url}/v1/publishers/verify"

        payload = {
            "domain": self.domain,
            "method": "dns_txt"
        }

        response = self.session.post(
            url,
            json=payload,
            headers=self._get_headers()
        )

        if response.status_code == 409:
            # Already verified
            return {
                "status": "already_verified",
                "domain": self.domain,
                "message": "Domain is already verified"
            }

        response.raise_for_status()
        return response.json()

    def add_entry(self, entry: Dict[str, Any]) -> str:
        """
        Add a content entry to the index

        Args:
            entry: Content entry with fields:
                - url: Content URL (required)
                - title: Content title
                - author: Author name
                - published_date: Publication date (ISO 8601)
                - license: License information dict
                - metadata: Additional metadata

        Returns:
            Entry ID (UUID)
        """
        entry_id = str(uuid.uuid4())

        # Validate required fields
        if 'url' not in entry:
            raise ValueError("Entry must have a 'url' field")

        # Add entry metadata
        entry_data = {
            "id": entry_id,
            "url": entry['url'],
            "title": entry.get('title', ''),
            "author": entry.get('author', ''),
            "published_date": entry.get('published_date', datetime.now(timezone.utc).isoformat()),
            "license": entry.get('license', {}),
            "metadata": entry.get('metadata', {}),
            "added_at": datetime.now(timezone.utc).isoformat()
        }

        self.entries.append(entry_data)
        return entry_id

    def generate_index(self) -> Dict[str, Any]:
        """
        Generate a signed index file from all added entries

        Returns:
            Signed index document containing:
                - publisher: Publisher information
                - entries: List of content entries
                - signature: Cryptographic signature
                - generated_at: Generation timestamp
        """
        # Build index document
        index_doc = {
            "publisher": {
                "domain": self.domain,
                "name": self.name,
                "contact": self.contact
            },
            "entries": self.entries,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.1"
        }

        # Sign the index
        signature = CryptoUtils.sign_data(index_doc, self.private_key)

        # Add signature to document
        signed_doc = {
            **index_doc,
            "signature": signature
        }

        return signed_doc

    def verify_receipt(self, receipt: Dict[str, Any]) -> bool:
        """
        Verify a receipt from an AI client

        Args:
            receipt: Receipt dictionary containing:
                - receipt_id: Unique receipt ID
                - publisher_domain: Should match this publisher's domain
                - article_url: URL of accessed content
                - timestamp: Access timestamp
                - signature: Client's signature
                - client_public_key: Client's public key

        Returns:
            True if receipt is valid, False otherwise
        """
        # Verify publisher domain matches
        if receipt.get('publisher_domain') != self.domain:
            return False

        # Verify the receipt signature
        client_public_key = receipt.get('client_public_key')
        if not client_public_key:
            return False

        # Extract data to verify
        receipt_data = {
            "receipt_id": receipt.get('receipt_id'),
            "publisher_domain": receipt.get('publisher_domain'),
            "article_url": receipt.get('article_url'),
            "timestamp": receipt.get('timestamp')
        }

        signature = receipt.get('signature')
        return CryptoUtils.verify_signature(receipt_data, signature, client_public_key)

    def submit_receipt(self, receipt: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a receipt to the API for verification and storage

        Args:
            receipt: Receipt to submit

        Returns:
            API response with verification status
        """
        url = f"{self.api_base_url}/v1/receipts/ingest"

        response = self.session.post(
            url,
            json=receipt,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def get_receipts(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get receipts for this publisher

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of receipts
        """
        url = f"{self.api_base_url}/v1/receipts"

        params = {
            "publisher_domain": self.domain,
            "limit": limit,
            "offset": offset
        }

        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()

        response = self.session.get(
            url,
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
