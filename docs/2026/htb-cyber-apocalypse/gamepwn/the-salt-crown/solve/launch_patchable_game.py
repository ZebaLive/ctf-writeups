#!/usr/bin/env python3
import os
import signal
import subprocess
import struct
import time


INITIAL_STATE = struct.pack(
    "<13I",
    0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 4, 0x1388,
)

SOLVED_STATE_PREFIX = struct.pack(
    "<20I",
    1, 1, 1, 1, 1, 1, 1, 1, 0, 1,
    1, 0, 0x1388, 1, 1, 1, 1, 1, 1, 0,
)

FINAL_STATE_PREFIX = struct.pack(
    "<20I",
    1, 1, 1, 1, 1, 1, 1, 1, 0, 0,
    1, 0, 0x1388, 1, 1, 1, 1, 1, 1, 1,
)

EVENT_RECORDS = bytes.fromhex(
    "19 01 01 00 01 00 00 00"
    "2d 02 03 00 00 00 00 00"
    "43 03 07 00 00 00 00 00"
    "58 04 0f 00 00 00 00 00"
    "6e 05 1f 00 00 00 00 00"
    "81 06 3f 00 00 00 00 00"
    "b7 07 7f 00 00 00 00 00"
)

TRANSCRIPT_DIGEST = bytes.fromhex(
    "58c1fd695c617b299de3cf4608fcc910e581b0334ff8ddc9726623862c427386"
)

REWARD_RENDER_STATE = (
    TRANSCRIPT_DIGEST
    + struct.pack("<QIIHBBI", 0, 0x2D, 0x3D, 0, 0, 0, 1)
)

POST_FINAL_GUARD = bytes.fromhex(
    "83 79 48 00 74 1a 45 33 c0 b8 03 00 00 00"
    "81 fa c4 72 00 00 44 0f 44 c0 41 8b c0 48 83 c4 28 c3"
)
POST_FINAL_GUARD_PATCH = bytes.fromhex("41 89 c0 90")


def maps(pid, required="rw"):
    with open(f"/proc/{pid}/maps", "r", errors="ignore") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) >= 5 and all(flag in parts[1] for flag in required):
                start, end = [int(value, 16) for value in parts[0].split("-")]
                if end - start <= 512 * 1024 * 1024:
                    yield start, end, parts[5] if len(parts) > 5 else ""


def patch_state(pid):
    patched = []
    with open(f"/proc/{pid}/mem", "r+b", 0) as mem:
        for start, end, path in maps(pid, "rx"):
            try:
                mem.seek(start)
                data = mem.read(end - start)
            except Exception:
                continue
            offset = data.find(POST_FINAL_GUARD)
            if offset != -1:
                address = start + offset + 20
                mem.seek(address)
                mem.write(POST_FINAL_GUARD_PATCH)
                patched.append((address, path))
        for start, end, path in maps(pid):
            try:
                mem.seek(start)
                data = mem.read(end - start)
            except Exception:
                continue
            for needle in (INITIAL_STATE, SOLVED_STATE_PREFIX):
                offset = data.find(needle)
                while offset != -1:
                    address = start + offset
                    mem.seek(address)
                    mem.write(FINAL_STATE_PREFIX)
                    mem.seek(address + 0x50)
                    mem.write(EVENT_RECORDS)
                    mem.seek(address + 0xB0)
                    mem.write(struct.pack("<Q", 7))
                    mem.seek(address + 0xB8)
                    mem.write(REWARD_RENDER_STATE)
                    patched.append((address, path))
                    offset = data.find(needle, offset + 4)
    return patched


def main():
    env = os.environ.copy()
    env["WINEDEBUG"] = "-all"
    cmd = ["wine", "The Salt Crown.exe", "--rendering-driver", "opengl3", "--audio-driver", "Dummy", "--verbose"]
    proc = subprocess.Popen(cmd, cwd=os.getcwd(), env=env)
    pid_file = "patchable_game.pid"
    with open(pid_file, "w") as handle:
        handle.write(str(proc.pid))
    print(f"spawned {proc.pid}; pid written to {pid_file}", flush=True)
    print("Play in the Wine window. Create patch_now to patch, or stop_now to quit.", flush=True)
    try:
        while proc.poll() is None:
            if os.path.exists("patch_now"):
                os.unlink("patch_now")
                patched = patch_state(proc.pid)
                print(f"patched {len(patched)} candidate state blocks", flush=True)
                for address, path in patched[:20]:
                    print(f"{address:#x} {path}", flush=True)
            if os.path.exists("stop_now"):
                os.unlink("stop_now")
                proc.terminate()
                break
            time.sleep(0.25)
    finally:
        try:
            os.unlink(pid_file)
        except FileNotFoundError:
            pass
        if proc.poll() is None:
            proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()