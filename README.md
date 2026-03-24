# yt-community-post-archiver

Archives YouTube community posts. Will try and grab the post's text content, images at as large of a resolution as possible, polls, and some other various bits of metadata. Works on members posts too if you're logged in/using cookies.

Note that:

- This was originally written very quickly to archive things in time for something, so it is somewhat scuffed.
- The scraping is also done in a way which is somewhat fragile, and may break easily as YouTube updates things.

Feel free to report problems or suggest features, though as a disclaimer,
_I may not have the bandwidth or interest to tackle all reported issues_.
PRs are always welcome, though!

## Usage

### From PyPI

The script is available via [pypi](https://pypi.org/project/yt-community-post-archiver/):

1. [Install Python](https://www.python.org/downloads/).
2. Install via `pip` (or alternatives like [`pipx`](https://github.com/pypa/pipx)):

    ```shell
    pip install yt-community-post-archiver
    ```

3. Run `yt-community-post-archiver`. For example:

   ```shell
   yt-community-post-archiver "https://www.youtube.com/@PomuRainpuff/posts"
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
   yt-community-post-archiver "https://www.youtube.com/@PomuRainpuff/posts"
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

4. (Optional) Install `uv` if you do not already have it:

   ```shell
   pip3 install uv
   ```

5. Make sure the computer you're running this on has Chrome or Firefox, as it uses a browser to grab posts.

6. Run the archiver using `uv run yt-community-post-archiver`. For example:

   ```shell
   uv run yt-community-post-archiver "https://www.youtube.com/@PomuRainpuff/posts"
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
yt-community-post-archiver "https://www.youtube.com/@IRyS/posts" -o "output/testing" -m 1  
```

This runs the archiver, directed to `https://www.youtube.com/@IRyS/posts`, saving to `output/testing`, and gets
a maximum of one post. If you are running from the repo, then replace `yt-community-post-archiver` with
`uv run yt-community-post-archiver`.

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
yt-community-post-archiver "https://www.youtube.com/@IRyS/posts" -o "/home/me/my_save"
```

#### Logging in

You may want to provide a logged-in instance to this tool as this is the only way to get membership posts or certain details like poll vote percentages. The tool supports a few methods.

##### Using a browser profile

I've found this way works a bit better from personal experience. You can re-use an existing browser profile that is
logged into your YouTube account to grab membership posts with the `-p` flag, where the path is where your user
profiles are located (for example, in Chrome, you can find this with `chrome://version`). For example:

```shell
yt-community-post-archiver -o output/ -p ~/.config/chromium/  "https://www.youtube.com/@WatsonAmelia/membership"
```

By default this will use the default profile name; if you need to override this then use `-n` as well. **I highly recommend
creating a new profile for using this tool (whether it's Chrome or Firefox) just so it doesn't accidentally delete some tabs or something**.

##### Using a cookies file

Another method is if you have a Netscape-format cookies file, which you can pass the path with `-c` / `--cookies`:

```shell
yt-community-post-archiver "https://www.youtube.com/@WatsonAmelia/posts" -c "/home/me/my_cookies_file.txt"
```

You can see how to get a cookies file by following [the instructions on how to do so from yt-dlp](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp).

**Note that from personal experience, this sometimes breaks, so your mileage may vary.**

Also note that when using this from WSL, avoid reusing a Windows Chrome profile path (`/mnt/c/.../User Data`) with `-p`. Linux Chrome/Chromium in WSL does not reliably read/decrypt Windows profile data. Use a Linux profile directory
instead (for example `~/.config/google-chrome`) or use a cookie file.

##### Using remote debugging to connect to a running instance

You can also start Chrome/Chromium with a remote debugging port, and connect this program to it. For example:

1. Start up Chrome/Chromium with a remote debugging port:

    ```shell
    chromium --remote-debugging-port=9222 --profile-directory="Profile 1"
    ```

2. Start `yt-community-post-archiver`:

    ```shell
    yt-community-post-archiver "https://www.youtube.com/@kaminariclara/posts" -o "output" --remote-debugging-port 9222
    ```

#### Use Firefox instead of Chrome as the driver

The default driver is Chrome, but Firefox should work as well.

```shell
yt-community-post-archiver "https://www.youtube.com/@PomuRainpuff/posts" -d "firefox"
```

## Other

### Polls

Poll vote percentages can only be shown if you are logged in, due to how vote results are only shown if the user has voted before.

This also means that if you are logged in but have not voted on the poll before in a post, the tool will temporarily vote for you so it can see the vote percentages. It will try to remove the vote if it had to do this to avoid affecting anything, though be aware that this may sometimes fail!

### How does this work?

This is just a typical Selenium/BeautifulSoup program, that's it. As such, it's simulating being a user and manually
copying + formatting all the data via a browser window. This is very evident if you disable headless mode,
and see all the action.
