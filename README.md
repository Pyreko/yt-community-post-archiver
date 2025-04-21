# yt-community-post-archiver

Archives YouTube community posts. Will try and grab the post's text content, images at
as large of a resolution as possible, polls, and some other various bits of metadata.
Works on members posts too.

Note this was initially written _really_ quickly, and might not work every time
(my Python is also only good at a scripting level). It is also a bit fragile,
and YT updates might break it. Feel free to let me know if it's broken, and if I
have the bandwidth I'll try and fix it.

## Usage

### From pypi

The script is available via [pypi](https://pypi.org/project/yt-community-post-archiver/):

1. [Install Python](https://www.python.org/downloads/).
2. Install via `pip` (or alternatives like [`pipx`](https://github.com/pypa/pipx)):

    ```shell
    pip install yt-community-post-archiver
    ```

3. Run `yt-community-post-archiver`. For example:

   ```shell
   yt-community-post-archiver "https://www.youtube.com/@PomuRainpuff/community"
   ```

   This will spawn a headless Chrome instance (that is, you won't see a Chrome window) and download all posts
   it can find from the provided page, and save text metadata + images in an automatically created folder called
   `archive-output` in the same directory the program was called in. Note this will take a while!

   For info on the options you can use, run with `--help`:

   ```shell
   yt-community-post-archiver --help
   ```

### From the wheel

From [Releases](https://github.com/Pyreko/yt-community-post-archiver/releases), you can install a wheel for this using Python.

1. [Install Python](https://www.python.org/downloads/).

2. Download one of the `.whl` files from [Releases](https://github.com/Pyreko/yt-community-post-archiver/releases)

3. Install the wheel file. For example, if the file you downloaded is called `yt_community_post_archiver-0.1.0-py3-none-any.whl`:

    ```shell
    pip install yt_community_post_archiver-0.1.0-py3-none-any.whl
    ```

4. Run `yt-community-post-archiver`. For example:

   ```shell
   yt-community-post-archiver "https://www.youtube.com/@PomuRainpuff/community"
   ```

   This will spawn a headless Chrome instance (that is, you won't see a Chrome window) and download all posts
   it can find from the provided page, and save text metadata + images in an automatically created folder called
   `archive-output` in the same directory the program was called in. Note this will take a while!

   For info on the options you can use, run with `--help`:

   ```shell
   yt-community-post-archiver --help
   ```

### From the repo

1. Clone the repo.

2. [Install Python](https://www.python.org/downloads/).

3. (Optional) Create and source a venv:

   ```shell
   python3 -m venv venv
   source venv/bin/activate
   ```

4. (Optional) Install `hatch` if you do not already have it:

   ```shell
   pip3 install hatch
   ```

5. Make sure the computer you're running this on has Chrome or Firefox, as it uses a browser to grab posts.

6. Run the archiver using `hatch run yt-community-post-archiver`. For example:

   ```shell
   hatch run yt-community-post-archiver "https://www.youtube.com/@PomuRainpuff/community"
   ```

   This will spawn a headless Chrome instance (that is, you won't see a Chrome window) and download all posts
   it can find from the provided page, and save text metadata + images in an automatically created folder called
   `archive-output` in the same directory the program was called in. Note this will take a while!

   For info on the options you can use, run with `--help`:

   ```shell
   yt-community-post-archiver --help
   ```

### Examples

For example, let's say I run:

```shell
yt-community-post-archiver "https://www.youtube.com/@IRyS/community" -o "output/testing" -m 1  
```

This runs the archiver, directed to `https://www.youtube.com/@IRyS/community`, saving to `output/testing`, and gets
a maximum of one post. If you are running from the repo, then replace `yt-community-post-archiver` with
`hatch run yt-community-post-archiver`. 

At the time of writing, this gives me two files that look like this - `post.json`:

```json
{
    "url": "https://www.youtube.com/post/Ugkxbg1AcEsx5spUWRjgtF8cvXDDgUIW1SFo",
    "text": "Carbonated Love Wallpaper for those who love the thumbnail :D Courtesy of kanauru!  Stream the song if you haven't yet!!\n\n⬇️FULL MV⬇️\nhttps://youtu.be/DjNNpw2x2dU?si=B0heA...",
    "images": [
        "https://yt3.ggpht.com/KfLmUOa22rydRozKY34zopeHP39EN0u_X5qLplQiKQd1i2rxxidrcG4RxH5s3ceGY9ql8VfIQgdA=s3840"
    ],
    "links": [
        "https://www.youtube.com/post/Ugkxbg1AcEsx5spUWRjgtF8cvXDDgUIW1SFo",
        "https://www.youtube.com/watch?v=DjNNpw2x2dU&t=0s",
    ],
    "is_members": false,
    "relative_date": "3 months ago",
    "approximate_num_comments": "111",
    "num_comments": "111",
    "num_thumbs_up": "7.3K",
    "poll": null,
    "when_archived": "2024-10-16 05:20:18.045639+00:00"
}
```

and an image file called `Ugkxljr0040TiZZTAVON7GBtrPz8jJEZQVP8-0.jpg`, containing the included image. Note that some
details may change throughout the versions; this document should be updated to reflect that though.

#### Set save location

If you want to set the save location, then use `-o`:

```shell
yt-community-post-archiver "https://www.youtube.com/@IRyS/community" -o "/home/me/my_save"
```

#### Logging in

You may want to provide a logged-in instance to this tool as this is the only way to get membership posts or certain details like poll vote percentages.
The tool supports two methods:

##### Use browser profile

I've found this way works a bit better from personal experience. You can re-use an existing browser profile that is
logged into your YouTube account to grab membership posts with the `-p` flag, where the path is where your user
profiles are located (for example, in Chrome, you can find this with `chrome://version`). For example:

```shell
yt-community-post-archiver -o output/ -p ~/.config/chromium/  "https://www.youtube.com/@WatsonAmelia/membership"
```

By default this will use the default profile name; if you need to override this then use `-n` as well.

##### Use cookies file

Another method is if you have a Netscape-format cookies file, which you can pass the path with `-c`:

```shell
yt-community-post-archiver "https://www.youtube.com/@WatsonAmelia/community" -c "/home/me/my_cookies_file.txt"
```

**Note that I've personally found this much flakier and occasionally fails in certain situations.** It should
work fine if you just want to get a few posts though, and already have a cookie file for things like
`ytarchive`.

#### Use Firefox instead of Chrome as the driver

The default driver is Chrome, but Firefox should work as well.

```shell
yt-community-post-archiver "https://www.youtube.com/@PomuRainpuff/community" -d "firefox"
```

### Notes

- Poll vote percentages can only be shown if you are logged in due to how vote results are only shown if the user has voted before.
  - If you have not voted on the poll before, the tool will temporarily vote for you to grab vote percentages, but will then try to undo the
    vote to avoid messing with anything, but this isn't perfect!

## Other

### How does this work?

This is just a typical Selenium/BeautifulSoup program, that's it. As such, it's simulating being a user and manually
copying + formatting all the data via a browser window. This is very evident if you disable headless mode,
and see all the action.
