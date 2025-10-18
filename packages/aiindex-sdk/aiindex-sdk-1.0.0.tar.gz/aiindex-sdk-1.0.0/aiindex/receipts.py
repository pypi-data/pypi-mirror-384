"""
Receipt handling with webhook server for receiving access receipts.
"""

import json
import uuid
from datetime import datetime
from typing import Callable, Dict, Optional
from threading import Thread

from flask import Flask, request, jsonify

from .types import Receipt, Access, Purpose, Attribution, Signature, HTTPMethod, ReceiptMetadata
from .validator import Validator


class ReceiptHandler:
    """
    Handle access receipts with webhook server.

    Example:
        >>> handler = ReceiptHandler()
        >>> handler.on_receipt(lambda receipt: print(f"Received: {receipt['receipt_id']}"))
        >>> handler.start_server(port=8080)
    """

    def __init__(self, validate: bool = True):
        """
        Initialize receipt handler.

        Args:
            validate: Whether to validate incoming receipts
        """
        self.app = Flask(__name__)
        self.validate = validate
        self.validator = Validator() if validate else None
        self.receipts: list[Dict] = []
        self._receipt_callback: Optional[Callable] = None

        # Setup routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup Flask routes."""

        @self.app.route('/webhook', methods=['POST'])
        def webhook():
            """Handle incoming receipt webhook."""
            try:
                receipt_data = request.get_json()

                if not receipt_data:
                    return jsonify({'error': 'No JSON data provided'}), 400

                # Validate if enabled
                if self.validate and self.validator:
                    is_valid, errors = self.validator.validate_receipt(receipt_data)
                    if not is_valid:
                        return jsonify({
                            'error': 'Invalid receipt',
                            'details': errors
                        }), 400

                # Store receipt
                self.receipts.append(receipt_data)

                # Call callback if registered
                if self._receipt_callback:
                    self._receipt_callback(receipt_data)

                return jsonify({
                    'status': 'success',
                    'receipt_id': receipt_data.get('receipt_id'),
                    'message': 'Receipt received'
                }), 200

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'receipts_received': len(self.receipts)
            }), 200

        @self.app.route('/receipts', methods=['GET'])
        def get_receipts():
            """Get all received receipts."""
            return jsonify({
                'count': len(self.receipts),
                'receipts': self.receipts
            }), 200

    def on_receipt(self, callback: Callable[[Dict], None]) -> None:
        """
        Register a callback for when receipts are received.

        Args:
            callback: Function to call with receipt data
        """
        self._receipt_callback = callback

    def start_server(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False) -> None:
        """
        Start the webhook server.

        Args:
            host: Host to bind to
            port: Port to listen on
            debug: Enable debug mode
        """
        print(f"Starting receipt webhook server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

    def start_server_background(self, host: str = '0.0.0.0', port: int = 8080) -> Thread:
        """
        Start server in background thread.

        Args:
            host: Host to bind to
            port: Port to listen on

        Returns:
            Thread object
        """
        thread = Thread(target=self.start_server, args=(host, port, False), daemon=True)
        thread.start()
        return thread

    def get_receipts(self) -> list[Dict]:
        """Get all received receipts."""
        return self.receipts

    def clear_receipts(self) -> None:
        """Clear all stored receipts."""
        self.receipts.clear()

    @staticmethod
    def create_receipt(
        publisher_id: str,
        client_id: str,
        signature: Signature,
        publisher_domain: Optional[str] = None,
        client_name: Optional[str] = None,
        client_version: Optional[str] = None,
        access: Optional[Access] = None,
        purpose: Optional[Purpose] = None,
        attribution: Optional[Attribution] = None,
        metadata: Optional[ReceiptMetadata] = None,
    ) -> Receipt:
        """
        Create a new receipt.

        Args:
            publisher_id: Publisher identifier
            client_id: Client identifier
            signature: Signature object
            publisher_domain: Publisher domain
            client_name: Client name
            client_version: Client version
            access: Access details
            purpose: Purpose of access
            attribution: Attribution details
            metadata: Additional metadata

        Returns:
            Receipt object
        """
        return Receipt(
            version="1.0",
            receipt_id=str(uuid.uuid4()),
            publisher_id=publisher_id,
            publisher_domain=publisher_domain,
            client_id=client_id,
            client_name=client_name,
            client_version=client_version,
            timestamp=datetime.utcnow(),
            access=access,
            purpose=purpose,
            attribution=attribution,
            signature=signature,
            metadata=metadata,
        )

    @staticmethod
    def send_receipt(receipt: Receipt, webhook_url: str) -> bool:
        """
        Send a receipt to a webhook URL.

        Args:
            receipt: Receipt object to send
            webhook_url: Webhook URL

        Returns:
            True if successful
        """
        import requests

        try:
            receipt_dict = receipt.model_dump(mode='json', exclude_none=True)
            response = requests.post(
                webhook_url,
                json=receipt_dict,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending receipt: {e}")
            return False


class ReceiptClient:
    """
    Client for sending access receipts.

    Example:
        >>> from aiindex import ReceiptClient, SignatureManager
        >>> client = ReceiptClient("my-client-id", "My AI App")
        >>> manager = SignatureManager()
        >>> private_key, public_key = manager.generate_keypair()
        >>> receipt = client.create_access_receipt(
        ...     publisher_id="example.com",
        ...     url="https://example.com/ai-index.json",
        ...     private_key=private_key,
        ...     key_id="key-123"
        ... )
        >>> client.send(receipt, "https://example.com/webhook")
    """

    def __init__(self, client_id: str, client_name: str, version: str = "1.0.0"):
        """
        Initialize receipt client.

        Args:
            client_id: Client identifier
            client_name: Client name
            version: Client version
        """
        self.client_id = client_id
        self.client_name = client_name
        self.version = version

    def create_access_receipt(
        self,
        publisher_id: str,
        url: str,
        private_key: bytes,
        key_id: str,
        publisher_domain: Optional[str] = None,
        status_code: int = 200,
        purpose_type: Optional[str] = None,
        purpose_description: Optional[str] = None,
        commercial: bool = False,
        attribution_method: Optional[str] = None,
    ) -> Receipt:
        """
        Create and sign an access receipt.

        Args:
            publisher_id: Publisher identifier
            url: URL accessed
            private_key: Private key for signing
            key_id: Key identifier
            publisher_domain: Publisher domain
            status_code: HTTP status code
            purpose_type: Purpose type
            purpose_description: Purpose description
            commercial: Commercial use flag
            attribution_method: Attribution method

        Returns:
            Signed Receipt object
        """
        from .signer import SignatureManager

        # Create access details
        access = Access(
            url=url,
            method=HTTPMethod.GET,
            status_code=status_code,
        )

        # Create purpose
        purpose = Purpose(
            type=purpose_type,
            description=purpose_description,
            commercial=commercial,
        ) if purpose_type else None

        # Create attribution
        attribution = Attribution(
            method=attribution_method,
        ) if attribution_method else None

        # Create metadata
        metadata = ReceiptMetadata(
            sdk_version="1.0.0",
            request_id=str(uuid.uuid4()),
        )

        # Create receipt payload for signing
        receipt_payload = {
            "version": "1.0",
            "receipt_id": str(uuid.uuid4()),
            "publisher_id": publisher_id,
            "client_id": self.client_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Sign the payload
        manager = SignatureManager()
        signature = manager.sign(receipt_payload, private_key, key_id, "ES256")

        # Create full receipt
        return ReceiptHandler.create_receipt(
            publisher_id=publisher_id,
            publisher_domain=publisher_domain,
            client_id=self.client_id,
            client_name=self.client_name,
            client_version=self.version,
            signature=signature,
            access=access,
            purpose=purpose,
            attribution=attribution,
            metadata=metadata,
        )

    def send(self, receipt: Receipt, webhook_url: str) -> bool:
        """Send a receipt to webhook URL."""
        return ReceiptHandler.send_receipt(receipt, webhook_url)
