# yt-community-post-archiver

Archives YouTube community posts. Will try and grab the post's text content, images at
as large of a resolution as possible, polls, and some other various metadata.

Note this was written _really_ quickly, and might not work every time (my Python is also
a bit shit). It is also a bit fragile, and YT updates might break it. Feel free to let
me know if it's broken, and if I have the bandwidth I'll try and fix it.

## Usage

1. Clone the repo.

2. (Optional) Create and source a venv:

   ```shell
   python3 -m venv venv
   source venv/bin/activate
   ```

3. (Optional) Download the dependencies in `requirements.txt` if you do not already have them:

   ```shell
   pip3 install -r requirements.txt
   ```

4. Make sure the computer you're running this on has Chrome or Firefox, as it uses a browser to grab posts.

5. Run `archiver.py`. For example:

   ```shell
   python3 archiver.py "https://www.youtube.com/@PomuRainpuff/community"
   ```

   This will spawn a headless Chrome instance (that is, you won't see a Chrome window) and download all posts
   it can find from the provided page, and save text metadata + images in an automatically created folder called
   `archive-output` in the same directory the program was called in. Note this will take a while!

   For info on the options you can use, run with `--help`:

   ```shell
   python3 archiver.py --help
   ```

### Set save location

If you want to set the save location, then use `-o`:

```shell
python3 archiver.py "https://www.youtube.com/@IRyS/community" -o "/home/me/my_save"
```

### Membership posts

Membership posts are a bit trickier and require having some way of showing YouTube that you're a member. This tool currently supports two methods:

#### Use browser profile

You can re-use an existing browser profile that is logged into your YouTube account to grab membership posts with the `-p` flag, where the path is where
your user profiles are located (for example, in Chrome, you can find this with `chrome://version`). For example:

```shell
venv/bin/python archiver.py -o output/ -p ~/.config/chromium/  "https://www.youtube.com/@WatsonAmelia/membership"
```

By default this will use the default profile name; if you need to override this then use `-n` as well.

#### Use cookies file

Another method is if you have a Netscape-format cookies file, which you can pass the path with `-c`:

```shell
python3 archiver.py "https://www.youtube.com/@WatsonAmelia/community" -c "/home/me/my_cookies_file.txt"
```

Note that I've personally found this much flakier and occasionally fails in certain situations.

### Use Firefox instead of Chrome as the driver

The default driver is Chrome, but Firefox should work as well.

```shell
python3 archiver.py "https://www.youtube.com/@PomuRainpuff/community" -d "firefox"
```

## Notes

- Poll vote percentages can only be shown if you are logged in due to how vote results are shown by YouTube.
  - If you have not voted on the poll before, the tool will temporarily vote for you to grab vote percentages, but will then try to undo the vote to avoid messing with anything, but this isn't perfect!
