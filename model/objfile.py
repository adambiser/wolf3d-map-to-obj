# http://paulbourke.net/dataformats/obj/

class ObjFile:
    def __init__(self):
        self._mtlib = []
        self._vertices = []  # (x, y, z)
        self._textures = []  # (u, v)
        self._normals = []  # (x, y, z)
        self._commands = []

    def _add_vertex(self, vertex):
        try:
            return self._vertices.index(vertex) + 1
        except ValueError:
            self._vertices.append(vertex)
            return len(self._vertices)

    def _add_textures(self, texture):
        try:
            return self._textures.index(texture) + 1
        except ValueError:
            self._textures.append(texture)
            return len(self._textures)

    def _add_normals(self, normal):
        try:
            return self._normals.index(normal) + 1
        except ValueError:
            self._normals.append(normal)
            return len(self._normals)

    def add_face(self, vertices, textures=None, normals=None):
        vertices = [self._add_vertex(v) for v in vertices]
        if textures is not None:
            assert len(textures) == len(vertices)
            textures = [self._add_textures(t) for t in textures]
        if normals is not None:
            assert len(normals) == len(vertices)
            normals = [self._add_normals(n) for n in normals]
        command = 'f'
        for index in range(len(vertices)):
            command += f' {vertices[index]}'
            if textures is not None:
                command += f'/{textures[index]}'
            if normals is not None:
                if textures is None:
                    command += '/'
                command += f'/{normals[index]}'
        self._commands.append(command)

    def add_mtl_file(self, file):
        self._mtlib.append(file)

    def add_comment(self, text):
        self._commands.append(f'# {text}')

    def add_object_name(self, name):
        self._commands.append(f'o {name}')

    def add_group(self, name):
        self._commands.append(f'g {name}')

    def add_use_material(self, name):
        self._commands.append(f'usemtl {name}')

    def save(self, file, header=None):
        with open(file, 'w') as f:
            if header:
                if isinstance(header, str):
                    f.write(f'# {header}\n')
                else:
                    for line in header:
                        f.write(f'# {header}\n')
                f.write('\n')
            if self._mtlib:
                f.write(f'mtllib {",".join(self._mtlib)}\n')
            for vertex in self._vertices:
                f.write(f'v {vertex[0]} {vertex[1]} {vertex[2]}\n')
            for texture in self._textures:
                f.write(f'vt {texture[0]} {texture[1]}\n')
            for normal in self._normals:
                f.write(f'vn {normal[0]} {normal[1]} {normal[2]}\n')
            for command in self._commands:
                f.write(f'{command}\n')
