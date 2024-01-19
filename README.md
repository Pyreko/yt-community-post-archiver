# yt-community-post-archiver

Archives YouTube community posts. Will try and grab the post's text content, images at as large of a resolution as
possible, and some other various metadata.

Note this was written _really_ quickly, and might not work every time - you may need to run this a few times to
get everything and not have crashes. It is also a bit fragile, and YT updates might break it. Feel free to let me know
if it's broken, and if I can I'll try to fix it!

## Usage

1. Clone the repo.

2. (Optional) Create and source a venv:

   ```shell
   python3 -m venv venv
   source venv/bin/activate
   ```

3. (Optional) Download the dependencies in `requirements.txt`:

   ```shell
   pip3 install -r requirements.txt
   ```

4. Run `archiver.py`. For example:

   ```shell
   python3 archiver.py "https://www.youtube.com/@PomuRainpuff/community
   ```

   For more information, run using `--help` like so:

   ```shell
   python3 archiver.py --help
   ```
