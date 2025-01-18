# cod

Hobby kernel development is so miserable that everyone has to invent their own wheel, because there is no package manager.

`cod` is a tiny C source code package manager tailored to hobby kernel development:

- Works across Windows, MacOS and Linux
- Easy to Install
- Install dependency automatically

| CPython           | 3.6 | 3.7                | 3.8                | 3.9                | 3.10               | 3.11               | 3.12               | 3.13               |
| --                | --  | --                 | --                 | --                 | --                 | --                 | --                 | --                 |
| Windows AMD64     |     | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| macOS arm64       |     |                    |                    | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| macOS x86_64      |     | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| manylinux x86_64  |     | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| manylinux aarch64 |     | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| musllinux x86_64  |     | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| musllinux aarch64 |     | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |

## Installation

```
pip install git+https://github.com/tanhaoqiang/cod.git
```

Before wheel package uploaded to PyPI, run this command to install libsolv:

```
pip install -i "https://tanhaoqiang.github.io/simple" solv
```

## License

cod is provided under [GNU Affero General Public License v3.0 only](https://spdx.org/licenses/AGPL-3.0-only.html). See [COPYING](COPYING]) for more information. Contributions to this project are accepted under the same license.

Individual files contain the following tag instead of the full license text.

    SPDX-License-Identifier: AGPL-3.0-only

This enables machine processing of license information based on the SPDX License Identifiers that are available here: http://spdx.org/licenses/
