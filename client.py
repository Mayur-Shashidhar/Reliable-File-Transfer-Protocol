import socket
import struct
import time
import hmac
import hashlib
from cryptography.fernet import Fernet
import base64

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000

WINDOW_SIZE = 4
TIMEOUT = 2
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
# CLIENT
# -------------------------------
def send_file(path):

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Read file
    chunks = []
    with open(path, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            chunks.append(data)

    total_chunks = len(chunks)

    base = 0
    next_seq = 0
    timers = {}
    acked = set()

    while base < total_chunks:

        # Send window
        while next_seq < base + WINDOW_SIZE and next_seq < total_chunks:
            if next_seq not in timers:
                secure_data = add_security(chunks[next_seq])
                pkt = create_packet(next_seq, FLAG_DATA, secure_data)
                sock.sendto(pkt, (SERVER_IP, SERVER_PORT))
                timers[next_seq] = time.time()
            next_seq += 1

        # Receive ACK
        sock.settimeout(0.5)
        try:
            raw, _ = sock.recvfrom(BUFFER_SIZE)
            packet = parse_packet(raw)

            if packet and (packet['flags'] & FLAG_ACK):
                seq = packet['seq_num']
                acked.add(seq)

                while base in acked:
                    base += 1

                pct = (base / total_chunks) * 100
                print(f"\r[CLIENT] {base}/{total_chunks} ({pct:.1f}%)", end='', flush=True)

        except socket.timeout:
            pass

        # Retransmit
        current_time = time.time()
        for seq in list(timers.keys()):
            if seq not in acked and current_time - timers[seq] > TIMEOUT:
                secure_data = add_security(chunks[seq])
                pkt = create_packet(seq, FLAG_DATA, secure_data)
                sock.sendto(pkt, (SERVER_IP, SERVER_PORT))
                timers[seq] = current_time
                print(f"\n[CLIENT] Retransmitting seq {seq}")

    # END
    sock.sendto(create_packet(0, FLAG_END), (SERVER_IP, SERVER_PORT))

    try:
        raw, _ = sock.recvfrom(BUFFER_SIZE)
        packet = parse_packet(raw)

        if packet and (packet['flags'] & FLAG_END):
            msg = verify_and_decrypt(packet['data'])
            print("\n[CLIENT] Server:", msg.decode())
    except:
        print("\n[CLIENT] No confirmation")

    sock.close()


if __name__ == "__main__":
    path = input("Enter file path: ")
    send_file(path)
