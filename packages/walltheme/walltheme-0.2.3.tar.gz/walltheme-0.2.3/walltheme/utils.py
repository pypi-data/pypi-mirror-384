"""
Utility functions
"""

import logging
import os
import shutil
import sys

from PIL import Image

from .settings import MODULE_DIR, TEMPLATE_DIR


def split_theme(theme: dict):
	"""
	Splits the various types of data to facilitate the creation of templates
	"""

	i = 0
	wallpaper = ''
	special = {}
	palette = {}
	for k, v in theme.items():
		if i <= 0:
			wallpaper = v
		elif 0 < i < 4:
			special[k] = v
		else:
			palette[k] = v

		i += 1

	return wallpaper, special, palette


def is_valid_image(image):
	"""
	Checks if image is valid
	"""

	try:
		with Image.open(image) as img:
			img.verify()
			return True
	except (IOError, SyntaxError):
		return False


def get_image(image):
	"""
	Gets the image's absolute path if it is valid
	"""

	if not os.path.isfile(image) or not is_valid_image(image):
		logging.error('No valid image found!')
		sys.exit(1)

	image_path = os.path.abspath(image)
	return image_path


def init_templates():
	"""
	Initializes the included templates in the correct location
	"""

	module_templates = os.path.join(MODULE_DIR, 'templates')

	for template in os.listdir(module_templates):
		template_path = os.path.join(module_templates, template)
		shutil.copy2(template_path, TEMPLATE_DIR)
		print(f'Generated {template} in {TEMPLATE_DIR}')
	print('')


def create_dir(dir_path):
	"""
	Util function to create a directory
	"""

	os.makedirs(dir_path, exist_ok=True)


def check_dir_empty(dir_path):
	"""
	Util function to check if a directory is empty
	"""

	return bool(
		os.path.exists(dir_path)
		and not os.path.isfile(dir_path)
		and not os.listdir(dir_path)
	)
