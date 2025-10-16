from dataclasses import dataclass
import enum
import os
import stat
import subprocess
import shutil
import platform
from lspinstaller.config import Config
from lspinstaller.constants import LSP_HOME
from lspinstaller.data import sources
from lspinstaller.resolver.arch import Arch, Arch, resolve_arch
from lspinstaller.resolver.arch import resolve_arch
from lspinstaller.resolver.util.github import default_version_parser, get_release_info
from lspinstaller.resolver.util.fetch import fetch

@dataclass
class Data:
    version: str
    os: str

def init_data(version: str):
    return Data(
        version=version,
        os=platform.system().lower()
    )

def parse_special(value, data: Data) -> str:
    if not isinstance(value, str):
        return value(data)
    else:
        # TODO: This will not scale well. Do not add more fields this way;
        # write a proper replacement engine instead.
        value = value.replace("${os}", data.os)
        value = value.replace("${version}", data.version)

        return value

def resolve(package_name, spec, config: Config):
    assert spec is not None
    os.makedirs(
        os.path.join(LSP_HOME, "bin"),
        exist_ok=True
    )
    if "removed" in spec:
        print(
            f"{package_name} has been removed, and will not be updated or installed"
        )
    elif "github" in spec:
        release = get_release_info(
            spec["github"]["fragment"],
            spec.get("version_parser", default_version_parser)
        )
        binary = spec["binary"]
        assert binary is not None, \
            f"misconfigured binary object for {package_name}"

        if "url" in binary:
            url = binary["url"]
            url = parse_special(
                url,
                init_data(
                    release.tag_name
                )
            )
        else:
            pattern = binary["pattern"]
            assert pattern is not None
            data = init_data(
                release.tag_name
            )
            if isinstance(pattern, dict):
                pattern  = pattern[data.os]

            pattern = parse_special(
                pattern,
                data,
            )

            if "arch" in spec:
                arch_spec = spec["arch"]
                arch: Arch = resolve_arch()
                if arch not in arch_spec["supported"][data.os]:
                    raise RuntimeError(
                        f"{package_name} is not supported on {arch}. "
                        f"Supported: {arch_spec['supported']}"
                    )

                pattern = pattern.replace("${arch}", arch_spec["parser"](arch))
            url = None
            for asset in release.assets:
                if asset.name == pattern:
                    print(f"Resolved asset to {asset.name}")
                    url = asset.url
                    break
            else:
                print(f"Failed to resolve asset for {package_name}")
                exit(-1)

        # Should never throw, but required because url is str | None due to the
        # = None assignment in the previous if statement
        assert url is not None
        root = fetch(
            LSP_HOME,
            url,
            package_name,
            binary["archive"],
            binary.get("is_nested", False)
        )

        for (dest_name, src_path) in binary["link"].items():

            full_src = os.path.join(root, src_path)
            full_dest = os.path.join(
                LSP_HOME,
                "bin",
                dest_name
            )
            if platform.system() != "Windows":
                print("Chmoding...")
                os.chmod(
                    full_src,
                    mode=os.stat(full_src).st_mode | stat.S_IEXEC
                )
            # TODO: symlinking breaks clangd
            # print(f"Symlinking {full_src} -> {full_dest}")
            # if os.path.exists(full_dest):
                # os.remove(full_dest)
            # os.link(
                # full_src, full_dest
            # )


        config.update_package(package_name, release.tag_name)
        return release.tag_name
    elif "npm" in spec:
        args = ["npm", "install", spec["npm"]["package"]]
        # TODO: There has to be a shorthand for this
        if "deps" in spec["npm"]:
            for dep in spec["npm"]["deps"]:
                args.append(dep)

        subprocess.run(
            args,
            cwd=LSP_HOME
        )
        return None

def do_update(config: Config):
    if os.path.exists(
        os.path.join(
            LSP_HOME,
            "node_modules"
        )
    ):
        # Pretty sure this should just work:tm:, since npm install uses the ^
        # notation, which should work with npm update:
        # https://stackoverflow.com/a/19824154
        subprocess.run(
            ["npm", "update"],
            cwd=LSP_HOME
        )

    for package in config.packages:
        dest = os.path.join(
            LSP_HOME,
            package
        )

        # Nuke the existing tree just in case
        if os.path.exists(dest):
            shutil.rmtree(
                dest
            )

        new_version = resolve(
            package,
            sources[package],
            config
        )
    config.commit()
