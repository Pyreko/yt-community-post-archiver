import os
from typing import List, Optional
import requests
import json
from dataclasses import dataclass


class PollEntry:
    def __init__(self, s: str) -> None:
        split = s.splitlines()

        try:
            self.option = split[0]
        except:
            self.option = "N/A"

        try:
            self.percentage = int(split[1].split("%")[0])
        except:
            self.percentage = "N/A"


@dataclass
class Post:
    """
    Represents a post's metadata.
    """

    url: str
    text: str
    images: List[str]
    links: List[str]
    is_members: bool
    relative_date: str
    num_comments: Optional[str]
    num_thumbs_up: Optional[str]
    poll: Optional[List[PollEntry]]

    def save(self, output_dir: str):
        id = self.url.split("/")[-1]
        dir = os.path.join(output_dir, id)

        # print(f"Trying to save `{id}` at `{dir}`...")

        if not os.path.exists(dir):
            try:
                os.mkdir(dir)
            except:
                print(f"err: couldn't make directory at {dir}")
                return

        try:
            data_path = os.path.join(dir, "post.txt")
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(self.__dict__, f, ensure_ascii=False, indent=4, default=lambda o: o.__dict__, skipkeys=True)
        except:
            print(f"err: couldn't save data dump at {data_path}")

        for itx, image in enumerate(self.images):
            try:
                img_name = f"{id}-{itx}.png"
                img_path = os.path.join(dir, img_name)

                if not os.path.exists(img_path):
                    img_data = requests.get(image).content
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                else:
                    # print(f"Skipping saving image at {img_path} as it's already been saved.")
                    pass
            except:
                print(f"err: couldn't save image `{image}` dump at {img_path}")
