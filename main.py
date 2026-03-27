import os

key = b"Zo\xc6T\x95\x9a\xe7ZsC\x16-k\x1e\xdf\x9b"  # os.urandom(16)
data = "xin chào"


def init_state(key: bytes):
    s = 0xA5
    for b in key:
        s ^= b
        s = ((s << 3) | (s >> 5)) & 0xFF  # rotate
    return s


def round_func(x, state):
    x ^= state  # XOR
    x = (x * 73 + 41) & 0xFF  # affine transform
    x = ((x << 3) | (x >> 5)) & 0xFF  # rotate left
    return x


def inv_round_func(x, state):
    # undo rotate left → rotate right
    x = ((x >> 3) | (x << 5)) & 0xFF

    # undo affine: x = (x - 41) * inv(73)
    inv_73 = pow(73, -1, 256)  # 🔥 nghịch đảo mod 256
    x = ((x - 41) * inv_73) & 0xFF

    # undo XOR
    x ^= state

    return x


ROUNDS = 4


def encode(data, key):
    data = data.encode("utf-8")
    state = init_state(key)
    iv = os.urandom(1)[0]
    result = [iv]
    prev = iv

    for b in data:
        x = b
        for _ in range(ROUNDS):
            state = (state ^ prev) & 0xFF
            state = (state * 137 + 13) & 0xFF

            x = round_func(x, state)
        result.append(x)

        prev = x  # chaining

    return bytes(result)


def decode(encoded, key):
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
            x = inv_round_func(x, s)

        result.append(x)
        prev = enc

    return bytes(result)


print(key)
enc = b"\xb4\xbc\xdb\x0ez^\xba\xadP\x92"
output = decode(enc, key=key)
print(enc)
print(output.decode("utf-8"))
