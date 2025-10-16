# qoi-rs

Python library made using [qoi](https://crates.io/crates/qoi) and [pyo3](https://crates.io/crates/pyo3).

## Usage

### With [Pillow](https://pillow.readthedocs.io/en/stable/)

```py
from PIL import Image
from qoi_rs import encode_pillow, decode_pillow

image: Image.Image = Image.open("./qoi_test_images/dice.png")

qoi_bytes: bytes = encode_pillow(image)
decoded: Image.Image = decode_pillow(qoi_bytes)

assert decoded.width == image.width
assert decoded.height == image.height

assert tuple(decoded.getdata()) == tuple(image.getdata())

image.close()
decoded.close()
```
