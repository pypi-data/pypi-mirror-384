# ColorTransfer

[English](README.md) | **中文**

---

## 项目概述

ColorTransfer 提供了一套用于颜色迁移任务的工具集。

## 安装

```bash
# 从 pypi 安装
pip install chromasoul_color_transfer

# 从发布版本安装
pip install chromasoul_color_transfer-{version}-py3-none-any.whl

# 从本地安装（不使用 uv）
pip install -e .

# 从本地安装（使用 uv）
uv sync
```

## 快速开始

1. 使用命令行工具

```bash
color_transfer --input /path/to/input_image --reference /path/to/reference_image --output /path/to/output_image --method mean_std --verbose

# 或使用简写
color_transfer -i /path/to/input_image -r /path/to/reference_image -o /path/to/output_image -m mean_std -v
```

2. 使用示例代码

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from color_transfer.libs import TransferFactory
from color_transfer.utils import ImageUtils


def main():
    # 初始化图像传输器
    transfer = TransferFactory.create("mean_std")

    # 加载图像
    img_ref = ImageUtils.load_img("path/to/input_image")
    img = ImageUtils.load_img("path/to/reference_image")

    # 提取参考图像的颜色特征
    transfer.extract(img_ref)
    # 将颜色特征应用到目标图像
    img_tgt = transfer.transfer(img)

    # 目标目录会自动创建
    ImageUtils.save_img(img_tgt, "path/to/output_image")


if __name__ == "__main__":
    main()

```

## 可用方法

- mean_std
- lab (Reinhard)
- pdf (Probability Density Function)
- lhm (Linear Histogram Matching)
- pccm (Principal Component Color Matching)
- emd (Earth Mover’s Distance OT method)
- sinkhorn (Sinkhorn OT method)

## 许可证

本项目采用 AGPLv3 许可证。这意味着你可以自由地使用、修改和分发代码，但任何修改或基于本项目的服务都必须以相同的许可证开源。对于商业闭源集成有兴趣，请联系我们获取商业许可。

查看 [LICENSE](LICENSE) 文件了解详情。

## 联系我

- 项目主页: [GitHub Repository](https://github.com/XIAODUOLU/ChromaSoul)
- 问题反馈: [Issues](https://github.com/XIAODUOLU/ChromaSoul/issues)
- 邮箱: lxd0705@163.com

---

**ChromaSoul** - 让每一种色彩都找到属于它的灵魂伴侣 ✨
