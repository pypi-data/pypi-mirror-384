# StyleTransfer

**English** | [中文](README_zh.md)

---

## Project Overview

StyleTransfer provides a suite of tools for style migration tasks.

## Installation

```bash
# from pypi
pip install chromasoul_style_transfer

# from release
pip install chromasoul_style_transfer-{version}-py3-none-any.whl

# from source code(without uv)
pip install -e .

# from source code(with uv)
uv sync
```

## Quick start

1. Use the cli tool.

```bash
style_transfer --input /path/to/input_image --reference /path/to/reference_image --output /path/to/output_image

# or shortcut
style_transfer -i /path/to/input_image -r /path/to/reference_image -o /path/to/output_image
```

2. Use the example code.

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from style_transfer.libs import TransferFactory
from style_transfer.utils import ImageUtils


def main():
    # init image transfer
    transfer = TransferFactory.create("prism")

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

- fast_photo_style (FastPhotoStyle-Style algorithm)

## License

This project is licensed under the AGPLv3 License. This means you are free to use, modify, and distribute the code, but any modifications or services based on this project must be open-sourced under the same license. For commercial closed-source integration, please contact us for a commercial license.

See the [LICENSE](LICENSE) file for details.

## Contact Me

- Project Homepage: [GitHub Repository](https://github.com/XIAODUOLU/ChromaSoul)
- Issue Reports: [Issues](https://github.com/XIAODUOLU/ChromaSoul/issues)
- Email: lxd0705@163.com

---

**ChromaSoul** - Let every color find its soul mate ✨
