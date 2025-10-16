#!/usr/bin/env python3
"""
Basic Matryoshka Protocol Package (matp)
Core steganographic messaging with fractal encryption
"""

from setuptools import setup, find_packages

setup(
    name="matp",
    version="0.1.0",
    author="Sangeet Sharma",
    author_email="sangeet.music01@gmail.com",
    description="Matryoshka Protocol - Invisible secure messaging system",
    long_description="""
# Matryoshka Protocol - Basic Edition

The world's first truly invisible secure messaging protocol.

## Core Features
- **Ghost Steganography**: Messages hidden in normal web traffic
- **Fractal Encryption**: Self-healing Russian doll keys
- **Perfect Invisibility**: Mathematically indistinguishable from browsing
- **Plausible Deniability**: Cryptographic proof of innocence

## Installation
```bash
pip install matp
```

## Quick Start
```python
from matp import MatryoshkaProtocol

# Create protocol instances
alice = MatryoshkaProtocol()
bob = MatryoshkaProtocol()

# Send invisible message
message = "This message is completely invisible!"
ghost_msg = alice.send_message(message, use_steganography=True)

# Receive and decrypt
received = bob.receive_message(ghost_msg)
print("Received:", received)
```

Perfect for developers who need basic invisible messaging capabilities.
    """,
    long_description_content_type="text/markdown",
    url="https://github.com/sangeet01/matp",
    packages=find_packages(),
    zip_safe=False,
    python_requires=">=3.8",
    
    install_requires=[
        "cryptography>=3.4.8",
    ],
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security :: Cryptography",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP",
    ],
    
    keywords="steganography cryptography messaging invisible security",
    
    project_urls={
        "Bug Reports": "https://github.com/sangeet01/matp/issues",
        "Source": "https://github.com/sangeet01/matp",
        "Documentation": "https://github.com/sangeet01/matp/docs",
    },
)