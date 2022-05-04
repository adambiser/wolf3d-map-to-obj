import PIL.ImagePalette


def load_palette(file):
    with open(file, "rb") as fp:
        return PIL.ImagePalette.ImagePalette(mode="RGB", palette=fp.read())
