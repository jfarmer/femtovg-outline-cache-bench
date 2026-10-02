"""Shared standard-library helpers for the paired Alustin font benchmark."""

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib

def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def file_info(path):
    path = Path(path).resolve(strict=True)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}


def git_head(root):
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()


def event_map(sample):
    return {event["event"]: event for event in sample["events"]}


def frame_spans(spans, marker):
    markers = [span for span in spans if span["name"] == marker]
    if len(markers) != 1:
        raise ValueError(f"expected one {marker} span, found {len(markers)}")
    at = markers[0]["start_ns"]
    frames = [span for span in spans if span["name"] == "femtovg.render"
              and span["start_ns"] <= at <= span["start_ns"] + span["duration_ns"]]
    if len(frames) != 1:
        raise ValueError(f"expected one rendered frame containing {marker}, found {len(frames)}")
    frame = frames[0]
    lo, hi = frame["start_ns"], frame["start_ns"] + frame["duration_ns"]
    totals = {}
    for span in spans:
        name = span["name"]
        if (name.startswith("femtovg.") and lo <= span["start_ns"]
                and span["start_ns"] + span["duration_ns"] <= hi):
            row = totals.setdefault(name, {"ms": 0.0, "calls": 0})
            value = span["amount"] if name.endswith("thread_cpu_ns") else span["duration_ns"]
            row["ms"] += value / 1_000_000
            row["calls"] += 1
    if "femtovg.render.thread_cpu_ns" not in totals:
        raise ValueError(f"missing renderer thread-CPU measurement in {marker}")
    return totals


def png_rgba(path):
    """Decode non-interlaced RGB/RGBA8 PNGs for exact screenshot pixel parity."""
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not PNG: {path}")
    pos, compressed = 8, []
    width = height = depth = color = interlace = None
    while pos < len(data):
        length = struct.unpack_from(">I", data, pos)[0]
        kind = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        crc = struct.unpack_from(">I", data, pos + 8 + length)[0]
        if zlib.crc32(kind + chunk) != crc:
            raise ValueError(f"PNG CRC mismatch: {path}")
        pos += 12 + length
        if kind == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", chunk)
            if (depth, color, compression, filtering, interlace) not in ((8, 2, 0, 0, 0), (8, 6, 0, 0, 0)):
                raise ValueError(f"unsupported PNG format {(depth, color, interlace)}")
        elif kind == b"IDAT":
            compressed.append(chunk)
        elif kind == b"IEND":
            break
    if width is None:
        raise ValueError("PNG has no dimensions")
    bpp = 4 if color == 6 else 3
    stride = width * bpp
    raw = zlib.decompress(b"".join(compressed))
    if len(raw) != height * (stride + 1):
        raise ValueError("PNG decoded size mismatch")
    previous, rows = bytearray(stride), bytearray()
    for y in range(height):
        offset = y * (stride + 1)
        filt = raw[offset]
        row = bytearray(raw[offset + 1:offset + 1 + stride])
        if filt not in range(5):
            raise ValueError(f"unsupported PNG filter {filt}")
        for x in range(stride):
            left = row[x - bpp] if x >= bpp else 0
            up = previous[x]
            upper_left = previous[x - bpp] if x >= bpp else 0
            if filt == 1:
                prediction = left
            elif filt == 2:
                prediction = up
            elif filt == 3:
                prediction = (left + up) // 2
            elif filt == 4:
                p = left + up - upper_left
                distances = (abs(p - left), abs(p - up), abs(p - upper_left))
                prediction = (left, up, upper_left)[distances.index(min(distances))]
            else:
                prediction = 0
            row[x] = (row[x] + prediction) & 255
        rows.extend(row)
        previous = row
    if color == 2:
        rgba = bytearray(width * height * 4)
        rgba[0::4], rgba[1::4], rgba[2::4], rgba[3::4] = rows[0::3], rows[1::3], rows[2::3], b"\xff" * (width * height)
        rows = rgba
    return width, height, bytes(rows)


