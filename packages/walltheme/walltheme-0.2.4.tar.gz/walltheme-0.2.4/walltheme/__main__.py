"""
WallTheme by Leandro Pata
"""

import argparse
import sys

from . import colors, jinja, utils
from .settings import CACHE_DIR, TEMPLATE_DIR, __version__


def get_args() -> argparse.Namespace:
	"""
	Gets the arguments passed to the program
	"""

	arg = argparse.ArgumentParser(
		prog='walltheme',
		description="Generate themes from an image's dominant colors",
	)

	arg.add_argument('image', nargs='?', default=None, help='Path to image file')

	arg.add_argument(
		'-m',
		'--max-colors',
		type=int,
		default=5,
		required=False,
		help='Number of dominant colors',
	)

	arg.add_argument(
		'-v',
		'--version',
		action='store_true',
		help='Print "walltheme" version',
	)

	return arg


def parse_args_exit(parser):
	"""
	Arguments restrictions that cause the program to exit
	"""

	args = parser.parse_args()

	if len(sys.argv) <= 1:
		parser.print_help()
		sys.exit(1)

	if args.version:
		parser.exit(0, 'WallTheme %s\n' % __version__)

	if not args.image:
		parser.error('No image provided!')
		sys.exit(1)


def parse_args(parser):
	"""
	Parses the arguments and generates the theme
	"""

	args = parser.parse_args()

	if args.image:
		image = utils.get_image(args.image)
		d_colors = colors.get_dominant_colors(image, args.max_colors)
		theme = colors.gen_theme(image, d_colors)
	else:
		parser.error('No image provided!')
		sys.exit(1)

	return theme


def main():
	"""
	Main function
	"""
	utils.create_dir(TEMPLATE_DIR)
	utils.create_dir(CACHE_DIR)

	is_empty = utils.check_dir_empty(TEMPLATE_DIR)

	if is_empty:
		utils.init_templates()

	parser = get_args()
	parse_args_exit(parser)
	theme = parse_args(parser)

	jinja.render_templates(TEMPLATE_DIR, CACHE_DIR, theme)


if __name__ == '__main__':
	main()
