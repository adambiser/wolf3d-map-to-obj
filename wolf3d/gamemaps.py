from dataclasses import dataclass
import typing as _typing
from .utils import *

__all__ = ["GameMaps", "GameMap"]


@dataclass
class MapHead:
    rlew_tag: int
    offsets: _typing.List[int]


@dataclass
class MapInfo:
    plane_start: _typing.List[int]
    plane_length: _typing.List[int]
    width: int
    height: int
    name: bytes


@dataclass
class GameMap:
    name: bytes
    width: int
    height: int
    planes: int
    tiles: list[list[list[int]]]  # plane,y,x


class GameMaps:
    NEARTAG = 0xa7
    FARTAG = 0xa8
    MAPPLANES = 3
    NAME_LENGTH = 16
    CARMACIZED = True
    MAPHEAD_NAME = "MAPHEAD"

    def __init__(self, file):
        self.file = file
        self.header = self.load_map_head()
        self.f = BinaryFileReader(file)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.f.close()

    def load_map_head(self):
        header_file = find_file(self.file, self.MAPHEAD_NAME)
        with BinaryFileReader(header_file) as f:
            rlew_tag = f.read_uint16()
            header_offsets = list(f.read_uint32_array())
        # Remove any sparse maps from the end of the list.
        first_sparse_map_index = max(nonzero(header_offsets)) + 1
        del header_offsets[first_sparse_map_index:]
        return MapHead(rlew_tag, header_offsets)

    def load_map_info(self, index: int):
        self.f.seek(self.header.offsets[index])
        planestart = self.f.read_uint32_array(self.MAPPLANES)
        planelength = self.f.read_uint16_array(self.MAPPLANES)
        width, height = self.f.read_uint16_array(2)
        name = self.f.read_text(self.NAME_LENGTH)
        return MapInfo(planestart, planelength, width, height, name)

    def load_map(self, index: int):
        info = self.load_map_info(index)
        data = []
        for plane in range(self.MAPPLANES):
            self.f.seek(info.plane_start[plane])
            plane_data = self.f.read(info.plane_length[plane])
            if self.CARMACIZED:
                plane_data = self.carmack_expand(plane_data)
            plane_data = self.rlew_expand(plane_data)
            plane_data = [plane_data[y * info.width:(y + 1) * info.width] for y in range(info.height)]
            data.append(plane_data)
        return GameMap(info.name, info.width, info.height, self.MAPPLANES, data)

    def carmack_expand(self, source: bytes) -> bytearray:
        source = BytesReader(source)
        dest = bytearray()
        length = source.read_uint16() // 2
        while length:
            chlow, chhigh = source.read(2)
            if chhigh in (self.NEARTAG, self.FARTAG):
                count = chlow
                if not count:
                    # have to insert a word containing the tag byte
                    dest.append(source.read(1))
                    dest.append(chhigh)
                    length -= 1
                else:
                    if chhigh == self.NEARTAG:
                        copytr = len(dest) - source.read(1) * 2
                    elif chhigh == self.FARTAG:
                        copytr = source.read_uint16() * 2
                    else:  # should never happen...
                        raise ValueError(f"Unexpected chhigh value: 0x{chhigh:02x}")
                    length -= count
                    while count:
                        dest.extend(dest[copytr:copytr+2])
                        copytr += 2
                        count -= 1
            else:
                dest.append(chlow)
                dest.append(chhigh)
                length -= 1
        assert source.tell() == len(source), f"Expected to be at end of data. Pos {source.tell()}, Len {len(source)}"
        return dest

    def rlew_expand(self, source) -> list[int]:
        source = BytesReader(source)
        dest = []
        length = source.read_uint16() // 2
        while length:
            value = source.read_uint16()
            if value == self.header.rlew_tag:
                # compressed
                count = source.read_uint16()
                value = source.read_uint16()
                length -= count
                dest.extend([value] * count)
            else:
                # uncompressed
                dest.append(value)
                length -= 1
        assert source.tell() == len(source), f"Expected to be at end of data. Pos {source.tell()}, Len {len(source)}"
        return dest
