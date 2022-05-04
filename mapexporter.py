import logging
import os
from math import sqrt
from wolf3d.gamemaps import *
from wolf3d.vswap import *
from model.objfile import ObjFile
from model.mtlfile import MtlFile

logger = logging.getLogger("mapexporter")

# MAP SETTINGS
WALL_CODES = tuple(range(1, 50))
FLOOR_CODES = tuple(range(107, 144))
FLOOR_MARKERS = (106, 107)  # Things like the ambush and secret elevator codes.
DOOR_EW_CODES = (90, 92, 94, 100)
DOOR_NS_CODES = (91, 93, 95, 101)
PUSHWALL_CODES = (98,)
DOOR_EW_PICS = (99, 105, 105, 103)
DOOR_EW_SIDES = (100, 100, 100, 100)
DOOR_NS_PICS = (98, 104, 104, 102)
DOOR_NS_SIDES = (101, 101, 101, 101)
FLOOR_COLOR = 112 / 256, 112 / 256, 112 / 256
CEILING_COLOR = 56 / 256, 56 / 256, 56 / 256

WALL_PLANE = 0
OBJECT_PLANE = 1
# NOTE: N/S faces are the lighter (even) ones!
_FACING_NS = 0
_FACING_EW = 1

# EXPORT SETTINGS
EXPORT_FLOORS = True
EXPORT_CEILINGS = True
EXPORT_PATH = "export"


def _normalize(x, y, z):
    multiplier = 1 / sqrt(x * x + y * y + z * z)
    return x * multiplier, y * multiplier, z * multiplier


def _get_wall_face(x1, z1, x2, z2, reverse_texture=False):
    """x1, z1 = bottom left, x2, z2 = top right"""
    v = ((x1, 0, z1),
         (x2, 0, z2),
         (x2, 1, z2),
         (x1, 1, z1))
    t = ((1, 0), (0, 0), (0, 1), (1, 1)) if reverse_texture else ((0, 0), (1, 0), (1, 1), (0, 1))
    nz = x2 - x1
    nx = z1 - z2
    n = (_normalize(nx, 0, nz),) * 4
    return v, t, n


def _get_flat_face(x1, z1, x2, z2, y):
    """floor = x, y + 1 -> x + 1, y
    ceiling = x + 1, y + 1 -> x, y
    """
    v = ((x1, y, z1),
         (x2, y, z1),
         (x2, y, z2),
         (x1, y, z2))
    t = ((0, 0), (1, 0), (1, 1), (0, 1))
    ny = x2 - x1
    n = (_normalize(0, ny, 0),) * 4
    return v, t, n


def _scan_for_rooms(gamemap: GameMap):
    rooms = {}

    def add_tile_to_room(floorcode, tx, ty):
        if floorcode not in rooms:
            rooms[floorcode] = []
        tile = (tx, ty)
        if tile not in rooms[floorcode]:
            rooms[floorcode].append(tile)

    def add_adjoining_floor_code(tx, ty, offsetx, offsety):
        """Returns True if a floor code was found at the tile adjoining the current tile.
        The current tile will be added to that floor code's room.
        """
        testx = tx + offsetx
        testy = ty + offsety
        if 0 <= testx < gamemap.width and 0 <= testy < gamemap.height:
            testcode = gamemap.tiles[WALL_PLANE][testy][testx]
            if testcode in FLOOR_CODES:
                add_tile_to_room(testcode, tx, ty)
                return True
        return False

    for y in range(gamemap.height):
        for x in range(gamemap.width):
            code = gamemap.tiles[WALL_PLANE][y][x]
            if code in FLOOR_CODES:
                add_tile_to_room(code, x, y)
            if code in FLOOR_MARKERS:
                # Should only be in one room.
                if not add_adjoining_floor_code(x, y, -1, 0):
                    if not add_adjoining_floor_code(x, y, 1, 0):
                        if not add_adjoining_floor_code(x, y, 0, -1):
                            if not add_adjoining_floor_code(x, y, 0, 1):
                                logger.warning(f"Could not find floor code for floor marker at {x}, {y}.")
            elif code in DOOR_EW_CODES:
                # Doors are in two rooms (each side). - Actually, just use the room to the west.
                if not add_adjoining_floor_code(x, y, -1, 0):
                    logger.warning(f"Could not find west floor code for door at {x}, {y}.")
                    if not add_adjoining_floor_code(x, y, 1, 0):
                        logger.warning(f"Could not find east floor code for door at {x}, {y}.")
            elif code in DOOR_NS_CODES:
                # Doors are in two rooms (each side). - Actually, just use the room to the north.
                if not add_adjoining_floor_code(x, y, 0, -1):
                    logger.warning(f"Could not find north floor code for door at {x}, {y}.")
                    if not add_adjoining_floor_code(x, y, 0, 1):
                        logger.warning(f"Could not find south floor code for door at {x}, {y}.")
            elif gamemap.tiles[OBJECT_PLANE][y][x] in PUSHWALL_CODES:
                # Pushwalls should only be in one room.
                if not add_adjoining_floor_code(x, y, -1, 0):
                    if not add_adjoining_floor_code(x, y, 1, 0):
                        if not add_adjoining_floor_code(x, y, 0, -1):
                            if not add_adjoining_floor_code(x, y, 0, 1):
                                logger.warning(f"Could not find floor code for pushwall at {x}, {y}.")
    return rooms


def _export_rooms(gamemap, mapindex, vswap, rooms):
    obj = ObjFile()
    mtl = MtlFile()
    mtl.start_material("floor")
    mtl.set_diffuse_reflectivity(*FLOOR_COLOR)
    mtl.start_material("ceiling")
    mtl.set_diffuse_reflectivity(*CEILING_COLOR)

    textures = []

    def get_wall_texture_id(wallcode, facing):
        return (wallcode - 1) * 2 + facing

    # noinspection PyShadowingNames
    def add_face_to_texture_group(group_name, face):
        if group_name not in texture_groups:
            texture_groups[group_name] = []
        texture_groups[group_name].append(face)

    # noinspection PyShadowingNames
    def load_texture(texture_type, texture_id):
        texture_name = f"{texture_type}{texture_id:03}"
        if texture_id not in textures:
            logger.info(f"Exporting {texture_name}")
            textures.append(texture_id)
            image = vswap.load_wall(texture_id)
            image.save(os.path.join(EXPORT_PATH, f"{texture_name}.png"))
            mtl.start_material(texture_name)
            mtl.set_color_texture(f"{texture_name}.png")
        return texture_name

    def add_if_wall(testx, testy, facing, tx1, ty1, tx2, ty2):
        """direction: 0 = N/S, 1 = E/W"""
        if 0 <= testx < gamemap.width and 0 <= testy < gamemap.height:
            wallcode = gamemap.tiles[WALL_PLANE][testy][testx]
            if wallcode in WALL_CODES and \
                    not gamemap.tiles[OBJECT_PLANE][testy][testx] in PUSHWALL_CODES:
                # noinspection PyShadowingNames
                texture_id = get_wall_texture_id(wallcode, facing)
                # noinspection PyShadowingNames
                name = load_texture("wall", texture_id)
                add_face_to_texture_group(name, _get_wall_face(tx1, ty1, tx2, ty2))

    # noinspection PyShadowingNames
    def write_faces(texture_name, faces):
        obj.add_use_material(texture_name)
        for face in faces:
            obj.add_face(*face)

    door_faces = []  # global to the map
    pushwall_faces = [] # global to the map
    for floor_code, tiles in sorted(rooms.items()):
        texture_groups = {}
        for floor_tile in tiles:
            x, y = floor_tile
            code = gamemap.tiles[WALL_PLANE][y][x]
            # Add flats.
            if EXPORT_FLOORS:
                add_face_to_texture_group("floor", _get_flat_face(x, y + 1, x + 1, y, 0))  # Floor
            if EXPORT_CEILINGS:
                add_face_to_texture_group("ceiling", _get_flat_face(x + 1, y + 1, x, y, 1))  # Ceiling
            # Special handling for doors.
            if code in DOOR_EW_CODES:
                door_index = DOOR_EW_CODES.index(code)
                texture_id = DOOR_EW_PICS[door_index]
                name = load_texture("door", texture_id)
                door_faces.append((name, (
                    _get_wall_face(x + 0.5, y, x + 0.5, y + 1),  # East, middle
                    _get_wall_face(x + 0.5, y + 1, x + 0.5, y, True)  # West, middle
                )))
                texture_id = DOOR_EW_SIDES[door_index]
                name = load_texture("wall", texture_id)
                add_face_to_texture_group(name, _get_wall_face(x, y, x + 1, y))  # South, inwards
                add_face_to_texture_group(name, _get_wall_face(x + 1, y + 1, x, y + 1))  # North, inwards
                continue
            elif code in DOOR_NS_CODES:
                door_index = DOOR_NS_CODES.index(code)
                texture_id = DOOR_NS_PICS[door_index]
                name = load_texture("door", texture_id)
                door_faces.append((name, (
                    _get_wall_face(x, y + 0.5, x + 1, y + 0.5),  # South, middle
                    _get_wall_face(x + 1, y + 0.5, x, y + 0.5, True)  # North, middle
                )))
                texture_id = DOOR_NS_SIDES[door_index]
                name = load_texture("wall", texture_id)
                add_face_to_texture_group(name, _get_wall_face(x, y + 1, x, y))  # West, inwards
                add_face_to_texture_group(name, _get_wall_face(x + 1, y, x + 1, y + 1))  # East, inwards
                continue
            elif code in WALL_CODES and gamemap.tiles[OBJECT_PLANE][y][x] in PUSHWALL_CODES:
                # These faces face *outwards* from the tile.
                texture_name_ew = load_texture("wall", get_wall_texture_id(code, _FACING_EW))
                texture_name_ns = load_texture("wall", get_wall_texture_id(code, _FACING_NS))
                # ns_texture_id = get_wall_texture_id(code, _FACING_NS)
                pushwall_faces.append((
                        (texture_name_ns, (
                            _get_wall_face(x, y + 1, x + 1, y + 1),  # South, outwards
                            _get_wall_face(x + 1, y, x, y)  # North, outwards
                        )),
                        (texture_name_ew, (
                            _get_wall_face(x, y, x, y + 1),  # West, outwards
                            _get_wall_face(x + 1, y + 1, x + 1, y)  # East, outwards
                        )),
                ))
                pass
            # Check for surrounding walls.
            add_if_wall(x - 1, y, _FACING_EW, x, y + 1, x, y)  # West, inwards
            add_if_wall(x + 1, y, _FACING_EW, x + 1, y, x + 1, y + 1)  # East, inwards
            add_if_wall(x, y - 1, _FACING_NS, x, y, x + 1, y)  # South, inwards
            add_if_wall(x, y + 1, _FACING_NS, x + 1, y + 1, x, y + 1)  # North, inwards

        # Output this room.
        obj.add_object_name(f"Room_{floor_code}")
        obj.add_group(f"Room_{floor_code}")
        for texture_name, faces in sorted([(tn, f) for tn, f in texture_groups.items() if tn.startswith("wall")]):
            write_faces(texture_name, faces)
        # Add flats
        if EXPORT_FLOORS:
            write_faces("floor", texture_groups["floor"])
        if EXPORT_CEILINGS:
            write_faces("ceiling", texture_groups["ceiling"])
    # Add door objects
    for (index, (texture_name, faces)) in enumerate(door_faces):
        obj.add_object_name(f"Door_{index + 1}")
        obj.add_group(f"Door_{index + 1}")
        write_faces(texture_name, faces)
    # Add pushwalls
    for (index, pushwall_info) in enumerate(pushwall_faces):
        obj.add_object_name(f"Pushwall_{index + 1}")
        obj.add_group(f"Pushwall_{index + 1}")
        for texture_name, faces in pushwall_info:
            write_faces(texture_name, faces)
    mtl.save(os.path.join(EXPORT_PATH, f"map{mapindex:02}.mtl"))
    obj.add_mtl_file(f"map{mapindex:02}.mtl")
    obj.save(os.path.join(EXPORT_PATH, f"map{mapindex:02}.obj"))


def export_map(gamemapsfile, vswapfile, palette, mapindex):
    with GameMaps(gamemapsfile) as maps:
        with Vswap(vswapfile) as vswap:
            vswap.set_palette(palette)
            gamemap = maps.load_map(mapindex)
            rooms = _scan_for_rooms(gamemap)
            os.makedirs(EXPORT_PATH, exist_ok=True)
            _export_rooms(gamemap, mapindex, vswap, rooms)
