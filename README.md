# 📡 Reliable File Transfer Protocol (Selective Repeat over UDP)

## 🚀 Overview

This project implements a **reliable file transfer protocol over UDP** using the **Selective Repeat ARQ (Automatic Repeat reQuest)** mechanism.

Unlike TCP, UDP does not guarantee delivery, ordering, or reliability. This system builds those guarantees at the **application layer**, demonstrating core transport layer concepts.

---

## 🎯 Features

* ✅ Reliable data transfer over UDP
* 🔁 Selective Repeat ARQ (per-packet retransmission)
* 📦 Chunk-based file transfer
* 🪟 Sliding window protocol
* 🔐 CRC32 checksum for data integrity
* 🔄 Resume interrupted transfers
* 📥 Out-of-order packet buffering
* ⚠️ Handles packet loss, corruption, and duplication

---

## 🧠 Protocol Design

### 📦 Packet Structure

Each packet consists of:

| Field           | Size     | Description           |
| --------------- | -------- | --------------------- |
| Sequence Number | 4 bytes  | Packet identifier     |
| Flags           | 2 bytes  | Packet type           |
| Checksum        | 4 bytes  | CRC32 integrity check |
| Data Length     | 2 bytes  | Payload size          |
| Data            | Variable | File chunk            |

---

### 🚩 Flags Used

* `FLAG_DATA` → Data packet
* `FLAG_ACK` → Acknowledgement
* `FLAG_NACK` → Negative ACK
* `FLAG_START` → Start of transfer
* `FLAG_END` → End of transfer
* `FLAG_RESUME_REQ` → Resume request
* `FLAG_RESUME_ACK` → Resume response

---

## 🔁 Selective Repeat Logic

* Sender transmits multiple packets within a **window**
* Each packet has an **independent timer**
* Receiver:

  * Accepts **out-of-order packets**
  * Buffers them
  * Sends **ACK for each packet**
* Sender:

  * Retransmits **only lost packets**
  * Slides window as ACKs arrive

---

## 🧩 Project Structure

```
CN/
│
├── packet.py               # Packet creation & parsing (shared)
├── reliability.py          # Selective Repeat logic (core)
├── protocol_constants.py   # Configurations (window, timeout)
├── utils.py                # File handling helpers
├── resume.py               # Resume logic
│
├── test_protocol.py        # Basic test
├── test_general.py         # Random loss simulation
├── test_advanced.py        # Full network simulation
│
└── README.md
```

---

## 🧪 Testing

### 1. Basic Test

Simulates packet loss and verifies retransmission:

```bash
python3 test_protocol.py
```

---

### 2. General Test

Simulates:

* Random packet loss
* Duplicate packets

```bash
python3 test_general.py
```

---

### 3. Advanced Simulation

Simulates real-world network conditions:

* Packet loss
* Corruption
* Delay (out-of-order)
* Duplicates
* Performance metrics

```bash
python3 test_advanced.py
```

---

## 📊 Sample Output

```
[LOSS] Packet 3
[CORRUPT] Packet 5
[RETX] Packet 3
[ACK] 3
```

Final Output:

```
b'Chunk-1'
b'Chunk-2'
...
```

---

## 📈 Metrics Tracked

* Total packets sent
* Packet loss count
* Corrupted packets
* Retransmissions
* Throughput (packets/sec)
* Delivery success rate

---

## 👥 Team Structure

| Role              | Responsibility                    |
| ----------------- | --------------------------------- |
| Client Engineer   | Sending, chunking, retransmission |
| Server Engineer   | Receiving, ACKs, reconstruction   |
| Protocol Engineer | Reliability logic, packet design  |

---

## 🧠 Key Concepts Demonstrated

* Transport Layer Protocol Design
* Sliding Window Mechanism
* Selective Repeat ARQ
* Error Detection (CRC32)
* Reliable Data Transfer over UDP
* Network Simulation

---

## 🎯 Learning Outcomes

* Built a **custom reliable protocol**
* Understood **how TCP works internally**
* Implemented **real-world networking concepts**
* Simulated **unreliable network conditions**

---

## 🏁 Future Improvements

* 🌐 Real socket-based client-server implementation
* 🔐 Encryption (TLS/AES)
* 📊 Visualization of performance metrics
* 🚀 Congestion control (TCP-like)

---

## 📌 Conclusion

This project demonstrates how reliability can be achieved over an unreliable protocol like UDP using **Selective Repeat ARQ**, making it a strong practical implementation of core Computer Networks concepts.

---
