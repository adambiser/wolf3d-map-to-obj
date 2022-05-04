import PIL
import PIL.Image
import PIL.ImageOps
import typing
from .utils import *
if typing.TYPE_CHECKING:
    import PIL.ImagePalette

__all__ = ["Vswap"]


class Vswap:
    TEXTURE_SIZE = 64

    def __init__(self, file):
        self.file = file
        self.palette = None
        self.f = BinaryFileReader(file)
        self.chunks_in_file = self.f.read_uint16()
        self.sprite_start = self.f.read_uint16()
        self.sound_start = self.f.read_uint16()
        self.offsets = self.f.read_uint32_array(self.chunks_in_file)
        self.lengths = self.f.read_uint16_array(self.chunks_in_file)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.f.close()

    def set_palette(self, palette: "PIL.ImagePalette.ImagePalette"):
        self.palette = palette

    def load_wall(self, index):
        assert 0 <= index < self.sprite_start, "Not a wall index."
        assert self.palette, "Palette not set."
        self.f.seek(self.offsets[index])
        assert self.lengths[index] == self.TEXTURE_SIZE * self.TEXTURE_SIZE, f"Unexpected length: {self.lengths[index]}"
        data = self.f.read(self.lengths[index])
        image = PIL.Image.new("P", (self.TEXTURE_SIZE, self.TEXTURE_SIZE))
        image.putpalette(self.palette)
        image.putdata(data)
        # VSWAP wall data is in posts, not rows, so flip diagonally.
        image = image.rotate(-90)  # negative to rotate clockwise.
        image = PIL.ImageOps.mirror(image)
        return image
