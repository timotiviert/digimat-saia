from struct import pack, unpack


def unpack_bin(binary: bytes):
    unpacked_ints = unpack(f'{len(binary)}B', binary)
    binary_strings = ['{0:b}'.format(i) for i in unpacked_ints]
    for i, b in enumerate(binary_strings):
        binary_strings[i] = [bool(int(char)) for char in binary_strings[i]]
    return binary_strings


if __name__ == '__main__':
    b1 = pack('BBB', 1, 2, 3)
    print(unpack_bin(b1))
    # print(chr(255))
