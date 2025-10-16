import os
import msgspec
from .constants import LSP_CONFIG_FILE

class Package(msgspec.Struct):
    version: str

class Config(msgspec.Struct):
    packages: dict[str, Package]

    def commit(self):
        with open(LSP_CONFIG_FILE, "wb") as f:
            f.write(
                msgspec.json.encode(self)
            )

    def update_package(self, package_name, version):
        if package_name not in self.packages:
            self.packages[package_name] = Package(
                version=version
            )
        else:
            self.packages[package_name].version = version

def load_config() -> Config:
    if os.path.exists(LSP_CONFIG_FILE):
        with open(LSP_CONFIG_FILE, "rb") as f:
            return msgspec.json.decode(f.read(), type=Config)

    # Defaults
    return Config(
        packages={}
    )

