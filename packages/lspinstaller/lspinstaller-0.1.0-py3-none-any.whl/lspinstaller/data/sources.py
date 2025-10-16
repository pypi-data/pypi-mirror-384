from dataclasses import dataclass
from enum import Enum

from lspinstaller.resolver.arch import Arch, simplified_arch, simplified_arch

from lspinstaller.resolver.arch import Arch

"""
# Syntax
## Root
```
"package name": { data object }
```

The package name is also used for folders in some cases, so make sure the
package name is plain text!

## Data objects

Data objects can have the following main keys:

* github
* npm
* binary
    * The binary spec describes a binary file. Its exact meaning depends on the
      main provider
    * Must be included when using any of  these providers: "github".

### OSDict

OSDicts are a special class of dicts that refer to dicts in the following
format:
```python
d = {
    "windows": <transform>,
    "linux": <transform>
}
```

The keys always line up with the value of `${os}`, which will be described in
the special values section.


### `github`

The github object contains the following keys:
* `fragment`: must be in the format `user/repo`

In addition, the separate `binary` object must be specified.

### `npm`

The npm object contains the following keys:
* `package`: the package name as it's used on npm

### `binary`

The binary object contains the following keys:
* `pattern`: required when using `github` or another provider that finds
  multiple files. Otherwise optional. Mutually exclusive with `url`
* `url`: required when the object is used with a source that's only used for
  the version. See kotlin-lsp for an example. Mutually exclusive with `pattern`
* `link`: describes which files to symlink to the special bin directory.
  Syntax: `"file name in lsp/bin": "filename relative to download root"`
  Currently only used to chmod executables, may be turned into a list if
  symlinking proves undoable.
* `archive`: the archive type. Required. Accepted values: "zip", ".tar[.*]", or
  "auto" to infer from the URL. Only set archive to auto if the URL in all
  configurations ends with the archive name.
* `is_nested`: whether or not the archive is nested, meaning the main archive
  has an inner folder. Clangd, for example, has this, where extracting the
  clangd archive extracts another clangd-<version> folder. Clangd therefore
  sets this to true. kotlin-lsp, on the other hand, just has its bin directory
  immediately after extraction, so it sets false. Required if `archive` is set

The binary object is special, and will never be executed standalone. It exists
to consume data from other providers to actually do the install.

### `arch`

Used to describe which architecture variants are supported. This is only
required to use the `${arch}` key.

It has the following keys:

* `supported`: An OSDict where the transform is supported architectures.
* `parser`: A function that turns the Arch enum into strings. See
  lspinstaller/resolver/arch.py for common implementations.

## Special values

In some strings, there are special values. These are in the format `${key}`,
and the currently recognised values are:

* `os`: One of the literals `windows` or `linux`
* `version`: the version as determined by a provider. Note that for versions
  including the `v` prefix, the `v` is stripped and must be included literally
  in the resulting string.
* `arch`: requires the `arch` key described in the previous section
"""
# TODO: need a better way to manage the logic for some of these variables,
# because they are not universally portable. Just with operating systems,
# upper-case first letter does occur in some projects. Some also abbreviate
# windows. Can probably sneak in more lambdas to mitigate this, but  that
# requires passing the whole data object  to the lambda, which is just a mess.
# Lambdas in python are also fairly shit, so that wouldn't be pretty. Maybe
# there's a light-weight templating language that makes sense to use?
sources = {
    "clangd": {
        "github": {
            "fragment": "clangd/clangd",
        },
        "binary": {
            "pattern": "clangd-${os}-${version}.zip",
            "link": {
                "clangd": "bin/clangd"
            },
            "archive": "auto",
            "is_nested": True
        }
    },
    "tsserver": {
        "npm": {
            "package": "typescript-language-server",
            "deps": [
                # We need typescript's tsserver to link to for yegappan/lsp to
                # work reliably. I'm pretty sure coc.nvim does this
                # automatically as well
                "typescript",
            ],
            "bin": "typescript-language-server"
        }
    },
    "pyright": {
        "npm": {
            "package": "pyright",
            "bin": "pyright"
        }
    },
    "kotlin-lsp": {
        "github": {
            "fragment": "Kotlin/kotlin-lsp"
        },
        "binary": {
            "url": "https://download-cdn.jetbrains.com/kotlin-lsp/${version}/kotlin-${version}.zip",
            "link": {
                "kotlin-lsp": "kotlin-lsp.sh"
            },
            "archive": "auto",
            "is_nested": False
        },
        "version_parser": lambda raw : raw[raw.index("v") + 1:]
    },
    "luals": {
        "github": {
            "fragment": "luals/lua-language-server"
        },
        "binary": {
            "pattern": {
                "linux": "lua-language-server-${version}-linux-${arch}.tar.gz",
                "windows": "lua-language-server-${version}-win32-${arch}.zip"
            },
            "link": {
                "lua-language-server": "bin/lua-language-server"
            },
            "archive": "auto",
            "is_nested": False
        },
        "arch": {
            "supported": {
                "windows": [Arch.X86_64],
                "linux": [Arch.X86_64, Arch.ARM64]
            },
            "parser": simplified_arch,
        },
    }
}
