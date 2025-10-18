"""
Setup script for aiindex-sdk
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='aiindex-sdk',
    version='1.0.0',
    description='Python SDK for the AIIndex Protocol - AI-readable website metadata and access control',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='AIIndex',
    author_email='contact@aiindex.org',
    url='https://github.com/aiindex/aiindex',
    license='MIT',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'aiindex-gen=aiindex.cli:cli',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Markup :: HTML',
    ],
    python_requires='>=3.8',
    keywords='ai, indexing, metadata, schema, crawling, web scraping, api',
    project_urls={
        'Documentation': 'https://aiindex.org/docs',
        'Source': 'https://github.com/aiindex/aiindex',
        'Bug Reports': 'https://github.com/aiindex/aiindex/issues',
    },
    include_package_data=True,
    zip_safe=False,
)
