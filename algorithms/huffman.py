from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import heapq
from itertools import count


@dataclass(frozen=True)
class Node:
    frequency: int
    symbol: int | None = None
    left: Node | None = None
    right: Node | None = None

    @property
    def is_leaf(self) -> bool:
        return self.symbol is not None


def build_tree(frequencies: dict[int, int]) -> Node | None:
    """Build a deterministic Huffman tree from byte frequencies."""
    queue: list[tuple[int, int, Node]] = []
    sequence = count()
    for symbol, frequency in sorted(frequencies.items()):
        if not 0 <= symbol <= 255 or frequency <= 0:
            raise ValueError("Frequencies must map bytes to positive counts.")
        heapq.heappush(queue, (frequency, next(sequence), Node(frequency, symbol)))

    while len(queue) > 1:
        left = heapq.heappop(queue)[2]
        right = heapq.heappop(queue)[2]
        parent = Node(left.frequency + right.frequency, left=left, right=right)
        heapq.heappush(queue, (parent.frequency, next(sequence), parent))
    return heapq.heappop(queue)[2] if queue else None


def build_codes(tree: Node | None) -> dict[int, str]:
    if tree is None:
        return {}
    codes: dict[int, str] = {}

    def visit(node: Node, prefix: str) -> None:
        if node.is_leaf:
            assert node.symbol is not None
            codes[node.symbol] = prefix or "0"
            return
        assert node.left is not None and node.right is not None
        visit(node.left, prefix + "0")
        visit(node.right, prefix + "1")

    visit(tree, "")
    return codes


def encode(data: bytes, codes: dict[int, str]) -> tuple[bytes, int]:
    bit_count = sum(len(codes[byte]) for byte in data)
    packed = bytearray((bit_count + 7) // 8)
    position = 0
    for byte in data:
        try:
            code = codes[byte]
        except KeyError as error:
            raise ValueError(f"No Huffman code for byte {byte}.") from error
        for bit in code:
            if bit == "1":
                packed[position // 8] |= 1 << (7 - position % 8)
            position += 1
    return bytes(packed), bit_count


def decode(payload: bytes, bit_count: int, tree: Node | None) -> bytes:
    if bit_count < 0 or bit_count > len(payload) * 8:
        raise ValueError("Invalid meaningful bit count.")
    if len(payload) != (bit_count + 7) // 8:
        raise ValueError("Payload length does not match the meaningful bit count.")
    if tree is None:
        if bit_count or payload:
            raise ValueError("An empty tree cannot decode a non-empty payload.")
        return b""
    if tree.is_leaf:
        assert tree.symbol is not None
        if any((payload[index // 8] >> (7 - index % 8)) & 1 for index in range(bit_count)):
            raise ValueError("Invalid bit in single-symbol payload.")
        return bytes([tree.symbol]) * bit_count

    output = bytearray()
    node = tree
    for position in range(bit_count):
        bit = (payload[position // 8] >> (7 - position % 8)) & 1
        node = node.right if bit else node.left  # type: ignore[assignment]
        if node is None:
            raise ValueError("Payload does not match the Huffman tree.")
        if node.is_leaf:
            assert node.symbol is not None
            output.append(node.symbol)
            node = tree
    if node is not tree:
        raise ValueError("Payload ends in the middle of a Huffman code.")
    return bytes(output)


def analyze(data: bytes) -> tuple[dict[int, int], Node | None, dict[int, str]]:
    frequencies = dict(Counter(data))
    tree = build_tree(frequencies)
    return frequencies, tree, build_codes(tree)
