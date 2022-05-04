# http://paulbourke.net/dataformats/mtl/

class MtlFile:
    def __init__(self):
        self._commands = []

    def start_material(self, name):
        if len(self._commands):
            self._commands.append("")
        self._commands.append(f'newmtl {name}')

    def end_material(self):
        self._commands.append("")

    def set_diffuse_reflectivity(self, red, green=None, blue=None):
        green = green or red
        blue = blue or red
        self._commands.append(f'Kd {red} {green} {blue}')

    def set_color_texture(self, file):
        self._commands.append(f'map_Kd {file}')

    def save(self, file, header=None):
        with open(file, 'w') as f:
            if header:
                if isinstance(header, str):
                    f.write(f'# {header}\n')
                else:
                    for line in header:
                        f.write(f'# {line}\n')
                f.write('\n')
            for command in self._commands:
                f.write(f'{command}\n')
