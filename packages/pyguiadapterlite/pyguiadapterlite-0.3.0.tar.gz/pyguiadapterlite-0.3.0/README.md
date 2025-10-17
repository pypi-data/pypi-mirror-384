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

`tkinter`另一个潜在的优势并非技术上的，而是法律层面的，相比Qt的几个Python binding， `tkinter`有着更加宽松的许可证，这意味着，
在法律上，它更加 “安全”。

当然，`tkinter`相比Qt也有其劣势，主要在于功能相对简单，高级控件匮乏，外观样式不够现代化。但是，对于开发一个工具类的应用来说，`tkinter`提供
的能力已经足够了。

`PyGUIAdapter`和`PyGUIAdapterLite`的定位与另一个开源项目[`Gooey`](https://github.com/chriskiehl/Gooey)类似，都致力于为Python程序员
提供一种极其简单的方式，为其Python程序创建一个相对整洁、美观、易用的图形用户界面，同时，允许程序员无需具备GUI编程的相关知识。

> 当然，如果程序员需要扩展`PyGUIAdapter[Lite]`，则需要了解一些GUI编程的知识。

`PyGUIAdapter[Lite]`和[`Gooey`](https://github.com/chriskiehl/Gooey)虽然目标类似，但二者在设计思想、实现机制上存在根本性的差异。

`Gooey`是面向命令行的，它要求程序员首先通过argparse定义命令行参数，然后再将命令行参数翻译为GUI界面。而`PyGUIAdapter[Lite]`则是面向函数的，
在我看来，函数本身就已经为创建GUI界面提供了基本但必要的信息。因此，`PyGUIAdapter[Lite]`以函数为基本单元，通过分析函数元信息等 ，
自动将函数翻译为用户界面。


总的来说，`PyGUIAdapter[Lite]`适用于工具类应用的开发，如果你刚好需要为你的小工具创建一个图形用户界面，但又不想在GUI代码上投入太多精力，那么，你可以
尝试一下`PyGUIAdapter[Lite]`。

> 尽管`PyGUIAdapterLite`已经尽可能在接口上与`PyGUIAdapter`保持一致，但是由于种种原因，无法保证二者接口的完全兼容。不过由于`PyGUIAdapterLite`
> 本身非常简单，因此，不要求用户对`PyGUIAdapter`有所了解，只需要简单阅读文档，就可以上手使用。

## 1. 安装

`PyGUIAdapterLite`的wheel包已经发布到`PyPI`上，可以直接通过pip安装：

```bash
> pip install pyguiadapterlite
```

如果要体验最新功能，可以从GitHub上clone整个项目，然后自行构建:

> `PyGUIAdapterLite`使用了`poetry`作为项目管理和构建工具，因此需要先安装`poetry`。

``` bash
> git clone https://github.com/zimolab/PyGUIAdapterLite.git
> cd PyGUIAdapterLite/
> poetry install
> poetry build
```

## 2. 快速入门

使用`PyGUIAdapterLite`非常简单，首先准备好需要翻译为GUI界面的函数。以下面这个最简单的函数为例：

```pycon
def sum_two_numbers(a: int, b: int) -> int:
    """
    计算两个整数之和。
    
    Args:
        a: 第一个整数。
        b: 第二个整数。
        
    Returns:
        两个整数之和。
    """
    return a + b
```

然后，创建`GUIAdapter`示例，调用`GUIAdapter.add()`将上述函数添加到实例中，最后调用`GUIAdapter.run()`将该函数翻译为GUI界面：

```python

if __name__ == "__main__":
    from pyguiadapterlite import GUIAdapter

    adapter = GUIAdapter()
    adapter.add(sum_two_numbers)
    adapter.run()
```
完整代码如下：

```python
def sum_two_numbers(a: int, b: int) -> int:
    """
    计算两个整数之和。
    
    Args:
        a: 第一个整数。
        b: 第二个整数。
        
    Returns:
        两个整数之和。
    """
    return a + b

if __name__ == "__main__":
    from pyguiadapterlite import GUIAdapter

    adapter = GUIAdapter()
    adapter.add(sum_two_numbers)
    adapter.run()
```

运行如上代码，`PyGUIAdapterLite`将生成如下界面：

<img src="./docs/code_snippet_1.gif" height="50%"/>

上述示例虽然非常简单，但为我们展示了`PyGUIAdapterLite`的一些基本特性：

- `PyGUIAdapterLite`为函数的每一个参数创建一个输入控件，输入控件的类型取决于参数的类型，而参数的类型通常通过其typing hint进行推导。`PyGUIAdapterLite`
会读取和分析函数参数的类型注解信息，并自动匹配适合的输入控件。
> 也可以在不使用类型标准的情况下为参数指定输入控件类型，这涉及到`GUIAdapterLite`的进阶用法。并且，无论在何种情况下，均推荐用户使用类型注解来描述函数参数。
> 事实证明，这样做可以大大提高代码的可读性和可维护性。

- `PyGUIAdapterLite`也会读取和分析函数的`docstring`，并自动生成对应的帮助信息。帮助信息包含两种类型，一种是函数的描述信息，另一种是函数的每个参数
的描述信息。对于函数的描述信息，`PyGUIAdapterLite`会将其显示在单独的Tab页中，而对于参数的描述信息，`PyGUIAdapterLite`会将其显示在每个参数
对应的输入控件的旁边，以`tooltip`的形式进行展示。

> 函数和参数的描述信息也可以通过其他方式进行指定，后面我们将说明这一点。

- `PyGUIAdapterLite`会自动生成一个“Execute”按钮，用户点击该按钮后，`PyGUIAdapterLite`会调用函数，并将用户输入的值作为参数传递给函数。
同时，`PyGUIAdapterLite`会捕获函数的返回值，默认情况下，`PyGUIAdapterLite`会弹窗显示函数的返回值，并将其显示窗口的模拟终端界面。

> 通过配置，可以改变上述行为，比如，禁用弹窗显示返回值，或者禁止自动打印返回值。这些配置项将在后面详细介绍。


`PyGUIAdapterLite`已经为内置基本类型创建了对应的输入控件，包括`int`、`float`、`str`、`bool`、`enum`等，下面是一个综合的示例，向你展示，
这些基本类型对应的输入控件默认情况下是什么样的：

```python
import time
from enum import Enum


class FileOperation(Enum):
    """文件操作类型"""

    COPY = "copy"
    MOVE = "move"
    RENAME = "rename"


class HashAlgorithm(Enum):
    """哈希算法类型"""

    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"


def batch_process_files(
    source_dir: str,
    target_dir: str = "",
    file_pattern: str = "*",
    operation: FileOperation = FileOperation.COPY,
    new_name_pattern: str = "",
    calculate_hash: bool = False,
    hash_algorithm: HashAlgorithm = HashAlgorithm.MD5,
    create_backup: bool = True,
    overwrite_existing: bool = False,
    file_size_limit: int = 100,
) -> str:
    """
    批量处理文件的工具函数

    这个函数可以批量复制、移动或重命名文件，支持文件过滤、哈希计算等功能。
    非常适合用于文件整理、备份或数据迁移任务。

    Args:
        source_dir: 源目录路径（必须存在）
        target_dir: 目标目录路径（移动/复制操作时必需）
        file_pattern: 文件匹配模式，如 "*.txt"、"image_*.jpg"
        operation: 文件操作类型：复制、移动或重命名
        new_name_pattern: 重命名模式，如 "file_{index}.{ext}"（重命名操作时使用）
        calculate_hash: 是否计算文件哈希值
        hash_algorithm: 选择哈希算法
        create_backup: 是否创建备份（在目标目录创建backup文件夹）
        overwrite_existing: 是否覆盖已存在的文件
        file_size_limit: 文件大小限制（MB），超过此大小的文件将被跳过

    Returns:
        处理结果的摘要信息
    """
    uprint(f"源目录：{source_dir}")
    uprint(f"目标目录：{target_dir}")
    uprint(f"文件匹配模式：{file_pattern}")
    uprint(f"文件操作类型：{operation.value}")
    uprint(f"新文件名模式：{new_name_pattern}")
    uprint(f"是否计算哈希值：{calculate_hash}")
    uprint(f"哈希算法：{hash_algorithm.value}")
    uprint(f"是否创建备份：{create_backup}")
    uprint(f"是否覆盖已存在文件：{overwrite_existing}")
    uprint(f"文件大小限制：{file_size_limit} MB")

    uprint("开始处理...")
    # 假装在处理
    time.sleep(3)
    uprint("处理完成！")
    return "处理完成！"


if __name__ == "__main__":
    from pyguiadapterlite import GUIAdapter, uprint

    adapter = GUIAdapter()
    adapter.add(batch_process_files)
    adapter.run()
```

<img src="./docs/code_snippet_2.gif" height="50%"/>

上述示例展示了`PyGUIAdapterLite`对基本类型参数的支持，同时，也展示了`uprint()`函数的用法，这个函数与内置的`print()`类似，用于输出一些信息，
但与`print()`不同的是，该函数会将信息输出到窗口的模拟终端界面，而非输出到标准输出。

> `uprint()`(或者说窗口的模拟终端界面)对`ANSI`提供有限支持，支持一些颜色和样式，但不支持全部特性。

同时，上述代码还隐藏这一个细节，注意到用户函数`batch_process_files()`中有一行`time.sleep(3)`，这是在模拟耗时操作，当程序在运行到这一行时，
我们的界面并没有冻结，这表明，在默认实现中，`PyGUIAdapterLite`将用户函数放在另一个线程中运行，而非在主线程（即UI线程）中，这避免了耗时操作阻塞UI线程。

> 在一些IO密集型的任务中，用户可能仍然会遭遇UI界面卡顿的问题，从我的实践而言，一个可能解决的方法是在用户函数中使用多进程（multiprocessing）。
> 但这超出了本文的讨论范围，感兴趣的读者可以自行研究。

## 3. 进阶用法

> TODO

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