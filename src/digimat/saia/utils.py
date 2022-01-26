from struct import pack, unpack


def unpack_bin(binary: bytes) -> list:
    unpacked_ints = unpack(f'{len(binary)}B', binary)
    binary_strings = ['{0:b}'.format(i) for i in unpacked_ints]

    for i, b in enumerate(binary_strings):
        bools = [bool(int(char)) for char in binary_strings[i]]
        bools.reverse()
        binary_strings[i] = bools
    return binary_strings


def pack_bin(bools: list) -> bytes:
    pass


if __name__ == '__main__':
    b1 = pack('BBB', 1, 2, 3)
    print(unpack_bin(b1))
    # print(chr(255))
