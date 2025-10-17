# Piket: Pikmin e+ Card Tools
All-in-one package for converting and managing Pikmin e+ Cards, pronounced "picket".

Currently only ships with confirmed-working Windows binaries. Linux and macOS are on the way!

## Current Capabilities
- Decode `.raw` to editable level data
- Encode editable level data to `.raw`

### Future Plans
- Go cross-platform with new binaries built from [plxl/nedclib](https://github.com/plxl/nedclib)
- Introduce classes for in-house manipulation!
  - `PikECard`: manipulate the primary card data
  - `PikELevel`: manipulate individual level data (`set_camera`, `set_character`, `set_tile`, etc.)

## Installation
Easily include Piket in your projects with `pip`:
```
pip install piket
```

## Demo
Try Piket now with the **Converter Demo**!
```
python -m venv .venv
.venv\Scripts\activate # or source .venv/bin/activate
pip install piket[demo]
python -m piket.converter_demo
```
This demo allows you to easily drag-and-drop .raw files and get decoded .bin files, and then vice versa!

## Usage Guide
Use Piket to easily decode, manipulate, and then re-encode `.raw` card files.
```py
import piket

card = piket.decode_raw("card.raw")
card[0x115] = 0x1 # set tile (0, 0) to grass
new_raw = piket.encode_raw("card.raw", card)
```
For more detailed usage, check the dedicated [Usage Guide](https://github.com/plxl/piket/blob/main/docs/usage_guide.md).

## Acknowledgements
- [Caitsith2](https://caitsith2.com/ereader/devtools.htm): Original e-Reader Tools (nedclib)
- [Lymia](https://github.com/Lymia/nedclib): Cross-platform, open source version of Caitsith2's nedclib
- [breadbored](https://github.com/breadbored/nedclib): Maintainer of Lymia's now-archived nedclib

Nintendo is the copyright and trademark holder for Pikmin, its designs and its characters. This project is free, and for educational purposes only.
