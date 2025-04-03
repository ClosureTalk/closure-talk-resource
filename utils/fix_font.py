from argparse import ArgumentParser
from pathlib import Path
from fontTools import ttLib
from fontTools.pens.areaPen import AreaPen

def main():
    parser = ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()

    file = Path(args.file)
    font = ttLib.TTFont(file, lazy=False)
    glyphs = font.getGlyphSet()

    to_keep = []
    for name in font.getGlyphNames():
        glyph = glyphs[name]
        pen = AreaPen()
        glyph.draw(pen)
        if pen.value > 0:
            to_keep.append(glyph.name)

    print(f"Keep {len(to_keep)} / {len(glyphs)} glyphs")
    (file.parent / f"{file.stem}-keep.txt").write_text("\n".join(to_keep))

if __name__ == "__main__":
    main()
