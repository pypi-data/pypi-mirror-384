"""
Command-line interface for AIIndex SDK.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click

from .generator import AIIndexGenerator
from .signer import SignatureManager
from .validator import Validator
from .receipts import ReceiptHandler


@click.group()
@click.version_option(version='1.0.0', prog_name='aiindex-gen')
def cli():
    """AIIndex Generator - Create and manage AI-readable website indexes."""
    pass


@cli.command()
@click.option('--domain', prompt='Domain name', help='Your website domain')
@click.option('--publisher-id', prompt='Publisher ID', help='Unique publisher identifier')
@click.option('--output', '-o', default='ai-index.json', help='Output file path')
def init(domain: str, publisher_id: str, output: str):
    """Initialize a new AI-index.json file."""
    try:
        generator = AIIndexGenerator(publisher_id, domain)
        doc = generator.build()

        # Convert to dict and save
        with open(output, 'w') as f:
            json.dump(doc.model_dump(exclude_none=True, mode='json'), f, indent=2, default=str)

        click.echo(f"✓ Created {output}")
        click.echo(f"  Domain: {domain}")
        click.echo(f"  Publisher ID: {publisher_id}")
        click.echo(f"\nNext steps:")
        click.echo(f"  1. Edit {output} to add your content")
        click.echo(f"  2. Run 'aiindex-gen build' to crawl your site")
        click.echo(f"  3. Run 'aiindex-gen sign' to sign the document")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('--input', '-i', default='ai-index.json', help='Input file to update')
@click.option('--output', '-o', help='Output file (default: same as input)')
@click.option('--max-pages', default=10, help='Maximum pages to crawl')
@click.option('--max-depth', default=3, help='Maximum crawl depth')
def build(url: str, input: str, output: Optional[str], max_pages: int, max_depth: int):
    """Build AI-index.json by crawling a website."""
    try:
        # Load existing file if it exists
        if Path(input).exists():
            with open(input, 'r') as f:
                data = json.load(f)
            publisher_id = data.get('publisher_id')
            domain = data.get('domain')
        else:
            click.echo(f"Error: {input} not found. Run 'aiindex-gen init' first.", err=True)
            sys.exit(1)

        click.echo(f"Crawling {url}...")
        generator = AIIndexGenerator(publisher_id, domain)

        # Crawl the site
        num_pages = generator.crawl(url, max_pages=max_pages, max_depth=max_depth)
        click.echo(f"✓ Crawled {num_pages} pages")

        # Extract metadata
        click.echo("Extracting metadata...")
        generator.extract_metadata(url)

        # Build document
        doc = generator.build()

        # Save
        output_file = output or input
        with open(output_file, 'w') as f:
            json.dump(doc.model_dump(exclude_none=True, mode='json'), f, indent=2, default=str)

        click.echo(f"✓ Saved to {output_file}")
        click.echo(f"  Pages: {len(generator.pages)}")
        if generator.publisher and generator.publisher.name:
            click.echo(f"  Publisher: {generator.publisher.name}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('file', type=click.Path(exists=True))
def verify(file: str):
    """Verify an AI-index.json file."""
    try:
        click.echo(f"Verifying {file}...")

        validator = Validator()
        is_valid, errors = validator.validate_json_file(file)

        if is_valid:
            click.echo("✓ Valid AI-index.json file")

            # Load and display info
            with open(file, 'r') as f:
                data = json.load(f)

            click.echo(f"\nDocument Information:")
            click.echo(f"  Version: {data.get('version')}")
            click.echo(f"  Publisher ID: {data.get('publisher_id')}")
            click.echo(f"  Domain: {data.get('domain')}")
            click.echo(f"  Last Updated: {data.get('last_updated')}")

            if 'pages' in data:
                click.echo(f"  Pages: {len(data['pages'])}")
            if 'entities' in data:
                click.echo(f"  Entities: {len(data['entities'])}")
            if 'faq' in data:
                click.echo(f"  FAQs: {len(data['faq'])}")
            if 'signature' in data:
                click.echo(f"  Signed: Yes (algorithm: {data['signature']['algorithm']})")
            else:
                click.echo(f"  Signed: No")

        else:
            click.echo("✗ Invalid AI-index.json file", err=True)
            click.echo("\nErrors:")
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--key-id', prompt='Key ID', help='Key identifier')
@click.option('--private-key', type=click.Path(exists=True), help='Private key file')
@click.option('--algorithm', default='ES256', type=click.Choice(['ES256', 'RS256']), help='Signature algorithm')
@click.option('--output', '-o', help='Output file (default: same as input)')
@click.option('--generate-key', is_flag=True, help='Generate a new keypair')
def sign(file: str, key_id: str, private_key: Optional[str], algorithm: str, output: Optional[str], generate_key: bool):
    """Sign an AI-index.json file."""
    try:
        # Load document
        with open(file, 'r') as f:
            document = json.load(f)

        manager = SignatureManager()

        # Generate keypair if requested
        if generate_key:
            click.echo(f"Generating new {algorithm} keypair...")
            priv_key, pub_key = manager.generate_keypair(algorithm)

            # Save keys
            priv_file = f"{key_id}.private.pem"
            pub_file = f"{key_id}.public.pem"
            manager.save_key(priv_key, priv_file)
            manager.save_key(pub_key, pub_file)

            click.echo(f"✓ Saved private key to {priv_file}")
            click.echo(f"✓ Saved public key to {pub_file}")
            click.echo(f"\n⚠️  Keep {priv_file} secure and never commit it to version control!")

            private_key_data = priv_key
        elif private_key:
            # Load existing key
            private_key_data = manager.load_key(private_key)
        else:
            click.echo("Error: Either --private-key or --generate-key is required", err=True)
            sys.exit(1)

        # Sign document
        click.echo(f"Signing document with {algorithm}...")
        signed_doc = manager.sign_document(document, private_key_data, key_id, algorithm)

        # Save
        output_file = output or file
        with open(output_file, 'w') as f:
            json.dump(signed_doc, f, indent=2, default=str)

        click.echo(f"✓ Signed document saved to {output_file}")
        click.echo(f"  Algorithm: {algorithm}")
        click.echo(f"  Key ID: {key_id}")
        click.echo(f"  Document Hash: {signed_doc['signature']['document_hash'][:16]}...")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--port', '-p', default=8080, help='Port to listen on')
@click.option('--host', default='0.0.0.0', help='Host to bind to')
def serve(port: int, host: str):
    """Start a webhook server to receive access receipts."""
    try:
        click.echo(f"Starting receipt webhook server...")
        click.echo(f"Listening on http://{host}:{port}")
        click.echo(f"Webhook endpoint: http://{host}:{port}/webhook")
        click.echo(f"Health check: http://{host}:{port}/health")
        click.echo(f"\nPress Ctrl+C to stop\n")

        handler = ReceiptHandler(validate=True)

        # Register callback to display receipts
        def on_receipt(receipt):
            click.echo(f"→ Receipt received: {receipt['receipt_id']}")
            click.echo(f"  Client: {receipt.get('client_name', receipt['client_id'])}")
            click.echo(f"  Publisher: {receipt['publisher_id']}")
            click.echo(f"  Timestamp: {receipt['timestamp']}")

        handler.on_receipt(on_receipt)
        handler.start_server(host=host, port=port, debug=False)

    except KeyboardInterrupt:
        click.echo("\n\nShutting down...")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('file', type=click.Path(exists=True))
def info(file: str):
    """Display information about an AI-index.json file."""
    try:
        with open(file, 'r') as f:
            data = json.load(f)

        click.echo(f"\n{file}")
        click.echo("=" * len(file))

        # Basic info
        click.echo(f"\nVersion: {data.get('version')}")
        click.echo(f"Publisher ID: {data.get('publisher_id')}")
        click.echo(f"Domain: {data.get('domain')}")
        click.echo(f"Last Updated: {data.get('last_updated')}")

        # Publisher info
        if 'publisher' in data and data['publisher']:
            pub = data['publisher']
            click.echo(f"\nPublisher:")
            if pub.get('name'):
                click.echo(f"  Name: {pub['name']}")
            if pub.get('description'):
                click.echo(f"  Description: {pub['description']}")
            if pub.get('url'):
                click.echo(f"  URL: {pub['url']}")

        # Content stats
        click.echo(f"\nContent:")
        if 'pages' in data:
            click.echo(f"  Pages: {len(data['pages'])}")
        if 'entities' in data:
            click.echo(f"  Entities: {len(data['entities'])}")
        if 'faq' in data:
            click.echo(f"  FAQs: {len(data['faq'])}")

        # Access policy
        if 'access_policy' in data:
            policy = data['access_policy']
            click.echo(f"\nAccess Policy:")
            click.echo(f"  Allowed: {policy.get('allowed', 'N/A')}")
            click.echo(f"  Attribution Required: {policy.get('attribution_required', 'N/A')}")
            click.echo(f"  Commercial Use: {policy.get('commercial_use', 'N/A')}")
            click.echo(f"  Receipt Required: {policy.get('receipt_required', 'N/A')}")
            if policy.get('webhook_url'):
                click.echo(f"  Webhook URL: {policy['webhook_url']}")

        # Signature
        if 'signature' in data:
            sig = data['signature']
            click.echo(f"\nSignature:")
            click.echo(f"  Algorithm: {sig['algorithm']}")
            click.echo(f"  Key ID: {sig['kid']}")
            click.echo(f"  Document Hash: {sig['document_hash'][:32]}...")
            if sig.get('signed_at'):
                click.echo(f"  Signed At: {sig['signed_at']}")

        click.echo()

    except json.JSONDecodeError:
        click.echo(f"Error: Invalid JSON file", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
