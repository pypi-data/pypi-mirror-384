"""
Generates themes from an image's dominant colors
"""

import colorsys
import json
import math
import re
import subprocess
from typing import Dict, List

import matplotlib.colors as mc


def get_dominant_colors(image_path: str, max_colors: int = 5) -> List[dict]:
	"""
	Get n (max_colors) dominant colors from the image provided
	"""

	cmd = [
		'dominant-colours',
		image_path,
		f'--colours={max_colors}',
		'--format=json',
	]

	# Get output from dominant-colours, in json format
	try:
		output = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
		# print(output)
	except subprocess.CalledProcessError as exc:
		print('dominant-colours error:', exc)
		print('Output:', exc.output)
		raise

	# Get only output inside {}
	output_json = re.search(r'\{.*\}', output, re.DOTALL)

	if not output_json:
		raise RuntimeError('Could not find JSON in dominant-colours output')

	data = json.loads(output_json.group(0))
	# print(data)

	return data['colours']


def adjust_lightness(color, amount):
	"""
	Generates a new color from the original color according to the amount provided
	Darker color if amount < 1 and lighter color if amount > 1
	"""

	c = color
	c = colorsys.rgb_to_hls(*mc.to_rgb(c))

	# Adjusts the lightness value of the color and then coverts it to rgb
	adjusted_color = colorsys.hls_to_rgb(
		c[0], max(0, min(1, amount * c[1])), c[2]
	)

	return mc.to_hex(adjusted_color)


def is_light(rgb: tuple):
	"""
	Checks if the color is too light, to properly adjust it later
	"""

	[r, g, b] = rgb
	hsp = math.sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b))

	if hsp > 75:
		return True

	return False


def is_dark(rgb: tuple):
	[r, g, b] = rgb
	hsp = math.sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b))

	if hsp < 35:
		return True
	return False


def gen_theme(image_path: str, colors: List[dict]) -> Dict[str, str]:
	"""
	Generates the theme from the dominant colors obtained previously
	"""

	theme = {}
	theme['wallpaper'] = image_path

	# Generates and adds an extremely dark tone and an extremely light tone
	# of the most dominant color for the background and foreground, respectively
	theme['background'] = adjust_lightness(colors[0]['hex'], 0.2)
	foreground = adjust_lightness(colors[0]['hex'], 5.5)
	theme['foreground'] = foreground
	theme['cursor'] = foreground

	#
	for color in colors:
		match len(theme):
			case 4:
				prefix = 'primary'
			case 7:
				prefix = 'secondary'
			case 10:
				prefix = 'tertiary'
			case 13:
				prefix = 'quaternary'
			case 16:
				prefix = 'quinary'
			case _:
				prefix = f'color{int((len(theme) - 1) / 3)}'
				# print(prefix)

		dark = adjust_lightness(color['hex'], 0.5)

		# To prevent the lighter tone to become white (or close to it)
		# I first check if the color is very light to adjust
		# how light to generate the new tone
		color_lightness = is_light(color['rgb'])
		light = (
			adjust_lightness(color['hex'], 1.5)
			if color_lightness
			else adjust_lightness(color['hex'], 2.5)
		)

		theme[prefix] = color['hex']
		theme[prefix + '_dark'] = dark
		theme[prefix + '_light'] = light

	return theme
