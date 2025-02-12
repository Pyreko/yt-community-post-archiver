import json
import os
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.parse import parse_qs
from pathlib import Path

import filetype
import requests

class PollEntry:
    def __init__(self, s: str) -> None:
        split = s.splitlines()

        try:
            self.option = split[0]
        except:
            self.option = None

        try:
            self.percentage = int(split[1].split("%")[0])
        except:
            self.percentage = None


@dataclass
class Poll:
    entries: list[PollEntry]
    total_votes: str | None


def get_post_id(url: str) -> str:
    return parse_qs(urlparse(url).query)["lb"][0]


@dataclass
class Post:
    """
    Represents a post's metadata.
    """

    url: str
    text: str
    images: list[str]
    links: list[str]
    is_members: bool
    relative_date: str
    approximate_num_comments: str | None
    num_comments: str | None
    num_thumbs_up: str | None
    poll: Poll | None
    when_archived: str

    def save(self, output_dir: str):
        post_id = get_post_id(self.url)
        dir = Path(os.path.join(output_dir, post_id))

        if not dir.exists():
            try:
                dir.mkdir(parents=True, exist_ok=True)
            except Exception as ex:
                print(f"err: couldn't make directory for post at {dir} - {ex}")
                return

        try:
            data_path = os.path.join(dir, "post.json")
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(
                    self.__dict__,
                    f,
                    ensure_ascii=False,
                    indent=4,
                    default=lambda o: o.__dict__,
                    skipkeys=True,
                )
        except:
            print(f"err: couldn't save data dump at {data_path}")

        for itx, image in enumerate(self.images):
            try:
                img_data = requests.get(image).content
                img_format = filetype.guess(img_data)
                img_extension = img_format.extension if img_format else "png"
                img_name = f"{post_id}-{itx}.{img_extension}"
                img_path = os.path.join(dir, img_name)

                if not os.path.exists(img_path):
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                else:
                    # print(f"Skipping saving image at {img_path} as it's already been saved.")
                    pass
            except:
                print(f"err: couldn't save image `{image}` dump at {img_path}")
