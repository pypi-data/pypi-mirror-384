# ColorTransfer

**English** | [中文](README_zh.md)

---

## Project Overview

ColorTransfer provides a suite of tools for color migration tasks.

## Installation

```bash
# from pypi
pip install chromasoul_color_transfer

# from release
pip install chromasoul_color_transfer-{version}-py3-none-any.whl

# from source code(without uv)
pip install -e .

# from source code(with uv)
uv sync
```

## Quick start

1. Use the cli tool.

```bash
color_transfer --input /path/to/input_image --reference /path/to/reference_image --output /path/to/output_image

# or shortcut
color_transfer -i /path/to/input_image -r /path/to/reference_image -o /path/to/output_image
```

2. Use the example code.

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from color_transfer.libs import TransferFactory
from color_transfer.utils import ImageUtils


def main():
    # init image transfer
    transfer = TransferFactory.create("mean_std")

    # load the images
    img_ref = ImageUtils.load_img("path/to/input_image")
    img = ImageUtils.load_img("path/to/reference_image")

    # load the images
    transfer.extract(img_ref)
    img_tgt = transfer.transfer(img)

    # the target dir will be auto created
    ImageUtils.save_img(img_tgt, "path/to/output_image")


if __name__ == "__main__":
    main()

```

## Available Methods

- mean_std
- lab (Reinhard)
- pdf (Probability Density Function)
- lhm (Linear Histogram Matching)
- pccm (Principal Component Color Matching)
- emd (Earth Mover’s Distance OT method)
- sinkhorn (Sinkhorn OT method)

## License

This project is licensed under the AGPLv3 License. This means you are free to use, modify, and distribute the code, but any modifications or services based on this project must be open-sourced under the same license. For commercial closed-source integration, please contact us for a commercial license.

See the [LICENSE](LICENSE) file for details.

## Contact Me

- Project Homepage: [GitHub Repository](https://github.com/XIAODUOLU/ChromaSoul)
- Issue Reports: [Issues](https://github.com/XIAODUOLU/ChromaSoul/issues)
- Email: lxd0705@163.com

---

**ChromaSoul** - Let every color find its soul mate ✨
