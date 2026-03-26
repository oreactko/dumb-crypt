import random
import os

random.seed(os.urandom(2))
key = [int.from_bytes(os.urandom(16), "big") for _ in range(16)]
data = "xin chào"


def encode(data, key):
    encode_arrays = []
    prev = 0
    for idx, char in enumerate(data):
        k = (key[idx % len(key)] ^ prev) & 0xFFFF
        enc = ord(char) ^ prev ^ k
        prev = enc & 0xFFFF  # giữ 16-bit
        encode_arrays.append(enc)
    return encode_arrays


def decode(encoded, key):
    result = []
    prev = 0
    for idx, enc in enumerate(encoded):
        k = (key[idx % len(key)] ^ prev) & 0xFFFF
        # đảo ngược encode
        x = enc ^ prev ^ k
        char = chr(x)
        result.append(char)
        # phải giống encode
        prev = enc & 0xFFFF

    return "".join(result)


print(key)
enc = encode(data, key=key)
output = decode(enc, key=key)
print(enc)
print(output)
