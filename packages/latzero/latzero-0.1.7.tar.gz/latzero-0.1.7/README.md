# latzero

**Zero-latency, zero-fuss shared memory for Python — dynamic, encrypted, and insanely fast.**

## Overview

**latzero** is a Python package designed to make inter-process communication (IPC) and shared-memory data exchange effortless. Unlike traditional shared memory systems that require fixed buffer sizes and manual serialization, latzero enables developers to:

- Create dynamic shared-memory pools accessible by multiple processes or clients
- Pass any pickleable object directly — no manual encoding/decoding
- Enable optional encryption and authentication for secure multi-process collaboration

latzero is ideal for AI workloads, distributed systems, and low-latency microservices that need real-time shared state management.

## Core Features

**Dynamic Shared Memory Pools**  
No predefined memory size. Pools expand and contract dynamically as new data arrives.

**Multi-Client Access**  
Multiple processes/clients can connect to the same pool simultaneously and share data in real time.

**Auto Cleanup**  
Data can have optional timeouts (`auto_clean=5`), automatically clearing entries after specified seconds.

**Encryption & Authentication**  
Pools can be protected with passwords. If `encryption=True`, the password becomes the encryption key.

**Data-Type Preservation**  
Stored data retains its type (`int`, `str`, `dict`, etc.) across clients.

**Self-Destructing Pools**  
Pools live only as long as one or more connected processes are active. When all disconnect, the pool is automatically destroyed.

**Pickle-Based Serialization**  
Any pickleable Python object can be stored and retrieved seamlessly.

**Event Sync** *(Coming Soon)*  
Hooks for client events like `on_connect`, `on_disconnect`, `on_update` for real-time sync logic.

## Installation

```bash
pip install latzero
```

## Quick Start

### Creating a Pool

```python
from latzero import SharedMemoryPool

pool_manager = SharedMemoryPool()
pool_manager.create(
    name="myPool",
    auth=True,
    auth_key="super_secret",
    encryption=True
)
```

### Connecting to a Pool

```python
ipc = pool_manager.connect(
    name="myPool",
    auth_key="super_secret"
)
```

### Basic Operations

```python
# Set values with optional auto-cleanup
ipc.set("key", value, auto_clean=5)

# Retrieve values
result = ipc.get("key")
```

### Type-Safe Example

```python
ipc.set("number", 42)
ipc.set("text", "yo bro")
ipc.set("data", {"a": 1, "b": 2})

print(ipc.get("number"))  # 42 (int)
print(ipc.get("text"))    # "yo bro" (str)
print(ipc.get("data"))    # {"a": 1, "b": 2} (dict)
```

## System Architecture

### Core Components

**Memory Controller**  
Manages shared memory segments dynamically.

**Pool Registry**  
Tracks all active pools via metadata.

**Encryption Layer**  
AES-GCM encryption for secure reads/writes.

**Data Layer (Pickle Serializer)**  
Automatic serialization with zlib compression.

**IPC Protocol**  
Uses `multiprocessing.shared_memory` for communication.

**Auto-Reclaim Daemon**  
Monitors idle pools and clears them when unused.

## Security Model

| Concern             | Mechanism                                                             |
|---------------------|-----------------------------------------------------------------------|
| Unauthorized access | Password-based authentication                                         |
| Data leakage        | AES-256 encryption when `encryption=True`                             |
| Data tampering      | Integrity checked using HMAC                                          |
| Memory persistence  | Pools are ephemeral; memory is released after last client disconnects |

## Performance Targets

| Metric                 | Target                             |
|------------------------|------------------------------------|
| Read latency           | < 1ms                              |
| Write latency          | < 2ms                              |
| Max concurrent clients | 128+                               |
| Memory scaling         | Dynamic up to available system RAM |
| Pool cleanup delay     | < 100ms post last disconnect       |

## Examples

Check the `examples/` directory for usage demos:

- `simple_pool.py` - Basic pool operations
- `encrypted_pool.py` - Secure pool with encryption
- `multi_client_demo.py` - Concurrent multi-client access

## Dependencies

- `multiprocessing.shared_memory`
- `cryptography` (for AES)
- `pickle`, `zlib`
- `threading`, `multiprocessing`
- `psutil` (for process detection)

## Roadmap

**Phase 1:** Core shared memory pools + pickle serialization  
**Phase 2:** Auth + encryption  
**Phase 3:** Dynamic memory expansion + auto-clean  
**Phase 4:** Performance optimization + PyPI release  
**Phase 5:** Real-time event hooks, WebSocket bridges

## Use Cases

- AI agents sharing memory
- Game servers syncing states
- Local caching for microservices
- High-speed analytics pipelines
- Multi-agent orchestration systems

## About

latzero makes shared-memory IPC as easy as Redis, without the network overhead. Fast, simple, encrypted, ephemeral — a zero-latency memory layer for Python developers.

**Created by BRAHMAI**  
https://brahmai.in