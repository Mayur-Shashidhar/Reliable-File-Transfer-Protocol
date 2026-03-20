import time

class SelectiveRepeatSender:
    def __init__(self, window_size, timeout):
        self.window_size = window_size
        self.timeout = timeout

        self.base = 0
        self.next_seq = 0

        self.timers = {}
        self.acked = set()

    def can_send(self):
        return self.next_seq < self.base + self.window_size

    def mark_sent(self, seq):
        self.timers[seq] = time.time()
        self.next_seq += 1

    def mark_acked(self, seq):
        self.acked.add(seq)

        while self.base in self.acked:
            self.base += 1

    def get_timeouts(self):
        now = time.time()
        retransmit = []

        for seq in list(self.timers.keys()):
            if seq not in self.acked and now - self.timers[seq] > self.timeout:
                retransmit.append(seq)
                self.timers[seq] = now

        return retransmit


class SelectiveRepeatReceiver:
    def __init__(self):
        self.buffer = {}
        self.received = set()
        self.expected = 0

    def receive(self, seq, data):
        if seq in self.received:
            return []

        self.buffer[seq] = data
        self.received.add(seq)

        output = []

        while self.expected in self.buffer:
            output.append(self.buffer.pop(self.expected))
            self.expected += 1

        return output