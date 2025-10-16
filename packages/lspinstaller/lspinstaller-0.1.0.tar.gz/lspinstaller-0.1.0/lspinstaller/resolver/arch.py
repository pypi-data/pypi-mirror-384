from enum import Enum
import platform

class Arch(Enum):
    X86 = 0
    X86_64 = 1
    # TODO: I know too little about ARM right now to sanely implement 
    # the rest of the enums.
    ARM64 = 16

def resolve_arch() -> Arch:
    raw_arch = platform.machine()

    if (raw_arch in ("x86_64", "AMD64")):
        return Arch.X86_64
    elif (raw_arch in ("x86", "i386", "i686")):
        return Arch.X86
    elif (raw_arch in ("arm64")):
        return Arch.ARM64
    else:
        raise RuntimeError(
            f"{raw_arch} has not yet been implemented/correctly identified"
        )

def full_arch(arch: Arch):
    return {
        Arch.X86: "x86",
        Arch.X86_64: "x86_64",
        Arch.ARM64: "arm64"
    }[arch]

def simplified_arch(arch: Arch):
    return {
        Arch.X86: "x86",
        Arch.X86_64: "x64",
        Arch.ARM64: "arm64"
    }[arch]
