import argparse
import logging
import os
from wolf3d.palette import *
import mapexporter

logging.basicConfig(level=logging.INFO)


def export_map(args):
    palette = load_palette("palettes/Wolf3D.pal")
    gamemapsfile = os.path.join(args.inpath, "GAMEMAPS.WL6")
    vswapfile = os.path.join(args.inpath, "VSWAP.WL6")
    mapexporter.EXPORT_FLOORS = not args.nofloor
    mapexporter.EXPORT_CEILINGS = not args.noceiling
    mapexporter.EXPORT_PATH = args.outpath
    mapexporter.export_map(gamemapsfile, vswapfile, palette, args.map)


def main():
    parser = argparse.ArgumentParser(description="A tool to convert Wolfenstein 3D maps to OBJ files.")
    parser.add_argument("-i", "--inpath", type=str, help="The path to the game data.", required=True)
    parser.add_argument("-m", "--map", type=int, help="The map number to export (0-based).", required=True)
    parser.add_argument("-o", "--outpath", type=str, help="The path to export the OBJ data to.")
    parser.add_argument("--nofloor", action='store_true', help="Disables exporting of floor faces.")
    parser.add_argument("--noceiling", action='store_true', help="Disables exporting of ceiling faces.")
    parser.set_defaults(outpath="export")
    # parser.print_help()
    args = parser.parse_args()
    export_map(args)


if __name__ == '__main__':
    main()
