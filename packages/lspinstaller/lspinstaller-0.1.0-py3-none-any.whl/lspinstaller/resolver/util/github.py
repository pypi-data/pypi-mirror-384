from dataclasses import dataclass
import requests
import msgspec

@dataclass
class ReleaseAsset:
    name: str
    url: str

@dataclass
class ReleaseInfo:
    tag_name: str
    release_name: str
    assets: list[ReleaseAsset]

def default_version_parser(raw: str):
    return raw[0 if raw[0] != "v" else 1:]

def get_release_info(repo_ref: str, version_parser = default_version_parser) -> ReleaseInfo:
    # TODO: should probably add an option for an API key here, but I don't feel
    # like doing that right now
    res = requests.get(
        "https://api.github.com/repos/{}/releases/latest".format(repo_ref)
    )
    if (res.status_code >= 400):
        print("GitHub says no:", res.text)
        exit(-2)

    json = msgspec.json.decode(res.text)
    return ReleaseInfo(
        tag_name = version_parser(json["tag_name"]),
        release_name = json["name"],
        assets = [
            ReleaseAsset(
                asset["name"],
                # the `url` field just returns a JSON response, and not the
                # actual file content.
                asset["browser_download_url"],
            ) for asset in json["assets"]
        ]
    )
