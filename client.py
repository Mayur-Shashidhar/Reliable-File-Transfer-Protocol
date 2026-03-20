import socket
import os
import hashlib
import time

from packet import (
    BUFFER_SIZE, SERVER_IP, SERVER_PORT,
    FLAG_DATA, FLAG_ACK, FLAG_START, FLAG_END,
    FLAG_RESUME_REQ, FLAG_RESUME_ACK,
    create_packet, parse_packet,
)

CHUNK_SIZE = 1024
WINDOW_SIZE = 5
TIMEOUT = 1.0


def compute_file_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_chunks(filepath):
    chunks = []
    with open(filepath, 'rb') as f:
        while True:
            data = f.read(CHUNK_SIZE)
            if not data:
                break
            chunks.append(data)
    return chunks


def request_resume(sock, filename):
    pkt = create_packet(0, FLAG_RESUME_REQ, filename.encode())
    sock.sendto(pkt, (SERVER_IP, SERVER_PORT))

    sock.settimeout(TIMEOUT)
    try:
        raw, _ = sock.recvfrom(BUFFER_SIZE)
        packet = parse_packet(raw)
        if packet and (packet['flags'] & FLAG_RESUME_ACK):
            last_seq, _ = packet['data'].decode().split(',')
            return int(last_seq) + 1
    except:
        pass

    return 0


def wait_for_ready(sock):
    while True:
        raw, _ = sock.recvfrom(BUFFER_SIZE)
        packet = parse_packet(raw)
        if packet and (packet['flags'] & FLAG_ACK):
            msg = packet['data'].decode()
            if msg.startswith("READY"):
                _, start_from = msg.split(',')
                return int(start_from)


def send_file(filepath):
    filename = os.path.basename(filepath)
    chunks = get_chunks(filepath)
    total_chunks = len(chunks)
    file_hash = compute_file_hash(filepath)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.1)

    resume_from = request_resume(sock, filename)

    start_msg = f"{filename},{total_chunks},{file_hash}".encode()
    sock.sendto(create_packet(0, FLAG_START, start_msg), (SERVER_IP, SERVER_PORT))

    base = wait_for_ready(sock)
    print(f"[CLIENT] Starting from chunk {base}")

    next_seq = base
    acked = set()
    timers = {}

    while base < total_chunks:

        while next_seq < base + WINDOW_SIZE and next_seq < total_chunks:
            if next_seq not in timers:
                pkt = create_packet(next_seq, FLAG_DATA, chunks[next_seq])
                sock.sendto(pkt, (SERVER_IP, SERVER_PORT))
                timers[next_seq] = time.time()
            next_seq += 1

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

        except:
            pass

        current_time = time.time()
        for seq in list(timers.keys()):
            if seq not in acked and current_time - timers[seq] > TIMEOUT:
                pkt = create_packet(seq, FLAG_DATA, chunks[seq])
                sock.sendto(pkt, (SERVER_IP, SERVER_PORT))
                timers[seq] = current_time
                print(f"\n[CLIENT] Retransmitting seq {seq}")

    sock.sendto(create_packet(0, FLAG_END), (SERVER_IP, SERVER_PORT))

    try:
        raw, _ = sock.recvfrom(BUFFER_SIZE)
        packet = parse_packet(raw)
        if packet and (packet['flags'] & FLAG_END):
            print("\n[CLIENT] Server response:", packet['data'].decode())
    except:
        print("\n[CLIENT] No final confirmation")

    sock.close()


if __name__ == "__main__":
    path = input("Enter file path: ").strip()

    if not os.path.exists(path):
        print("File not found")
    else:
        send_file(path)