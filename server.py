import socket
import struct
import hmac
import hashlib
from cryptography.fernet import Fernet
import base64

SERVER_IP = "127.0.0.1"
PORT = 5000
BUFFER_SIZE = 4096

FLAG_DATA = 1
FLAG_ACK = 2
FLAG_END = 4

# Shared key
SHARED_KEY = b'0123456789abcdef0123456789abcdef'
fernet_key = base64.urlsafe_b64encode(SHARED_KEY)
cipher = Fernet(fernet_key)


# -------------------------------
# Packet functions
# -------------------------------
def create_packet(seq, flags, data=b''):
    header = struct.pack("!II", seq, flags)
    return header + data


def parse_packet(packet):
    if len(packet) < 8:
        return None
    seq, flags = struct.unpack("!II", packet[:8])
    data = packet[8:]
    return {"seq_num": seq, "flags": flags, "data": data}


# -------------------------------
# Security functions
# -------------------------------
def add_security(data):
    encrypted = cipher.encrypt(data)
    tag = hmac.new(SHARED_KEY, encrypted, hashlib.sha256).digest()
    return tag + encrypted


def verify_and_decrypt(data):
    tag = data[:32]
    encrypted = data[32:]

    expected = hmac.new(SHARED_KEY, encrypted, hashlib.sha256).digest()

    if not hmac.compare_digest(tag, expected):
        return None

    return cipher.decrypt(encrypted)


# -------------------------------
# SERVER
# -------------------------------
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, PORT))

print("[SERVER] Secure UDP server running...")

received = {}

while True:
    raw, addr = sock.recvfrom(BUFFER_SIZE)

    packet = parse_packet(raw)
    if not packet:
        continue

    seq = packet['seq_num']
    flags = packet['flags']

    # DATA
    if flags & FLAG_DATA:
        decrypted = verify_and_decrypt(packet['data'])

        if decrypted is None:
            print(f"[SERVER] Packet {seq} failed authentication")
            continue

        print(f"[SERVER] Received seq {seq}")

        received[seq] = decrypted

        ack = create_packet(seq, FLAG_ACK)
        sock.sendto(ack, addr)

    # END
    elif flags & FLAG_END:
        print("[SERVER] Transfer complete")

        with open("received_file.txt", "wb") as f:
            for i in sorted(received.keys()):
                f.write(received[i])

        msg = add_security(b"File received securely")
        sock.sendto(create_packet(0, FLAG_END, msg), addr)
        break

sock.close()
