# openECSC 2025

## Challenge: Calamansi

## Tags: stego

## Difficulty: Medium

## Table of Contents

- [Solution Overview](#solution-overview)
- [Tools Used](#tools-used)
- [Solution](#solution)
- [Solution Scripts](#solution-scripts)
- [Flag](#flag)

### Solution Overview

The provided [`calamansi.png`](./calamansi.png) appears to be a simple flat calamansi-yellow square, but it's actually an APNG (animated PNG) with 50 hidden frames. Each frame contains letter-shaped differences in the RGB channels that are invisible due to transparent alpha channels. By parsing the PNG chunk structure, extracting and decompressing each frame's raw pixel data, converting non-background pixels to white, and concatenating the resulting character images, the complete flag is revealed as a horizontal strip.

### Tools Used

- Python 3 standard library (`struct`, `zlib`, `itertools`)
- Pillow (PIL) for image processing and manipulation
- `file` command for initial format verification

### Solution

When I first looked at this challenge, I was immediately suspicious. **The image looked like a simple flat yellow square, but the file size was 22 KB.**

**First thought**: *"Why would a solid color square be 22 KB? That's way too big for what should be a tiny PNG."*

#### Initial Investigation

I ran a quick check on the file format:

```bash
file calamansi.png
# calamansi.png: PNG image data, 200 x 100, 8-bit/color RGBA, non-interlaced
```

Hmm, that didn't show anything special. But then I tried:

```bash
identify calamansi.png
# calamansi.png PNG 200x100 200x100+0+0 8-bit sRGB 22.1KB 0.000u 0:00.000
```

Still no indication of animation. But that file size kept bothering me. Let me try a more detailed check:

```bash  
pngcheck -v calamansi.png
```

**BINGO!** The verbose output revealed something crucial:
- The PNG had `fcTL` (frame control) and `fdAT` (frame data) chunks
- These are **APNG chunks** - this was an animated PNG!
- There were 50 animation frames hidden in the file

**Key insight**: *"The file is an APNG with 50 frames. Each frame might contain part of the flag, but why can't I see the animation?"*

#### Understanding the APNG Structure

I decided to parse the PNG manually to understand its structure. APNGs work by having:
- An `IDAT` chunk for the default/first frame
- `fcTL` chunks that control frame timing/blending  
- `fdAT` chunks containing the actual frame data

My approach became: extract every `fdAT` chunk, decompress the frame data, and see what's actually in each frame.

```python
import struct, zlib
from pathlib import Path
from PIL import Image

PNG_SIG = b"\x89PNG\r\n\x1a\n"
BG = (252, 255, 164)  # The calamansi yellow background

with open("calamansi.png", "rb") as f:
    assert f.read(8) == PNG_SIG
    width = height = None
    frames = []
    
    while True:
        header = f.read(8)
        if not header:
            break
        length, chunk_type = struct.unpack(">I4s", header)
        payload = f.read(length)
        f.read(4)  # Skip CRC
        
        if chunk_type == b"IHDR":
            width, height, *_ = struct.unpack(">IIBBBBB", payload)
            print(f"Image dimensions: {width}x{height}")
        elif chunk_type == b"fdAT":
            # fdAT format: [4 bytes sequence] [compressed data]
            frames.append(zlib.decompress(payload[4:]))
            
print(f"Found {len(frames)} animation frames")
```

**Result**: 50 frames extracted! But when I looked at the first few frames, I noticed something strange.

#### The Hidden Characters

Each decompressed frame contained raw RGBA pixel data. The PNG format stores pixels row by row, with each row having a filter byte followed by the actual pixel data.

**The revelation came when I examined the pixel values**:

```python
stride = 1 + width * 4  # Filter byte + RGBA pixels
for i, raw in enumerate(frames[:3], start=1):
    print(f"\nFrame {i}:")
    different_pixels = 0
    
    for y in range(height):
        line = raw[y * stride : (y + 1) * stride]
        assert line[0] == 0  # Filter type 0 (no filtering)
        row = line[1:]
        
        for x in range(width):
            r, g, b, a = row[x * 4 : x * 4 + 4]
            if (r, g, b) != BG:  # Not background color
                different_pixels += 1
                if different_pixels <= 5:  # Show first few
                    print(f"  Pixel at ({x},{y}): RGB=({r},{g},{b}), Alpha={a}")
                    
    print(f"  Total non-background pixels: {different_pixels}")
```

**The breakthrough**: 
- Most pixels were the background color (252, 255, 164) 
- But some pixels had different RGB values (usually white: 255, 255, 255)
- **However, ALL pixels had alpha = 0** (completely transparent)!
- The different RGB pixels formed letter-like shapes

**This explained everything!** The animation frames contained letters, but they were invisible because the alpha channel made them transparent.

#### Revealing the Characters

*"If the frames contain letter-shaped RGB differences but they're invisible due to alpha, I just need to make them visible by ignoring the alpha channel."*

My solution: For each frame, convert every non-background pixel to white (255) and every background pixel to black (0), creating a binary image that reveals the hidden character.

```python
for i, raw in enumerate(frames, start=1):
    out = Image.new("L", (width, height), 0)  # Grayscale image, black background
    pixels = out.load()
    
    for y in range(height):
        line = raw[y * stride : (y + 1) * stride]
        row = line[1:]  # Skip filter byte
        
        for x in range(width):
            r, g, b, a = row[x * 4 : x * 4 + 4]
            if (r, g, b) != BG:  # Non-background pixel
                pixels[x, y] = 255  # Make it white
            # Background pixels stay black (0)
                
    out.save(f"revealed_{i:02d}.png")
```

**Success!** Each `revealed_XX.png` file now showed a single character clearly visible as white text on a black background.

#### Assembling the Flag

After extracting all 50 character images, I needed to combine them into the final flag. 

**The final insight**: *"The characters are already in the right order - the frame numbers correspond to the flag character positions."*

I concatenated all the revealed character images horizontally:

```python
def stitch_frames():
    frames = []
    for i in range(1, 51):  # 50 frames
        img = Image.open(f"revealed_{i:02d}.png").convert("L")
        frames.append(img)
    
    # Calculate total width
    total_width = sum(frame.width for frame in frames)
    max_height = max(frame.height for frame in frames)
    
    # Create canvas and paste each frame
    canvas = Image.new("L", (total_width, max_height), 0)
    x_offset = 0
    
    for frame in frames:
        canvas.paste(frame, (x_offset, 0))
        x_offset += frame.width
        
    canvas.save("flag.png")
```

Opening `flag.png` revealed the complete flag as a horizontal strip of 50 characters!

![flag](./flag.png)

### Solution Scripts

**Extract and reveal characters per frame**:

```python
import struct, zlib
from pathlib import Path
from PIL import Image

PNG_SIG = b"\x89PNG\r\n\x1a\n"
BG = (252, 255, 164)

with open("calamansi.png", "rb") as f:
    assert f.read(8) == PNG_SIG
    width = height = None
    frames = []
    while True:
        header = f.read(8)
        if not header:
            break
        length, chunk_type = struct.unpack(">I4s", header)
        payload = f.read(length)
        f.read(4)  # CRC
        if chunk_type == b"IHDR":
            width, height, *_ = struct.unpack(">IIBBBBB", payload)
        elif chunk_type == b"fdAT":
            frames.append(zlib.decompress(payload[4:]))

Path(".").mkdir(exist_ok=True)
stride = 1 + width * 4
for i, raw in enumerate(frames, start=1):
    out = Image.new("L", (width, height), 0)
    pixels = out.load()
    for y in range(height):
        line = raw[y * stride : (y + 1) * stride]
        assert line[0] == 0  # filter type 0
        row = line[1:]
        for x in range(width):
            r, g, b, a = row[x * 4 : x * 4 + 4]
            if (r, g, b) != BG:
                pixels[x, y] = 255
    out.save(f"revealed_{i:02d}.png")
```

**Concatenate revealed frames**:

```python
#!/usr/bin/env python3
import glob
import os
import re
from typing import List, Tuple
from PIL import Image

Frame = Tuple[int, Image.Image, str]

def load_frames(pattern: str = "revealed_*.png") -> List[Frame]:
    frames: List[Frame] = []
    for path in sorted(glob.glob(pattern)):
        match = re.search(r"(\d+)", os.path.basename(path))
        idx = int(match.group(1)) if match else -1
        frames.append((idx, Image.open(path).convert("L"), path))
    frames.sort(key=lambda item: item[0])
    return frames

def stitch(frames: List[Frame]) -> Image.Image:
    total_width = sum(frame.width for _, frame, _ in frames)
    max_height = max(frame.height for _, frame, _ in frames)
    canvas = Image.new("L", (total_width, max_height), 0)
    x = 0
    for _, image, _ in frames:
        canvas.paste(image, (x, 0))
        x += image.width
    return canvas

def main() -> None:
    frames = load_frames()
    order = " ".join(os.path.basename(path) for _, _, path in frames)
    print("Using frames in left-to-right order:\n", order)
    stitched = stitch(frames)
    stitched.save("flag.png")

if __name__ == "__main__":
    main()
```

Running these two scripts produces `flag.png`, a 50-character strip that spells out the answer.

### Flag

**`openECSC{B3f0r3-1t-w45-Y3ll0w-n0w-1t5-c4l4m4n51}`**