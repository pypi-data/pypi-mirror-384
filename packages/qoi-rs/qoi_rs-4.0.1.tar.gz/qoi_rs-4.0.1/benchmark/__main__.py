import sys
from collections.abc import Buffer

import qoi  # type: ignore[import-untyped]
import qoi_rs
import numpy
from PIL import Image
from .timer import Timer


def qoi_encode(image: Image.Image) -> bytes:
    return qoi.encode(numpy.asarray(image))


def qoi_rs_encode(image: Image.Image) -> bytes:
    return qoi_rs.encode_pillow(image)


def main(args: list[str]) -> int | str:
    timers = [(Timer(fun.__name__), fun) for fun in (qoi_encode, qoi_rs_encode)]

    for _ in range(10):
        timers.reverse()
        for image_path in args:
            qoi_images = set()
            image = Image.open(image_path)
            image.load()
            for (timer, fun) in timers:
                with timer:
                    qoi_img = fun(image)
                assert isinstance(qoi_img, Buffer)
                if not _:
                    decoded = qoi_rs.decode(qoi_img)
                    qoi_images.add((decoded.width, decoded.height, decoded.mode, decoded.colour_space, decoded.data))
            image.close()
            del image
            if not _:
                assert len(qoi_images) == 1, f"{qoi_images}"

    print(f"Benchmarked with {len(args)} images")
    for (timer, _) in timers:
        print(timer)

    for (timer, _) in timers:
        assert timer.count == len(args) * 10, f"{timer.name} has wrong count {timer.count}"

    return 0


sys.exit(main(sys.argv[1:]))
