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
python3 archiver.py "https://www.youtube.com/@PomuRainpuff/community" -o "/home/me/my_save"
```

### Use cookies file

If you want to grab membership posts, you'll need to have a Netscape-format cookies file, which you can pass the path with `-c`:

```shell
python3 archiver.py "https://www.youtube.com/@PomuRainpuff/community" -c "/home/me/my_cookies_file.txt"
```

### Use Firefox instead of Chrome as the driver

```shell
python3 archiver.py "https://www.youtube.com/@PomuRainpuff/community" -d "firefox"
```

## Notes

- Poll vote percentages can only be shown if you are logged in and have voted on the poll before.
