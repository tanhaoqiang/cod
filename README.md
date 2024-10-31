# cod

Hobby kernel development is so miserable that everyone has to invent their own wheel, because there is no package manager.

`cod` is a tiny C source code package manager tailored to hobby kernel development:

- Works across Windows, MacOS and Linux
- Easy to Install
- Install dependency automatically

For example

```c
#include <awesome.h>

void kernel_main() {
  awesome_main();
}
```

At compiling, `cod` will try to find a package which provdes file `awesome.h`.

At linking, `cod` will try to find a package provides symbol `awesome_main`.

Now, let's reinvent the wheel, once and for all.

## Installation

```
pip install git+https://github.com/tanhaoqiang/cod.git
```

## License

cod is provided under [GNU Affero General Public License v3.0 only](https://spdx.org/licenses/AGPL-3.0-only.html). See [COPYING](COPYING]) for more information. Contributions to this project are accepted under the same license.

Individual files contain the following tag instead of the full license text.

    SPDX-License-Identifier: AGPL-3.0-only

This enables machine processing of license information based on the SPDX License Identifiers that are available here: http://spdx.org/licenses/
