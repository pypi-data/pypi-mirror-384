"""
Proto Generation Information

This file contains information about when and how the proto bindings were generated.
Generated automatically by scripts/generate_proto.py
"""

import subprocess

# Source repository information
PROTO_REPOSITORY = "https://github.com/ehsaniara/joblet-proto"
PROTO_COMMIT_HASH = "2091bf61cc03f11e923bc7f6695b3f168996beb2"
PROTO_TAG = "v2.2.1"
GENERATION_TIMESTAMP = (
    "Wed Oct 15 08:41:44 PM UTC 2025"
)

# Protocol buffer compiler version
try:
    PROTOC_VERSION = subprocess.run(
        ["protoc", "--version"], capture_output=True, text=True
    ).stdout.strip()
except Exception:
    PROTOC_VERSION = "unknown"

# Python grpcio-tools version
GRPCIO_TOOLS_VERSION = "1.75.1"
