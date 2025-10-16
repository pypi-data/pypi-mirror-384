"""
Jinja2 setup
"""

import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from . import colors, utils


def setup_jinja_env(templates_dir: Path) -> Environment:
	"""
	Jinja2 environment setup
	"""

	env = Environment(
		loader=FileSystemLoader(str(templates_dir)),
		autoescape=False,
		keep_trailing_newline=True,
		trim_blocks=True,
		lstrip_blocks=True,
	)

	# Lighten/Darken color with adjust_lightness
	env.filters['lighten'] = lambda color, amount=1.2: colors.adjust_lightness(
		color, amount
	)
	env.filters['darken'] = lambda color, amount=0.8: colors.adjust_lightness(
		color, amount
	)

	return env


def render_templates(
	templates_dir: Path, output_dir: Path, theme: dict
) -> None:
	"""
	Render all *.j2 templates in templates_dir into output_dir
	Templates keep their filename but with the .j2 suffix removed
	"""

	env = setup_jinja_env(templates_dir)

	for template_path in templates_dir.rglob('*.j2'):
		rel = template_path.relative_to(templates_dir)
		template = env.get_template(str(rel))
		wallpaper, special, palette = utils.split_theme(theme)
		context = {
			'theme': theme,
			'wallpaper': wallpaper,
			'special': special,
			'palette': palette,
		}
		rendered = template.render(**context)

		# Write to output file with same path but strip .j2
		output = output_dir / rel.with_suffix('')
		output.parent.mkdir(parents=True, exist_ok=True)
		output.write_text(rendered, encoding='utf-8')
		print(f'Generated {os.path.basename(template_path)} to {output}')
