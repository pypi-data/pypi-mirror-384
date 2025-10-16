#!/usr/bin/env -S uv run --reinstall-package qoi-rs --script
# /// script
# dependencies = [
#   "qoi-rs",
# ]
# [tool.uv.sources]
# qoi-rs = { path = ".", extra = "pillow" }
# ///

from collections.abc import Buffer
from pathlib import Path

import qoi_rs

from PIL import Image

IMAGES_DIR = Path(__file__).absolute().parent / "qoi_test_images"


for file in "dice", "testcard", "qoi_logo", "wikipedia_008":
    qoi_image_path = IMAGES_DIR / f"{file}.qoi"
    png_image_path = IMAGES_DIR / f"{file}.png"

    image = qoi_rs.decode(qoi_image_path.read_bytes())
    assert isinstance(image, qoi_rs.types.Image)
    png_image = Image.open(png_image_path)
    pil_qoi_image = Image.open(qoi_image_path)

    assert image.width == png_image.width == pil_qoi_image.width
    assert image.height == png_image.height == pil_qoi_image.height
    assert image.mode == pil_qoi_image.mode
    assert isinstance(image.data, Buffer)
    assert image.mode in {"RGB", "RGBA"}

    for img in png_image, pil_qoi_image:
        encoded = qoi_rs.encode(img.getdata(), width=img.width, height=img.height)
        assert encoded == qoi_rs.encode(img, width=img.width, height=img.height, input_channels="RGBX" if img.mode.upper() == "RGB" else "RGBA")
        assert encoded == qoi_rs.encode(img.tobytes(), width=img.width, height=img.height)
        assert encoded == qoi_rs.encode_pillow(img)
        assert isinstance(encoded, Buffer)
        assert type(encoded) is bytes
        decoded = qoi_rs.decode(encoded)
        assert image.width == decoded.width
        assert image.height == decoded.height
        assert image.colour_space == decoded.colour_space
        assert image.mode == decoded.mode, f"{file}: {image.mode} != {decoded.mode}"
        assert image.channels == image.channels
        assert type(image) is type(decoded)
        assert len(image.data) == len(decoded.data), f"{file}: {len(image.data)} != {len(decoded.data)}"
        assert image.data == decoded.data, f"{file}"
        assert image == decoded, f"{file}"

        assert tuple(png_image.getdata()) == tuple(qoi_rs.decode_pillow(encoded).getdata())

    encoded = qoi_rs.encode(image.data, width=image.width, height=image.height, colour_space="linear")
    assert qoi_rs.decode(encoded).colour_space == "linear"
    encoded = qoi_rs.encode(image.data, width=image.width, height=image.height, colour_space="SRGB")
    assert qoi_rs.decode(encoded).colour_space == "SRGB"

    for img in png_image, pil_qoi_image:
        encoded = qoi_rs.encode_pillow(img, colour_space="linear")
        assert qoi_rs.decode(encoded).colour_space == "linear"
        encoded = qoi_rs.encode_pillow(img, colour_space="SRGB")
        assert qoi_rs.decode(encoded).colour_space == "SRGB"

    try:
        qoi_rs.encode(image.data, width=image.width, height=image.height, colour_space="test")  # type: ignore[arg-type]
    except ValueError as err:
        assert len(err.args) == 1
        assert "invalid colour space" in err.args[0]
    else:
        assert False

    if image.mode == "RGB":
        encoded = qoi_rs.encode(image.data, width=image.width, height=image.height, input_channels="RGB")
        assert qoi_rs.decode(encoded).mode == "RGB"
        encoded = qoi_rs.encode(image.data, width=image.width, height=image.height, input_channels="BGR")
        assert qoi_rs.decode(encoded).mode == "RGB"
    else:
        encoded = qoi_rs.encode(image.data, width=image.width, height=image.height, input_channels="RGBA")
        assert qoi_rs.decode(encoded).mode == "RGBA"
        encoded = qoi_rs.encode(image.data, width=image.width, height=image.height, input_channels="ARGB")
        assert qoi_rs.decode(encoded).mode == "RGBA"
        encoded = qoi_rs.encode(image.data, width=image.width, height=image.height, input_channels="RGBX")
        assert qoi_rs.decode(encoded).mode == "RGB"

    try:
        qoi_rs.encode(image.data, width=image.width, height=image.height, input_channels="test")  # type: ignore[arg-type]
    except ValueError as err:
        assert len(err.args) == 1
        assert "invalid channels" in err.args[0]
    else:
        assert False

    try:
        qoi_rs.encode(image.data, width=image.width + 1, height=image.height)
    except ValueError as err:
        assert len(err.args) == 1
        assert err.args[0].startswith("invalid image length: ")
    else:
        assert False

    try:
        qoi_rs.encode(image.data, width=image.width, height=image.height + 1)
    except ValueError as err:
        assert len(err.args) == 1
        assert err.args[0].startswith("invalid image length: ")
    else:
        assert False

    png_image.close()
    pil_qoi_image.close()

try:
    qoi_rs.encode(b"", width=1, height=1)
except ValueError as err:
    assert len(err.args) == 1
    assert "invalid image length: 0 bytes for 1x1" == err.args[0]
else:
    assert False

try:
    qoi_rs.decode(b"")
except ValueError as err:
    assert len(err.args) == 1
    assert "unexpected input buffer end while decoding" == err.args[0]
else:
    assert False


assert qoi_rs.decode(qoi_rs.encode([(1, 2, 3)] * 12, width=4, height=3)).mode == "RGB"
assert qoi_rs.decode(qoi_rs.encode([(1, 2, 3, 4)] * 12, width=4, height=3)).mode == "RGBA"
try:
    qoi_rs.encode([(1, 2, 3, 4)] * 9, width=4, height=3)
except ValueError as err:
    assert len(err.args) == 1
    assert "got 9 pixels, image can't be 4x3" == err.args[0]
else:
    assert False


assert qoi_rs.decode(qoi_rs.encode([(1, 2, 3, 4)], width=1, height=1, colour_space="linear")).colour_space == "linear"
assert qoi_rs.decode(qoi_rs.encode([(1, 2, 3, 4)], width=1, height=1, colour_space="SRGB")).colour_space == "SRGB"
try:
    qoi_rs.encode([(1, 2, 3, 4)], width=1, height=1, colour_space="ÄÖÜ")  # type: ignore[arg-type]
except ValueError as err:
    assert len(err.args) == 1
    assert 'invalid colour space, needs to be one of ["linear", "SRGB"]' == err.args[0]
else:
    assert False
