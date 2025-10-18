"""
IAIndex Client SDK

Provides functionality for AI clients to access content and send usage receipts.
"""

import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid
from .crypto import CryptoUtils


class IAIndexClient:
    """
    IAIndex Client for AI systems

    Enables AI clients to:
    - Access content with proper attribution
    - Send usage receipts to publishers
    - Track content usage
    """

    def __init__(
        self,
        client_id: str,
        private_key: str,
        name: Optional[str] = None,
        organization: Optional[str] = None,
        api_base_url: str = "https://api.iaindex.org"
    ):
        """
        Initialize IAIndex Client

        Args:
            client_id: Unique identifier for this AI client
            private_key: Base64-encoded ECDSA private key for signing receipts
            name: Optional name of the AI client
            organization: Optional organization name
            api_base_url: API base URL (default: deployed API)
        """
        self.client_id = client_id
        self.private_key = private_key
        self.name = name or client_id
        self.organization = organization
        self.api_base_url = api_base_url.rstrip('/')
        self.session = requests.Session()
        self._token: Optional[str] = None

        # Derive public key from private key
        from ecdsa import SigningKey, SECP256k1
        import base64
        sk_bytes = base64.b64decode(private_key)
        sk = SigningKey.from_string(sk_bytes, curve=SECP256k1)
        vk = sk.get_verifying_key()
        self.public_key = base64.b64encode(vk.to_string()).decode('utf-8')

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

    def access_content(self, url: str) -> Dict[str, Any]:
        """
        Access content and retrieve metadata

        This method fetches content from a URL and extracts IAIndex metadata
        if available. It returns both the content and the metadata needed
        for generating a receipt.

        Args:
            url: URL of the content to access

        Returns:
            Dictionary containing:
                - url: Content URL
                - publisher_domain: Extracted domain
                - metadata: Any IAIndex metadata found
                - accessed_at: Access timestamp
                - title: Content title (if available)
        """
        from urllib.parse import urlparse

        # Extract domain from URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        # Fetch content
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            content = response.text

            # Parse HTML to find IAIndex metadata
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')

            # Look for IAIndex meta tags or link to ai-index.json
            metadata = {}
            title = None

            # Get title
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()

            # Look for IAIndex link
            aiindex_link = soup.find('link', {'rel': 'aiindex'})
            if aiindex_link and aiindex_link.get('href'):
                aiindex_url = aiindex_link.get('href')
                # Fetch AIIndex document
                try:
                    if not aiindex_url.startswith('http'):
                        # Relative URL
                        aiindex_url = f"{parsed_url.scheme}://{parsed_url.netloc}{aiindex_url}"
                    index_response = self.session.get(aiindex_url, timeout=10)
                    index_response.raise_for_status()
                    metadata = index_response.json()
                except Exception:
                    pass

        except Exception as e:
            # If content fetch fails, still return basic info
            title = None
            metadata = {}

        return {
            "url": url,
            "publisher_domain": domain,
            "metadata": metadata,
            "accessed_at": datetime.now(timezone.utc).isoformat(),
            "title": title,
            "client_id": self.client_id
        }

    def send_receipt(
        self,
        content: Dict[str, Any],
        usage: Dict[str, Any]
    ) -> bool:
        """
        Send a usage receipt for accessed content

        Args:
            content: Content dictionary from access_content()
            usage: Usage information dictionary containing:
                - purpose: Usage purpose (e.g., "training", "inference")
                - context: Additional context about usage
                - model: Model name/version (optional)
                - tokens: Number of tokens processed (optional)

        Returns:
            True if receipt was successfully sent and verified
        """
        # Generate receipt ID
        receipt_id = str(uuid.uuid4())

        # Create receipt data
        timestamp = datetime.now(timezone.utc).isoformat()
        receipt_data = {
            "receipt_id": receipt_id,
            "publisher_domain": content['publisher_domain'],
            "article_url": content['url'],
            "timestamp": timestamp
        }

        # Sign the receipt
        signature = CryptoUtils.sign_data(receipt_data, self.private_key)

        # Build complete receipt
        receipt = {
            **receipt_data,
            "signature": signature,
            "client_id": self.client_id,
            "client_public_key": self.public_key,
            "client_name": self.name,
            "client_organization": self.organization,
            "usage": usage,
            "metadata": {
                "content_title": content.get('title'),
                "accessed_at": content.get('accessed_at'),
                **usage
            }
        }

        # Submit receipt to API
        try:
            url = f"{self.api_base_url}/v1/receipts/ingest"
            response = self.session.post(
                url,
                json=receipt,
                headers=self._get_headers()
            )
            response.raise_for_status()
            result = response.json()

            # Check if receipt was verified
            return result.get('verified', False)

        except requests.exceptions.RequestException as e:
            # Log error but don't fail completely
            print(f"Failed to send receipt: {e}")
            return False

    def get_usage_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get usage history for this client

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results

        Returns:
            List of receipts sent by this client
        """
        # Note: This would require a client-specific endpoint in the API
        # For now, return empty list
        return {
            "receipts": [],
            "total": 0,
            "client_id": self.client_id,
            "message": "Client-specific receipt history not yet implemented in API"
        }

    def verify_publisher(self, domain: str) -> Dict[str, Any]:
        """
        Check if a publisher domain is verified

        Args:
            domain: Publisher domain to check

        Returns:
            Verification status information
        """
        url = f"{self.api_base_url}/v1/publishers/verified-domains"

        try:
            response = self.session.get(url, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()

            # Find the domain in the list
            domains = data.get('domains', [])
            for pub in domains:
                if pub.get('domain') == domain:
                    return {
                        "verified": True,
                        "domain": domain,
                        "verified_at": pub.get('verified_at'),
                        "receipt_count": pub.get('receipt_count', 0)
                    }

            return {
                "verified": False,
                "domain": domain,
                "message": "Domain not found in verified publishers list"
            }

        except Exception as e:
            return {
                "verified": False,
                "domain": domain,
                "error": str(e)
            }
