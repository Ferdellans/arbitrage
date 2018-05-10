import zlib


def inflate(data):
    decompress = zlib.decompressobj(-zlib.MAX_WBITS)
    inflated = decompress.decompress(data)
    inflated += decompress.flush()
    return inflated


def deflate(data):
    compress = zlib.compressobj(-zlib.MAX_WBITS)
    deflated = compress.compress(data)
    deflated += compress.flush()
    return deflated
