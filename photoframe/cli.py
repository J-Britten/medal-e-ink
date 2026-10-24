import argparse
import logging
import sys

from PIL import Image

from . import epd, image

COLORS = {
    "white": epd.WHITE,
    "black": epd.BLACK,
    "yellow": epd.YELLOW,
    "red": epd.RED,
    "blue": epd.BLUE,
    "green": epd.GREEN,
}


def cmd_show(args):
    with Image.open(args.image) as src:
        pimg = image.prepare(
            src,
            rotate=args.rotate,
            fit=args.fit,
            saturation=args.saturation,
            contrast=args.contrast,
            dither=not args.no_dither,
        )

    if args.preview:
        image.preview(pimg).save(args.preview)
        logging.info("preview written to %s", args.preview)
        return

    buf = image.pack(pimg)
    with epd.EPD() as panel:
        panel.display(buf)


def cmd_clear(args):
    with epd.EPD() as panel:
        panel.clear(COLORS[args.color])


def build_parser():
    parser = argparse.ArgumentParser(prog="photoframe", description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="display a single picture")
    show.add_argument("image", help="path to a JPEG/PNG/... file")
    show.add_argument(
        "--rotate",
        type=int,
        default=0,
        choices=(0, 90, 180, 270),
        help="panel mounting rotation, clockwise (90/270 = portrait frame)",
    )
    show.add_argument(
        "--fit",
        choices=("cover", "contain"),
        default="cover",
        help="cover: crop to fill (default); contain: letterbox with white bars",
    )
    show.add_argument("--saturation", type=float, default=1.2)
    show.add_argument("--contrast", type=float, default=1.0)
    show.add_argument("--no-dither", action="store_true")
    show.add_argument(
        "--preview",
        metavar="OUT.png",
        help="write what would be displayed to a PNG instead of using the panel",
    )
    show.set_defaults(func=cmd_show)

    clear = sub.add_parser("clear", help="fill the panel with one color")
    clear.add_argument("--color", choices=COLORS, default="white")
    clear.set_defaults(func=cmd_clear)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )
    try:
        args.func(args)
    except (OSError, ValueError, TimeoutError) as e:
        logging.error("%s", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
