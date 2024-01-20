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

4. Install Chrome, as this uses headless Chrome.

5. Run `archiver.py`. For example:

   ```shell
   python3 archiver.py "https://www.youtube.com/@PomuRainpuff/community"
   ```

   This will spawn a headless Chrome instance (that is, you won't see a Chrome window) and download all posts
   it can find from the provided page, and save results in an automatically created folder called `archive-output`
   in the same directory.

   If you want to set the save location, then use `-o`:

   ```shell
   python3 archiver.py "https://www.youtube.com/@PomuRainpuff/community" -o "/home/me/my_save"
   ```

   If you need to pass your user profile, then pass it with `-p`:

   ```shell
   python3 archiver.py "https://www.youtube.com/@PomuRainpuff/community" -p "/home/me/.config/google-chrome/Profile 1"
   ```

   You can find the profile path at `chrome://version` beside "Profile Path". Note that if you pass in a profile,
   the archiver cannot run in headless mode for [reasons](https://github.com/SeleniumHQ/selenium/issues/11224), so
   you will see a browser window pop up. Just don't touch it while it works; you can leave it minimized!

   For more information, run using `--help` like so:

   ```shell
   python3 archiver.py --help
   ```

## Notes

- Poll vote percentages can only be shown if you are logged in and have voted on the poll.
