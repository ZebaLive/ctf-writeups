#!/usr/bin/env python3
import struct
import matplotlib.pyplot as plt

# Read the mouse data
with open("/tmp/mouse_data.txt", "r") as f:
    lines = f.readlines()

# Parse mouse movements
x, y = 0, 0
positions = []
button_states = []

for line in lines:
    line = line.strip()
    if not line or len(line) < 14:  # Need at least 7 bytes (14 hex chars)
        continue

    # Parse hex data
    try:
        data = bytes.fromhex(line)

        # HID mouse report format:
        # Byte 0: Buttons (bit 0 = left button, bit 1 = right button, etc.)
        # Bytes 1-2: X movement (signed 16-bit little-endian)
        # Bytes 3-4: Y movement (signed 16-bit little-endian)
        # Bytes 5-6: Wheel or other data

        buttons = data[0]

        # Extract X and Y as signed 16-bit integers (little-endian)
        x_delta = struct.unpack("<h", data[1:3])[0]
        y_delta = struct.unpack("<h", data[3:5])[0]

        # Update position
        x += x_delta
        y += y_delta

        positions.append((x, y, buttons))
        button_states.append(buttons)

    except Exception as e:
        print(f"Error parsing line: {line} - {e}")
        continue

print(f"Total positions: {len(positions)}")
print(f"X range: {min(p[0] for p in positions)} to {max(p[0] for p in positions)}")
print(f"Y range: {min(p[1] for p in positions)} to {max(p[1] for p in positions)}")

# Visualize the mouse movements
# We want to draw lines when the left button is pressed (button bit 0 = 1)
fig, ax = plt.subplots(figsize=(20, 10))

# Draw all movements
for i in range(len(positions) - 1):
    x1, y1, btn1 = positions[i]
    x2, y2, btn2 = positions[i + 1]

    # If left button is pressed, draw a line
    if btn1 & 0x01:  # Left button pressed
        ax.plot([x1, x2], [y1, y2], "b-", linewidth=2)

# Invert Y axis (since screen coordinates usually have Y increasing downward)
ax.invert_yaxis()
# Don't use equal aspect ratio to allow Y axis to stretch
ax.set_title("Mouse Drawing - Blue Mouse CTF Challenge", fontsize=16)
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(
    "/home/zeba/ECSC/blue-mouse/mouse_drawing.png", dpi=200, bbox_inches="tight"
)
print("Drawing saved to mouse_drawing.png")
# plt.show()  # Comment out to avoid blocking
