from __future__ import annotations

from collections import Counter
import struct

from algorithms.huffman import analyze, build_tree, decode, encode


MAGIC = b"HUF1"
_HEADER = struct.Struct(">4sQQH")
_ENTRY = struct.Struct(">BQ")
_MAX_ORIGINAL_SIZE = (1 << 64) - 1


def compress(data: bytes) -> bytes:
    if len(data) > _MAX_ORIGINAL_SIZE:
        raise ValueError("Input is too large for the HUF format.")
    frequencies, tree, codes = analyze(data)
    payload, bit_count = encode(data, codes)
    if bit_count > _MAX_ORIGINAL_SIZE:
        raise ValueError("Encoded input is too large for the HUF format.")
    result = bytearray(_HEADER.pack(MAGIC, len(data), bit_count, len(frequencies)))
    for symbol, frequency in sorted(frequencies.items()):
        result.extend(_ENTRY.pack(symbol, frequency))
    result.extend(payload)
    return bytes(result)


def decompress(compressed: bytes) -> bytes:
    if len(compressed) < _HEADER.size:
        raise ValueError("File is too short to contain a HUF header.")
    magic, original_size, bit_count, symbol_count = _HEADER.unpack_from(compressed)
    if magic != MAGIC:
        raise ValueError("Not a supported HUF file.")
    if symbol_count > 256:
        raise ValueError("Invalid symbol count in HUF header.")
    table_end = _HEADER.size + symbol_count * _ENTRY.size
    if table_end > len(compressed):
        raise ValueError("Truncated frequency table in HUF header.")

    frequencies: dict[int, int] = {}
    for offset in range(_HEADER.size, table_end, _ENTRY.size):
        symbol, frequency = _ENTRY.unpack_from(compressed, offset)
        if symbol in frequencies or frequency == 0:
            raise ValueError("Invalid frequency table in HUF header.")
        frequencies[symbol] = frequency
    if sum(frequencies.values()) != original_size:
        raise ValueError("Frequency table does not match the original size.")
    if bool(original_size) != bool(symbol_count):
        raise ValueError("Empty input must have an empty frequency table.")

    payload = compressed[table_end:]
    tree = build_tree(frequencies)
    decoded = decode(payload, bit_count, tree)
    if len(decoded) != original_size or Counter(decoded) != Counter(frequencies):
        raise ValueError("Decoded data does not match the HUF header.")
    return decoded
