import json
import logging
import os
import struct

# Configure logging
LOG = logging.getLogger(__name__)

# Get the NODE_CHANNEL_FD environment variable with a default of -1 if not set
NODE_CHANNEL_FD = int(os.getenv("NODE_CHANNEL_FD", -1))


def _write(obj):
    """
    Write a JSON-serializable object to a file descriptor if NODE_CHANNEL_FD is valid.
    """
    # Serialize the object to a JSON string
    data = json.dumps(obj, separators=(",", ":")) + os.linesep

    # Check if NODE_CHANNEL_FD is valid
    if NODE_CHANNEL_FD == -1:
        # Do nothing if NODE_CHANNEL_FD is not set
        return

    if os.name == "nt":
        # On Windows, add a header before sending the data
        buf = data.encode("utf-8")
        header = struct.pack("<Q", 1) + struct.pack("<Q", len(buf))
        os.write(NODE_CHANNEL_FD, header + buf)
    else:
        # On Unix-like systems, write the data directly
        os.write(NODE_CHANNEL_FD, data.encode("utf-8"))


def send_message(message_type, payload):
    """
    Send a message with a specified type and payload.
    """
    obj = {
        "type": message_type,
        "payload": payload,
    }
    try:
        _write(obj)
    except Exception as e:
        LOG.warning(f"IPC error sending: {obj}", exc_info=True)


# Example usage:
if __name__ == "__main__":
    message_type = "example"
    message_payload = {"data": "Hello, world!"}
    send_message(message_type, message_payload)
