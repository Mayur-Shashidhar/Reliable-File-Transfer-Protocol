def parse_resume_response(data):
    try:
        last_seq, total = data.decode().split(',')
        return int(last_seq), int(total)
    except:
        return -1, 0


def create_resume_request(filename):
    return filename.encode()