"""
Schema validation for AIIndex documents and receipts.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import jsonschema
from jsonschema import Draft7Validator, validators
from pydantic import ValidationError

from .types import AIIndexDocument, Receipt


class Validator:
    """
    Validate AIIndex documents and receipts against JSON schemas.

    Example:
        >>> validator = Validator()
        >>> is_valid, errors = validator.validate_document(doc_dict)
        >>> if not is_valid:
        ...     print(errors)
    """

    def __init__(self, schema_dir: Optional[str] = None):
        """
        Initialize validator.

        Args:
            schema_dir: Directory containing schema files. If None, uses embedded schemas.
        """
        self.schema_dir = schema_dir
        self._schemas: Dict[str, Dict] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load JSON schemas."""
        # AIIndex schema
        self._schemas['aiindex'] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["version", "publisher_id", "domain", "last_updated"],
            "properties": {
                "version": {"type": "string", "pattern": "^1\\.0$"},
                "publisher_id": {"type": "string", "minLength": 3, "maxLength": 255},
                "domain": {"type": "string", "format": "hostname"},
                "last_updated": {"type": "string", "format": "date-time"},
                "publisher": {"type": "object"},
                "entities": {"type": "array"},
                "pages": {"type": "array"},
                "faq": {"type": "array"},
                "access_policy": {"type": "object"},
                "signature": {"type": "object"},
                "verification": {"type": "object"},
                "metadata": {"type": "object"}
            }
        }

        # Receipt schema
        self._schemas['receipt'] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["version", "receipt_id", "publisher_id", "client_id", "timestamp", "signature"],
            "properties": {
                "version": {"type": "string", "pattern": "^1\\.0$"},
                "receipt_id": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
                },
                "publisher_id": {"type": "string", "minLength": 3, "maxLength": 255},
                "publisher_domain": {"type": "string"},
                "client_id": {"type": "string", "minLength": 3, "maxLength": 255},
                "client_name": {"type": "string"},
                "client_version": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "access": {"type": "object"},
                "purpose": {"type": "object"},
                "attribution": {"type": "object"},
                "signature": {
                    "type": "object",
                    "required": ["algorithm", "kid", "signature", "payload_hash"]
                },
                "metadata": {"type": "object"}
            }
        }

        # Load from files if directory provided
        if self.schema_dir:
            schema_path = Path(self.schema_dir)
            if (schema_path / "aiindex.schema.json").exists():
                with open(schema_path / "aiindex.schema.json") as f:
                    self._schemas['aiindex'] = json.load(f)
            if (schema_path / "receipts.schema.json").exists():
                with open(schema_path / "receipts.schema.json") as f:
                    self._schemas['receipt'] = json.load(f)

    def validate_document(self, document: Dict) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate an AIIndex document.

        Args:
            document: Document dictionary to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # First, validate against JSON schema
        try:
            jsonschema.validate(document, self._schemas['aiindex'])
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        # Then, validate with Pydantic for deeper validation
        try:
            AIIndexDocument(**document)
        except ValidationError as e:
            for error in e.errors():
                field = " -> ".join(str(x) for x in error['loc'])
                errors.append(f"Field '{field}': {error['msg']}")

        return len(errors) == 0, errors if errors else None

    def validate_receipt(self, receipt: Dict) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate an access receipt.

        Args:
            receipt: Receipt dictionary to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Validate against JSON schema
        try:
            jsonschema.validate(receipt, self._schemas['receipt'])
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        # Validate with Pydantic
        try:
            Receipt(**receipt)
        except ValidationError as e:
            for error in e.errors():
                field = " -> ".join(str(x) for x in error['loc'])
                errors.append(f"Field '{field}': {error['msg']}")

        return len(errors) == 0, errors if errors else None

    def validate_json_file(self, filepath: str) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate a JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Determine type based on required fields
            if 'receipt_id' in data:
                return self.validate_receipt(data)
            else:
                return self.validate_document(data)

        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {str(e)}"]
        except FileNotFoundError:
            return False, [f"File not found: {filepath}"]
        except Exception as e:
            return False, [f"Error reading file: {str(e)}"]

    def validate_access_policy(self, policy: Dict) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate an access policy.

        Args:
            policy: Access policy dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        if policy.get('receipt_required') and not policy.get('webhook_url'):
            errors.append("webhook_url is required when receipt_required is true")

        # Validate webhook URL format
        if 'webhook_url' in policy:
            url = policy['webhook_url']
            if not url.startswith(('http://', 'https://')):
                errors.append("webhook_url must start with http:// or https://")

        return len(errors) == 0, errors if errors else None

    def validate_signature(self, signature: Dict) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate a signature structure (not cryptographic verification).

        Args:
            signature: Signature dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        required_fields = ['algorithm', 'kid', 'signature', 'document_hash']
        for field in required_fields:
            if field not in signature:
                errors.append(f"Missing required field: {field}")

        if 'algorithm' in signature and signature['algorithm'] not in ['ES256', 'RS256']:
            errors.append(f"Invalid algorithm: {signature['algorithm']}")

        return len(errors) == 0, errors if errors else None

    def get_schema(self, schema_type: str) -> Dict:
        """
        Get a schema by type.

        Args:
            schema_type: 'aiindex' or 'receipt'

        Returns:
            Schema dictionary
        """
        return self._schemas.get(schema_type, {})

    def format_errors(self, errors: List[str]) -> str:
        """Format error messages for display."""
        if not errors:
            return "No errors"
        return "\n".join(f"  - {error}" for error in errors)
