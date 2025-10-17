# PyGUIAdapterLite

## 0. 一些背景

`PyGUIAdapterLite`是我另一个开源项目[`PyGUIAdapter`](https://github.com/zimolab/PyGUIAdapterLite)的Lite版本，
在保持基本功能一致的情况下，聚焦于“轻量化”这一目标。因此，它去除了`PyGUIAdapter`中最重量级的外部依赖——`Qt`，
使用了更轻量级的`tkinter`作为GUI后端。

使用`tkinter`最大的好处是， 它是Python的标准GUI库，绝大多数情况下随Python一起安装，不需要任何额外的步骤，这也意味着基本上也无需考虑它与python的兼容性
以及跨平台的问题。

> 部分Linux发行版预装的Python版本可能没有包含tkinter， 此时需要手动安装，但这非常简单，以Ubuntu-based发行版为例，可以运行类似以下命令来安装tkinter：
> 
> ```
> sudo apt-get install python3-tk
> ```
>

另外，`tkinter`非常轻量，无论是生成的可执行文件体积还是运行时的内存占用，相比于Qt（无论是`PyQt`还是`PySide`），都要小很多。

`tkinter`另一个潜在的优势不是技术上的，而是法律层面的，相比Qt的几个Python binding， `tkinter`有着更加宽松的许可证。

当然，`tkinter`相比也有其劣势，


## 1. 安装

`PyGUIAdapterLite`的wheel包已经发布到`PyPI`上，可以直接通过pip安装：

```bash
> pip install PyGUIAdapterLite
```

如果要体验最新功能，可以从GitHub上clone整个项目，然后自行构建:

> `PyGUIAdapterLite`使用了`poetry`作为项目管理和构建工具，因此需要先安装`poetry`。

``` bash
> git clone https://github.com/zimolab/PyGUIAdapterLite.git
> cd PyGUIAdapterLite/
> poetry install
> poetry build
```


## 第三方库许可

本项目使用了以下优秀的开源库：

- **IconPark** 
  - 用途：使用了IconPark部分图标，版权归IconPark所有。
  - 许可：Apache License 2.0
  - 许可证文件：`licenses/IconPark-LICENSE.txt`
  - 项目地址：https://github.com/bytedance/IconPark

- **tomlkit**
  - 用途：解析和生成TOML格式的配置文件。
  - 许可：MIT License
  - 许可证文件：`licenses/tomlkit-LICENSE.txt`
  - 项目地址：https://github.com/python-poetry/tomlkit/

- **docstring_parser**
  - 用途：解析Python文件的docstring。
  - 许可：MIT License
  - 许可证文件：`licenses/docstring_parser-LICENSE.md`
  - 项目地址：https://github.com/rr-/docstring_parser