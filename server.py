import socket
import os
import hashlib
import json

from packet import (
    BUFFER_SIZE, SERVER_IP, SERVER_PORT,
    FLAG_DATA, FLAG_ACK, FLAG_START, FLAG_END,
    FLAG_RESUME_REQ, FLAG_RESUME_ACK,
    create_packet, parse_packet,
)

OUTPUT_DIR         = 'received_files'
PROGRESS_FILE      = 'progress.json'
INACTIVITY_TIMEOUT = 15


def load_progress(filename):
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            data = json.load(f)
        if filename in data:
            return data[filename]
    return {'last_seq': -1, 'total_chunks': 0}


def save_progress(filename, last_seq, total_chunks):
    data = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            data = json.load(f)
    data[filename] = {'last_seq': last_seq, 'total_chunks': total_chunks}
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f)


def clear_progress(filename):
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            data = json.load(f)
        data.pop(filename, None)
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(data, f)


def compute_file_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def receive_file(sock, client_addr, filename, total_chunks, expected_hash, resume_from=0):
    print(f"\n[SERVER] Receiving '{filename}' | {total_chunks} chunks | resuming from {resume_from}")

    received_seqs = set(range(resume_from))
    ooo_buffer    = {}
    next_in_order = resume_from

    temp_path  = os.path.join(OUTPUT_DIR, f"{filename}.tmp")
    write_mode = 'ab' if resume_from > 0 else 'wb'

    # 🔑 Save old timeout and set new one
    old_timeout = sock.gettimeout()
    sock.settimeout(INACTIVITY_TIMEOUT)

    try:
        with open(temp_path, write_mode) as f:
            while len(received_seqs) < total_chunks:
                try:
                    raw, addr = sock.recvfrom(BUFFER_SIZE)
                except socket.timeout:
                    print("\n[SERVER] Transfer interrupted — saving progress")
                    save_progress(filename, next_in_order - 1, total_chunks)
                    return False

                if addr != client_addr:
                    continue

                packet = parse_packet(raw)
                if packet is None:
                    print("[SERVER] Corrupted packet dropped")
                    continue

                flags   = packet['flags']
                seq_num = packet['seq_num']

                if flags & FLAG_END:
                    print("\n[SERVER] END signal received")
                    break

                if flags & FLAG_DATA:
                    # Send ACK
                    ack = create_packet(seq_num, FLAG_ACK)
                    sock.sendto(ack, client_addr)

                    if seq_num in received_seqs:
                        continue

                    received_seqs.add(seq_num)

                    if seq_num == next_in_order:
                        f.write(packet['data'])
                        next_in_order += 1

                        while next_in_order in ooo_buffer:
                            f.write(ooo_buffer.pop(next_in_order))
                            received_seqs.add(next_in_order)
                            next_in_order += 1
                    else:
                        ooo_buffer[seq_num] = packet['data']

                    pct = len(received_seqs) / total_chunks * 100
                    print(f"\r[SERVER] {len(received_seqs)}/{total_chunks} ({pct:.1f}%)", end='', flush=True)

                    if len(received_seqs) % 100 == 0:
                        save_progress(filename, next_in_order - 1, total_chunks)

    except Exception as e:
        print(f"\n[SERVER] Error: {e}")
        save_progress(filename, next_in_order - 1, total_chunks)
        return False

    finally:
        # 🔑 ALWAYS restore timeout
        sock.settimeout(old_timeout)

    if ooo_buffer:
        with open(temp_path, 'ab') as f:
            for seq in sorted(ooo_buffer):
                f.write(ooo_buffer[seq])

    print(f"\n[SERVER] All chunks received. Verifying hash...")

    actual_hash = compute_file_hash(temp_path)

    if actual_hash == expected_hash:
        final_path = os.path.join(OUTPUT_DIR, filename)
        os.replace(temp_path, final_path)
        print(f"[SERVER] Hash match — file saved to {final_path}")
        clear_progress(filename)
        sock.sendto(create_packet(0, FLAG_END, b'SUCCESS'), client_addr)
        return True
    else:
        print(f"[SERVER] Hash mismatch — file corrupted")
        sock.sendto(create_packet(0, FLAG_END, b'HASH_FAIL'), client_addr)
        return False


def run_server():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, SERVER_PORT))
    sock.settimeout(None)  # 🔑 Always blocking in main loop

    print(f"[SERVER] Listening on {SERVER_IP}:{SERVER_PORT}")

    while True:
        try:
            raw, client_addr = sock.recvfrom(BUFFER_SIZE)
        except KeyboardInterrupt:
            print("\n[SERVER] Shutting down")
            break

        packet = parse_packet(raw)
        if packet is None:
            continue

        flags = packet['flags']

        if flags & FLAG_RESUME_REQ:
            filename     = packet['data'].decode()
            progress     = load_progress(filename)
            last_seq     = progress['last_seq']
            total_chunks = progress['total_chunks']

            print(f"[SERVER] Resume request for '{filename}' — last_seq={last_seq}")

            reply = f"{last_seq},{total_chunks}".encode()
            sock.sendto(create_packet(0, FLAG_RESUME_ACK, reply), client_addr)

        elif flags & FLAG_START:
            try:
                info = packet['data'].decode()
                filename, n_str, file_hash = info.split(',', 2)
                total_chunks = int(n_str)
            except Exception as e:
                print(f"[SERVER] Bad START packet: {e}")
                continue

            print(f"[SERVER] New transfer: '{filename}' | {total_chunks} chunks")

            progress    = load_progress(filename)
            resume_from = 0

            if progress['last_seq'] >= 0 and progress['total_chunks'] == total_chunks:
                resume_from = progress['last_seq'] + 1
                print(f"[SERVER] Resuming from chunk {resume_from}")

            ready_msg = f"READY,{resume_from}".encode()
            sock.sendto(create_packet(0, FLAG_ACK, ready_msg), client_addr)

            success = receive_file(sock, client_addr, filename, total_chunks, file_hash, resume_from)

            print(f"[SERVER] Transfer {'SUCCESS' if success else 'FAILED'} for '{filename}'\n")


if __name__ == '__main__':
    run_server()