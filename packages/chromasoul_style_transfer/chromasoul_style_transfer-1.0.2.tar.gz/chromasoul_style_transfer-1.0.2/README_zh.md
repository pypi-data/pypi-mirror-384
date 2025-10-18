# StyleTransfer

[English](README.md) | **中文**

---

## 项目概述

StyleTransfer 提供了一套用于风格迁移任务的工具集。

## 安装

```bash
# 从 pypi 安装
pip install chromasoul_style_transfer

# 从发布版本安装
pip install chromasoul_style_transfer-{version}-py3-none-any.whl

# 从本地安装（不使用 uv）
pip install -e .

# 从本地安装（使用 uv）
uv sync
```

## 快速开始

1. 使用命令行工具

```bash
style_transfer --input /path/to/input_image --reference /path/to/reference_image --output /path/to/output_image --method fast_photo_style --verbose

# 或使用简写
style_transfer -i /path/to/input_image -r /path/to/reference_image -o /path/to/output_image -m fast_photo_style -v
```

2. 使用示例代码

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from style_transfer.libs import TransferFactory
from style_transfer.utils import ImageUtils


def main():
    # 初始化图像传输器
    transfer = TransferFactory.create("fast_photo_style")

    # 加载图像
    img_ref = ImageUtils.load_img("path/to/input_image")
    img = ImageUtils.load_img("path/to/reference_image")

    # 提取参考图像的风格特征
    transfer.extract(img_ref)
    # 将风格特征应用到目标图像
    img_tgt = transfer.transfer(img)

    # 目标目录会自动创建
    ImageUtils.save_img(img_tgt, "path/to/output_image")


if __name__ == "__main__":
    main()

```

## 可用方法

- fast_photo_style (FastPhotoStyle-Style algorithm)

## 许可证

本项目采用 AGPLv3 许可证。这意味着你可以自由地使用、修改和分发代码，但任何修改或基于本项目的服务都必须以相同的许可证开源。对于商业闭源集成有兴趣，请联系我们获取商业许可。

查看 [LICENSE](LICENSE) 文件了解详情。

## 联系我

- 项目主页: [GitHub Repository](https://github.com/XIAODUOLU/ChromaSoul)
- 问题反馈: [Issues](https://github.com/XIAODUOLU/ChromaSoul/issues)
- 邮箱: lxd0705@163.com

---

**ChromaSoul** - 让每一种色彩都找到属于它的灵魂伴侣 ✨
