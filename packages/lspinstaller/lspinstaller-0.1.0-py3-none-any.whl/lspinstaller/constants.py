import os
from pathlib import Path

LSP_HOME = os.path.join(
    Path.home(),
    ".local/share/lsp"
)

LSP_CONFIG_FILE = os.path.join(
    LSP_HOME,
    "config.json"
)
