from algorithms.huffman import analyze, decode, encode
from formats.huf_file import compress, decompress


def _assert_codec_round_trip(data: bytes) -> None:
    frequencies, tree, codes = analyze(data)
    packed, bit_count = encode(data, codes)
    assert decode(packed, bit_count, tree) == data
    assert sum(frequencies.values()) == len(data)


def test_codec_common_inputs() -> None:
    for data in (b"", b"A" * 100, b"BANANA BANDANA", "Huffman 🐍".encode("utf-8")):
        _assert_codec_round_trip(data)


def test_file_round_trip_and_header_overhead() -> None:
    for data in (b"", b"x" * 100, b"abracadabra", "café 🐍".encode("utf-8")):
        packed = compress(data)
        assert decompress(packed) == data
    assert len(compress(b"short")) > len(b"short")


def test_corrupt_file_is_rejected() -> None:
    packed = bytearray(compress(b"abc"))
    packed[0] ^= 0xFF
    try:
        decompress(bytes(packed))
    except ValueError:
        pass
    else:
        raise AssertionError("Corrupt signature was accepted.")
