# WallTheme

## A color-scheme generation tool

Generates a color-scheme theme using the dominant colors of an image, inspired by pywal, wallust and (roughly) in the scheme of matugen (Material You theming).

## Features

 For each color retrieved from the image 2 more are generated and added to the theme. These are:

(The `primary` connotation depends on the relevance of the color. The most dominant color is the `primary`, the second is the "secondary", the third is the "tertiary", the forth is the "quaternary", the fifth is the "quinary". Further colors will just be colorN, where N is the color number)

- `primary`: The original color, useful for accents;
- `primary_light`: A lighter tone of the original color, useful for text and stuff in the foreground;
- `primary_dark`: A darker tone of the original color, useful for containers and stuff in the background;

Also, on every theme, there are four extra fields:

- `wallpaper`: The absolute path of the image provided;
- `background`: A color for the background stuff based on the most dominant color (it is darker than `primary_dark`, optimally, it will an almost black/dark grey with a slight tint of the most dominant color);
- `foreground`: A color to use in foreground stuff based on the most dominant color (it is lighter than `primary_light`, optimally, it will an almost white with a slight tint of the most dominant color);
- `cursor`: A color to use as the cursor color. It is the exact same as `foreground`;

## Requirements

- Requires python version 3.10 or greater;
- Requires [llaisdy's dominant-colours](https://github.com/llaisdy/dominant-colours);

```shell
cargo install dominant-colours
```

## Installation

- Install dominant-colours:

```shell
cargo install dominant-colours
```

- Install WallTheme:

```shell
pipx install walltheme
```

## Backend

The backend to find the dominant colors from images is [llaisdy's dominant-colours](https://github.com/llaisdy/dominant-colours) command line tool, it **IS NOT** created by me.

## Templates

Templates are also completely supported (with `jinja2`) and the following variables are available (a number of templates and an example template with multiple correct syntaxes are available in the `templates` folder):

- `theme`: Includes all the values;
- `wallpaper`: Includes the wallpaper absolute path;
- `special`: Includes the background, foreground and cursor values;
- `palette`: Includes all the colors;

While `wallpaper` is a `string` with a single value (i.e. can be referenced by just its name), all the other are dictionaries and require the following syntax to be referenced correctly:

  All these are examples and can be used on all dictionaries variables:

- `theme.items()`: References all the items in the dictionary;
- `special['background']`: References the `background` variable in `special` (quotes are required);
- `palette.secondary`: References the `secondary` variable in `palette`;

## Why

I created this tool because the available options I found and tried never satisfied my needs completely.

Both [pywal](https://github.com/dylanaraps/pywal) and [wallust](https://codeberg.org/explosion-mental/wallust) create color-schemes with colors from a provided image in pretty much any format (just have to have or create the corresponding template), but, for me, a lot of the times the order of the was seemingly random, making automation of using the color schemes the way I wanted difficult.

[Matugen](https://github.com/InioX/matugen) did choose the dominant color for the theming the grand majority of the times, but it takes into account only a single color, and the color tones of color schemes themselves are not based on the color itself, but on what the color is (red, green, blue, etc), resulting in a lot of similar looking themes and mismatching secondary and tertiary colors.

This tool (in my biased opinion), combines the best of both worlds.
