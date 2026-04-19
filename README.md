# 📡 Reliable File Transfer Protocol (Selective Repeat over UDP)

## 🚀 Overview

This project implements a **reliable file transfer system over UDP** using the **Selective Repeat ARQ protocol**.

Since UDP does not provide reliability, ordering, or retransmission, this system implements these features at the **application layer**, mimicking core TCP behavior.

---

## 📖 Course Information

- Course Name : Computer Networks
- Course Code : UE24CS252B

---


## 🎯 Key Features

* ✅ Reliable data transfer over UDP
* 🔁 Selective Repeat ARQ (per-packet retransmission)
* 🪟 Sliding window protocol
* 📦 Chunk-based file transfer
* 🔐 CRC32 checksum (packet-level integrity)
* 🔒 SHA-256 (file-level integrity)
* 🔄 Resume interrupted transfers
* 📥 Out-of-order packet buffering
* 🌐 Network simulation (loss, corruption, retransmission)

---

## 🧠 Protocol Highlights

### 📦 Packet Design

Each packet contains:

* Sequence Number
* Flags (DATA, ACK, START, END, etc.)
* CRC32 Checksum
* Data Length
* Payload

---

### 🔁 Selective Repeat Logic

* Sender transmits packets within a window
* Each packet has an independent timer
* Receiver:

  * Accepts out-of-order packets
  * Buffers them
  * Sends ACK for each packet
* Sender retransmits **only lost packets**

---

## 📁 Project Structure

```bash
Reliable-File-Transfer-Protocol/
│
├── client.py                # Sender (Selective Repeat + simulation)
├── server.py                # Receiver (buffering + reconstruction)
│
├── packet.py                # Core packet structure (shared protocol)
├── reliability.py           # Selective Repeat logic (modular)
├── protocol_constants.py    # Config (window size, timeout, etc.)
├── utils.py                 # File handling helpers
├── resume.py                # Resume protocol helpers
│
├── received_files/          # Output directory
├── progress.json            # Resume tracking
└── README.md
```

---

## 📂 File Descriptions

### 🔹 `client.py`

Implements the **sender side**:

* Splits file into chunks
* Sends packets using sliding window
* Handles ACKs and retransmissions
* Supports resume functionality
* Simulates:

  * Packet loss
  * Packet corruption

---

### 🔹 `server.py`

Implements the **receiver side**:

* Receives packets over UDP
* Buffers out-of-order packets
* Sends ACKs for each packet
* Reconstructs file in order
* Verifies integrity using SHA-256
* Saves progress for resume

---

### 🔹 `packet.py`

Defines the **core protocol format**:

* Packet creation (`create_packet`)
* Packet parsing (`parse_packet`)
* CRC32 checksum validation
* Shared by both client and server

---

### 🔹 `reliability.py`

Contains modular **Selective Repeat logic**:

* Sender-side window + timeout management
* Receiver-side buffering logic
* Used for testing and abstraction

---

### 🔹 `protocol_constants.py`

Centralized configuration:

* Chunk size
* Window size
* Timeout
* Server IP/Port

---

### 🔹 `utils.py`

Helper utilities:

* File chunking
* File size handling

---

### 🔹 `resume.py`

Handles resume protocol:

* Resume request/response parsing
* Determines restart point

---

## ▶️ How to Run

### 1. Start Server

```bash
python3 server.py
```

---

### 2. Run Client

```bash
python3 client.py
```

Enter file path when prompted.

---

## 🧪 Simulation (Important)

The client includes real network simulation:

```python
LOSS_PROB    = 0.1   # packet loss
CORRUPT_PROB = 0.05  # corruption
```

### Example Output

```text
[CLIENT] LOSS seq 45
[CLIENT] CORRUPT seq 78
[CLIENT] RETRANSMIT seq 45
```

---

## 📊 What This Demonstrates

* Reliable transmission over unreliable network
* Efficient retransmission using Selective Repeat
* Handling of:

  * Packet loss
  * Corruption
  * Out-of-order delivery
* Data integrity verification

---

## 🧠 Key Concepts Covered

* Transport Layer Protocol Design
* Sliding Window Mechanism
* Selective Repeat ARQ
* Error Detection (CRC32)
* Reliable Data Transfer
* Network Simulation

---

## 🎯 Learning Outcomes

* Built a custom reliable protocol over UDP
* Understood how TCP works internally
* Implemented real-world networking logic
* Simulated unreliable network conditions

---

## 🏁 Future Improvements

* 🌐 Multi-client support
* 📊 Live metrics dashboard
* 🔐 Encryption (TLS/AES)
* 📈 Throughput visualization

---

## 📌 Conclusion

This project successfully demonstrates how reliability can be implemented over UDP using **Selective Repeat ARQ**, making it a strong practical implementation of transport layer concepts.

---
