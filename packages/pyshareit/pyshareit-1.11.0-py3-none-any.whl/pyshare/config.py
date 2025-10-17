# pyshare/config.py

DISCOVERY_PORT = 50001
TCP_PORT = 50002
DISCOVERY_INTERVAL = 2
BROADCAST_ADDRESS = '<broadcast>'
DISCOVERY_MAGIC = b"PYSHARE_DISCOVERY_V2"
RESPONSE_MAGIC = b"PYSHARE_RESPONSE_V2"
# Increased buffer size for significantly faster transfers
BUFFER_SIZE = 1048576 # 1 MB