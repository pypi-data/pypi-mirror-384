from simple_zstd import compress, decompress


def test_session():
    content: bytes = open("uv.lock").read().encode("utf-8")

    last_compressed_size: int = -1
    for i in range(10):
        compressed: bytes = compress(content)

        assert len(compressed) < len(content)

        if i == 5:
            assert last_compressed_size > len(compressed)
        elif i > 0:
            assert last_compressed_size == len(compressed)
        last_compressed_size = len(compressed)

        assert decompress(compressed) == content
