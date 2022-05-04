import os as _os
import struct as _struct


def find_file(basefile, findfile):
    """Find a file named `findfile` in the same path and with the same extension as `basefile`."""
    basepath = _os.path.split(basefile)[0]
    ext = _os.path.splitext(basefile)[1]
    return _os.path.join(basepath, findfile + ext)


def get_ubyte(data, offset: int = 0) -> int:
    """Returns an unsigned byte."""
    return _struct.unpack('B', data[offset])[0]


def get_uint16(data, offset: int = 0) -> int:
    """Reads an unsigned short."""
    return _struct.unpack('<H', data[offset:offset+2])[0]


def get_uint16_array(data, offset: int = 0, count: int = 0):
    """Reads an array of unsigned shorts."""
    if count <= 0:
        count = (len(data) - offset) // 2
    return _struct.unpack(f'<{count}H', data[offset:offset+count*2])


def get_uint32(data, offset: int = 0) -> int:
    """Reads an unsigned int."""
    return _struct.unpack('<I', data[offset:offset+4])[0]


def get_uint32_array(data, offset: int = 0, count: int = 0):
    """Reads an array of unsigned ints."""
    if count <= 0:
        count = len(data) // 4
    return _struct.unpack(f'<{count}I', data[offset:offset+count*4])


def get_text(data, offset: int = 0, length: int = -1, strip_nulls: bool = True) -> bytes:
    if length < 0:
        length = len(data) - offset
    result = data[offset:offset+length]
    if strip_nulls:
        result = result.strip(b'\x00')
    return result


def nonzero(items):
    return [index for (index, item) in enumerate(items) if item != 0]


class BytesReader:
    def __init__(self, data):
        self.__pos = 0
        self.__data = data

    def __len__(self):
        return len(self.__data)

    def read(self, n: int = -1):
        if n < 0:
            result = self.__data[self.__pos:]
            self.__pos = len(self.__data)
        elif n == 1:
            result = self.__data[self.__pos]
            self.__pos += n
        else:
            result = self.__data[self.__pos:self.__pos+n]
            self.__pos += n
        return result

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence == 0:
            self.__pos = offset
        elif whence == 1:
            self.__pos += offset
        elif whence == 2:
            self.__pos = len(self.__data) - offset
        else:
            raise ValueError(f"Invalue value for whence: {whence}")
        return self.__pos

    def tell(self) -> int:
        return self.__pos

    def read_ubyte(self) -> int:
        """Reads an unsigned byte."""
        result = get_ubyte(self.__data, self.__pos)
        self.__pos += 1
        return result

    def read_uint16(self) -> int:
        """Reads an unsigned short."""
        result = get_uint16(self.__data, self.__pos)
        self.__pos += 2
        return result

    def read_uint16_array(self, count: int = 0):
        """Reads an array of unsigned shorts."""
        result = get_uint16_array(self.__data, self.__pos, count)
        self.__pos += 2 * len(result)
        return result

    def read_uint32(self) -> int:
        """Reads an unsigned int."""
        result = get_uint32(self.__data, self.__pos)
        self.__pos += 4
        return result

    def read_uint32_array(self, count: int = 0):
        """Reads an array of unsigned ints."""
        result = get_uint32_array(self.__data, self.__pos, count)
        self.__pos += 4 * len(result)
        return result

    def read_text(self, length: int, strip_nulls: bool = True) -> bytes:
        result = get_text(self.__data, self.__pos, length, strip_nulls=strip_nulls)
        self.__pos += length
        return result


class BinaryFileReader:
    def __init__(self, file):
        self.__f = open(file, "rb")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read(self, n: int = -1) -> bytes:
        return self.__f.read(n)

    def seek(self, offset: int, whence: int = 0) -> int:
        return self.__f.seek(offset, whence)

    def tell(self) -> int:
        return self.__f.tell()

    def close(self):
        self.__f.close()

    def read_ubyte(self) -> int:
        """Reads an unsigned byte."""
        return get_ubyte(self.read(1))

    def read_uint16(self) -> int:
        """Reads an unsigned short."""
        return get_uint16(self.__f.read(2))

    def read_uint16_array(self, count: int = 0):
        """Reads an array of unsigned shorts."""
        data = self.__f.read(2 * count) if count > 0 else self.__f.read()
        return get_uint16_array(data, 0, count)

    def read_uint32(self) -> int:
        """Reads an unsigned int."""
        return get_uint32(self.__f.read(4))

    def read_uint32_array(self, count: int = 0):
        """Reads an array of unsigned ints."""
        data = self.__f.read(4 * count) if count > 0 else self.__f.read()
        return get_uint32_array(data, 0, count)

    def read_text(self, length: int, strip_nulls: bool = True) -> bytes:
        return get_text(self.__f.read(length), strip_nulls=strip_nulls)
