"""
Provide utilities to fix my flattened music list.  Screw you Amazon/Google Music!

Leverages mutagen to gain audio details from the file metadata.
See more here:  https://mutagen.readthedocs.io/en/latest/user/gettingstarted.html

Mainly, this module can:
    1.  Move a directory of mp3 files (other types are ignored) into an Artist -> Album folder structure.
        In doing so the mp3 files also renamed using information provided in their ID3 tags.
        - Note:  This process will fail for files without artist metadata.
    2.  Provides some utilities to manipulate the ID3 metadata on a song.

"""
import mutagen
from mutagen.id3 import TIT2, TALB, TPE1

import logging
from functools import partial
from collections import defaultdict
import os


MUSIC_DIR = r"C:\Users\Admin\OneDrive\Music"

ALBUM_TITLE = "TALB"
ARTIST = "TPE1"
TRACK_TITLE = "TIT2"


def get_aggregate_data(directory):
    file_names = os.listdir(directory)
    extensions = defaultdict(int)
    for file_name in file_names:
        _, _, ext = file_name.rpartition(".")
        extensions[ext] += 1
    logging.info(extensions)


def confirm_or_create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    return True


def sanitize_file_name_text(raw):
    s = str(raw)
    s = s.strip()
    fixes = [
        ("/", "-"), ("?", ""),
        (":", "-"), ("\"", ""),
    ]
    for fix in fixes:
        s = s.replace(*fix)
    return s


def get_tag_value(track_file, tag_key):
    try:
        t = track_file.tags[tag_key]
    except KeyError as e:
        logging.debug(f"{track_file.filename} is missing key: {e}")
        return ""
    else:
        return sanitize_file_name_text(t)


def unflatten_track_file(track_file: mutagen.FileType, original_track_path, new_root_dir, dry_run=False):
    # Discontinue if there is no artist information.
    try:
        artist = track_file.tags[ARTIST]
    except KeyError:
        raise
    else:
        artist = sanitize_file_name_text(artist)

    album_title = get_tag_value(track_file, ALBUM_TITLE)
    track_title = get_tag_value(track_file, TRACK_TITLE)
    # If the album title is not found use the track title...
    album_title = album_title or "Unknown Album"
    # ... but don't let it have .mp3 extension.
    album_title = album_title.replace(".mp3", "")

    artist_dir = os.path.join(new_root_dir, artist)
    album_dir = os.path.join(artist_dir, album_title)
    track_new_path = os.path.join(new_root_dir, artist, album_title, ".".join([track_title, "mp3"]))

    logging.info(f"Album: {album_title}, Track: {track_title}, Artist: {artist}")
    if not os.path.exists(track_new_path):
        if not dry_run:
            confirm_or_create_dir(artist_dir)
            confirm_or_create_dir(album_dir)
            os.rename(original_track_path, track_new_path)
        return True
    else:
        logging.info(f"File exists: {track_new_path}")
    return False


def mutagen_dialect_unflatten(dry_run=False):
    """A mutagen implementation for un-flattening audio files within a directory."""
    files = os.listdir(MUSIC_DIR)
    count = jpg_count = file_existed_count = 0
    initial_count = len(files)

    logging.info("Initiating...")

    for file in files:
        if file.endswith("mp3"):
            track_path = os.path.join(MUSIC_DIR, file)
            track_file = mutagen.File(track_path)
            logging.info(f"Handling: {file}")
            try:
                was_moved = unflatten_track_file(track_file, track_path, MUSIC_DIR, dry_run=dry_run)
            except KeyError as e:
                logging.error(f"Error with {file}: {e}")
            else:
                count += was_moved
                file_existed_count += not was_moved
        elif file.endswith("jpg"):
            jpg_count += 1

    logging.info(f"""** FINISHED **
        TOTAL_FILES:  {initial_count}
        MP3_FILES_MOVED:  {count}
        JPG FILES:  {jpg_count}
        MP3_FILES EXISTED IN DEST: {file_existed_count}
        """)


def fix_missing_file_extensions(root_dir, dry_run=False):
    """Fix moving files with no file extension.  Whoops!

    :param root_dir: The directory to begin looking for files.
    :param dry_run: If True, no rename takes place.

    """
    files = os.listdir(root_dir)
    dirs = [f for f in files if os.path.isdir(os.path.join(root_dir, f))]
    for d in dirs:
        p = os.path.join(root_dir, d)
        for album in os.listdir(p):
            a = os.path.join(p, album)
            for track in os.listdir(a):
                if not track.endswith(".mp3"):
                    old = os.path.join(a, track)
                    new = old + ".mp3"
                    print(f"Old: {old}")
                    print(f"New: {new}")
                    if not dry_run:
                        os.rename(old, new)


def _set_tag(F, **kwargs):
    audio = kwargs.get("audio")
    audio.tags.add(F(**kwargs))


set_title = partial(_set_tag, TIT2, encoding=3)
set_artist = partial(_set_tag, TPE1)
set_album = partial(_set_tag, TALB)


def get_audio(file):
    p = os.path.join(MUSIC_DIR, file)
    return mutagen.File(p)


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    mutagen_dialect_unflatten(dry_run=False)
    # fix_missing_file_extensions(MUSIC_DIR, dry_run=False)


if __name__ == '__main__':
    main()
