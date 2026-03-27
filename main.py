import os
import hashlib
import random

key = b"Zo\xc6T\x95\x9a\xe7ZsC\x16-k\x1e\xdf\x9b"  # os.urandom(16)
data = "xin chào"
ROUNDS = 32


def key_schedule(key, rounds):
    keys = []
    current = key

    for i in range(rounds):
        current = hashlib.sha256(current + bytes([i])).digest()
        keys.append(current[0])  # lấy 1 byte cho mỗi round

    return keys


def init_state(key: bytes):
    s = 0xA5
    for b in key:
        s ^= b
        s = ((s << 3) | (s >> 5)) & 0xFF  # rotate
    return s


def pad(data, block=16):
    pad_len = block - (len(data) % block)
    return data + bytes([pad_len] * pad_len)


def unpad(data):
    pad_len = data[-1]
    return data[:-pad_len]


def encrypt_block(block, key, sbox, round_keys):
    state = init_state(key)
    prev = 0

    out = []

    for b in block:
        x = b
        for i in range(ROUNDS):
            rk = round_keys[i]
            state = (state ^ prev ^ rk) & 0xFF
            state = (state * 137 + 13) & 0xFF

            x = round_func(x, state, sbox, rk)

        out.append(x)
        prev = x

    return bytes(out)


def decrypt_block(block, key, inv_sbox, round_keys):
    state = init_state(key)
    prev = 0

    out = []

    for enc in block:
        x = enc

        states = []
        tmp_state = state

        for i in range(ROUNDS):
            rk = round_keys[i]
            tmp_state = (tmp_state ^ prev ^ rk) & 0xFF
            tmp_state = (tmp_state * 137 + 13) & 0xFF
            states.append((tmp_state, rk))

        state = states[-1][0]

        for s, rk in reversed(states):
            x = inv_round_func(x, s, inv_sbox, rk)

        out.append(x)
        prev = enc

    return bytes(out)


def split_blocks(data, block=16):
    return [data[i : i + block] for i in range(0, len(data), block)]


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


def round_func(x, state, sbox, rk):
    x = sbox[x ^ rk]  # 🔥 SubBytes
    x = rotl(x, 3)  # 🔥 diffusion
    x = (x * 73 + 41) & 0xFF  # 🔥 affine
    x ^= state  # 🔥 AddRoundKey (để cuối)
    return x


def rotr(x, n):
    return ((x >> n) | (x << (8 - n))) & 0xFF


def inv_round_func(x, state, inv_sbox, rk):
    x ^= state

    inv_73 = pow(73, -1, 256)
    x = ((x - 41) * inv_73) & 0xFF

    x = rotr(x, 3)

    x = inv_sbox[x]
    x ^= rk

    return x


def encode(data, key, sbox):
    data = pad(data)

    iv = gen_iv(key, data)  # hoặc random
    prev_block = bytes([iv] * 16)

    blocks = split_blocks(data)
    round_keys = key_schedule(key, ROUNDS)

    result = [bytes([iv])]

    for block in blocks:
        # XOR với block trước
        xored = bytes([b ^ p for b, p in zip(block, prev_block)])

        enc = encrypt_block(xored, key, sbox, round_keys)

        result.append(enc)
        prev_block = enc

    return b"".join(result)


def decode(encoded, key, inv_sbox):
    iv = encoded[0]
    data = encoded[1:]

    blocks = split_blocks(data)
    prev_block = bytes([iv] * 16)

    round_keys = key_schedule(key, ROUNDS)

    result = []

    for block in blocks:
        dec = decrypt_block(block, key, inv_sbox, round_keys)

        # XOR lại
        plain = bytes([b ^ p for b, p in zip(dec, prev_block)])

        result.append(plain)
        prev_block = block

    return unpad(b"".join(result))


print(key)
sbox, inv_sbox = gen_sbox(key)
enc = encode(data.encode("utf-8"), key, sbox)
output = decode(enc, key=key, inv_sbox=inv_sbox)
print(enc)
print(output.decode("utf-8"))
