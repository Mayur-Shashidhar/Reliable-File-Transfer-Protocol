import struct
import zlib

CHUNK_SIZE   = 1024
WINDOW_SIZE  = 10
SERVER_IP    = '127.0.0.1'
SERVER_PORT  = 5001
BUFFER_SIZE  = 2048

HEADER_FORMAT = '!IHIH'
HEADER_SIZE   = struct.calcsize(HEADER_FORMAT)

FLAG_DATA       = 0x0001
FLAG_ACK        = 0x0002
FLAG_NACK       = 0x0004
FLAG_START      = 0x0008
FLAG_END        = 0x0010
FLAG_RESUME_REQ = 0x0020
FLAG_RESUME_ACK = 0x0040


def compute_checksum(data):
    return zlib.crc32(data) & 0xFFFFFFFF


def create_packet(seq_num, flags, data=b''):
    checksum = compute_checksum(data)
    header   = struct.pack(HEADER_FORMAT, seq_num, flags, checksum, len(data))
    return header + data


def parse_packet(raw):
    if len(raw) < HEADER_SIZE:
        return None
    seq_num, flags, checksum, data_len = struct.unpack(HEADER_FORMAT, raw[:HEADER_SIZE])
    data = raw[HEADER_SIZE: HEADER_SIZE + data_len]
    if compute_checksum(data) != checksum:
        return None
    return {'seq_num': seq_num, 'flags': flags, 'data': data}
