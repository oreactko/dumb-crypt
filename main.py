import os
import hashlib
import random

key = b"Zo\xc6T\x95\x9a\xe7ZsC\x16-k\x1e\xdf\x9b"  # os.urandom(16)
data = "xin chào"


def init_state(key: bytes):
    s = 0xA5
    for b in key:
        s ^= b
        s = ((s << 3) | (s >> 5)) & 0xFF  # rotate
    return s


def gen_iv(key, data):
    h = hashlib.sha256(key + data).digest()
    return h[0]


def gen_sbox(key):
    seed = hashlib.sha256(key).digest()
    rng = random.Random(int.from_bytes(seed, "big"))

    sbox = list(range(256))
    rng.shuffle(sbox)

    inv = [0] * 256
    for i, v in enumerate(sbox):
        inv[v] = i

    return sbox, inv


def rotl(x, n):
    return ((x << n) | (x >> (8 - n))) & 0xFF


def round_func(x, state, sbox):
    x = sbox[x]  # 🔥 SubBytes
    x = rotl(x, 3)  # 🔥 diffusion
    x = (x * 73 + 41) & 0xFF  # 🔥 affine
    x ^= state  # 🔥 AddRoundKey (để cuối)
    return x


def rotr(x, n):
    return ((x >> n) | (x << (8 - n))) & 0xFF


def inv_round_func(x, state, inv_sbox):
    x ^= state

    inv_73 = pow(73, -1, 256)
    x = ((x - 41) * inv_73) & 0xFF

    x = rotr(x, 3)

    x = inv_sbox[x]

    return x


ROUNDS = 4
sbox, inv_sbox = gen_sbox(key)


def encode(data: bytes, key: bytes, sbox):
    state = init_state(key)
    iv = gen_iv(key, data)
    result = [iv]
    prev = iv

    for b in data:
        x = b
        for _ in range(ROUNDS):
            state = (state ^ prev) & 0xFF
            state = (state * 137 + 13) & 0xFF

            x = round_func(x, state, sbox)
        result.append(x)

        prev = x  # chaining

    return bytes(result)


def decode(encoded, key, inv_sbox):
    prev = encoded[0]
    encoded = encoded[1:]

    state = init_state(key)
    result = []

    for enc in encoded:
        x = enc

        # 🔥 lưu lại toàn bộ state của round
        states = []
        tmp_state = state

        for _ in range(ROUNDS):
            tmp_state = (tmp_state ^ prev) & 0xFF
            tmp_state = (tmp_state * 137 + 13) & 0xFF
            states.append(tmp_state)

        # 🔥 update state thật (giống encode)
        for s in states:
            state = s

        # 🔥 đảo thứ tự round
        for s in reversed(states):
            x = inv_round_func(x, s, inv_sbox)

        result.append(x)
        prev = enc

    return bytes(result)


print(key)
enc = encode(data.encode("utf-8"), key, sbox)
output = decode(enc, key=key, inv_sbox=inv_sbox)
print(enc)
print(output.decode("utf-8"))
