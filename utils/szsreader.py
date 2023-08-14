import struct
import wszst_yaz0
from attr import dataclass


BYTEORDER = 'big'
BYTEORDER_FCHAR = '>'


def decompress(file) -> bytes:
    return wszst_yaz0.decompress(file.read())


def extract_file(path: str, filename: str):
    with open(path, 'rb') as f:
        data = decompress(f)

    header = U8Header.parse(data[0:])
    if header.magic != 0x55AA382D:
        raise ValueError('File not recognized as U8 archive')

    root = U8Node.parse(data[header.first_offset:])
    strings_offset = header.first_offset + root.end * U8Node.length()

    for i in range(1, root.end):
        offset = header.first_offset + i * U8Node.length()
        node = U8Node.parse(data[offset:])
        if not node.is_directory:
            name_offset = node.name_offset + strings_offset
            name = _parse_c_string(data[name_offset:])
            if name == filename:
                return data[node.start:(node.start + node.end)]


def extract_file_to(srcpath: str, dstpath: str, filename: str):
    data = extract_file(srcpath, filename)
    with open(dstpath, 'wb') as f:
        f.write(data)


@dataclass
class U8Header:
    _FORMAT = BYTEORDER_FCHAR + 'I3i16x'

    magic: int
    first_offset: int
    size: int
    file_offset: int

    @classmethod
    def length(cls):
        return struct.calcsize(cls._FORMAT)

    @classmethod
    def parse(cls, data: bytes):
        tp = struct.unpack(cls._FORMAT, data[:cls.length()])
        return U8Header(*tp)


@dataclass
class U8Node:
    _FORMAT = BYTEORDER_FCHAR + '?3sII'

    is_directory: bool
    name_offset: int
    start: int
    end: int

    @classmethod
    def length(cls):
        return struct.calcsize(cls._FORMAT)

    @classmethod
    def parse(cls, data: bytes):
        ls = list(struct.unpack(cls._FORMAT, data[:cls.length()]))
        ls[1] = int.from_bytes(ls[1], byteorder='big', signed=False)
        return U8Node(*ls)


def _parse_c_string(data: bytes) -> str:
    for i, b in enumerate(data):
        if b == 0:
            return str(data[:i], 'ascii')
    raise TypeError('C string missing null terminator')
