import os
import shutil
import urllib.request as request
import zipfile
import tarfile
import tempfile

def fetch(
    lsp_base_dir: str,
    url: str,
    dest: str,
    is_archive: str | None,
    is_nested: bool,
) -> str:
    """
    Fetches an archive or file from a URL, unpacks if the it's an archive, and
    returns a string pointing to the root dir for the install.
    """
    if (is_archive):
        if (is_archive == "auto"):
            frag = url.split(".")[-2:]
            if frag[0] == "tar":
                is_archive = ".".join(frag)
            else:
                is_archive = frag[1]
        download_dest = tempfile.gettempdir() \
            + "/lspinstaller/" \
            + dest \
            + f".{is_archive}"
        os.makedirs(
            tempfile.gettempdir() + "/lspinstaller/",
            exist_ok=True,
        )
    else:
        download_dest = os.path.join(
            lsp_base_dir,
            dest
        )
    os.makedirs(
        lsp_base_dir,
        exist_ok=True,
    )

    final_dir = os.path.join(
        lsp_base_dir,
        dest
    )
    print(f"Now downloading {url}...")
    [loc, response] = request.urlretrieve(
        url,
        download_dest
    )
    print(f"Downloaded to {loc}")

    if not is_archive:
        return loc

    if is_archive == "zip":
        print("Extracting .zip file...")
        with zipfile.ZipFile(loc) as archive:
            # TODO: this doesn't really account for root issues. clangd
            # extracts into clangd-<version>
            archive.extractall(
                os.path.join(
                    lsp_base_dir,
                    dest
                )
            )
    elif is_archive.startswith("tar"):
        print("Extracting .tar file...")
        with tarfile.open(loc, "r:*") as archive:
            archive.extractall(
                os.path.join(
                    lsp_base_dir,
                    dest
                )
            )

    elif is_archive is not None:
        raise RuntimeError("archive type not implemented yet")

    if is_archive is not None and is_nested:
        print("Unfucking nested folder")
        folder = os.path.join(
            final_dir,
            os.listdir(final_dir)[0]
        )
        assert os.path.isdir(folder), \
            f"You shouldn't be fucking with the folders manually (expected {folder} to be a folder"
        assert ".local/share" in folder, \
            f"rm -rf / safeguard triggered. Identified folder {folder}"
        shutil.copytree(
            folder,
            final_dir,
            dirs_exist_ok=True
        )
        shutil.rmtree(folder)

    print("Done")
    return final_dir
