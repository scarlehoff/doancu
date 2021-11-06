#!/usr/bin/env python3
"""
    DOwnload ANd CUt video from youtube (or any youtube-dl supported source)
"""

import logging
import tempfile
import sys
import shutil
from errno import ENOENT
import subprocess as sp
from pathlib import Path
from argparse import ArgumentParser

from pydub import AudioSegment

logging.basicConfig(level=logging.WARNING, format="[{levelname}] {message}", style="{")
logger = logging.getLogger(__name__)


def parse_all_args():
    """Wrapper for the argument parser"""

    parser = ArgumentParser()

    parser.add_argument("url", help="URL to download from (or file with urls")
    parser.add_argument("-f", "--final_time", help="final time of the video at which to cut")
    parser.add_argument(
        "-b",
        "--initial_offset",
        help="offset to cut at the beginning of the video in the format minutes:seconds",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="output name. if unset, use whatever name comes from youtube",
    )
    parser.add_argument(
        "--raw",
        help="don't remove the -blabla youtube-dl writes if -o not given",
        action="store_true",
    )
    parser.add_argument(
        "--dry",
        help="skip the download of the video (ie, assume it is already there)",
        action="store_true",
    )
    parser.add_argument("-v", "--verbose", help="Make the output more verbose", action="store_true")

    return parser.parse_args()


def parse_input(input_uri, output=None, beginning=None, end=None):
    """Parse the input into an iterator of
        (input urls, output names, beginnings, ends)
    We can just use the CLI to get one single file or get files
    from a library of urls
    """
    # First check whether this is a file
    input_file = Path(input_uri)
    if input_file.exists():
        f = input_file.open()
        url_lst = []
        io_lst = []
        fo_lst = []
        output_lst = []
        for line_raw in f:
            # First remove comments and skip empty lines
            line = line_raw.split("#", 1)[0]
            if line.strip() == "":
                continue
            # Are times included in the line? format: url, beginning, ending, name
            comma_format = line.split(",")
            if len(comma_format) == 4:
                url_lst.append(comma_format[0].strip())
                io_lst.append(comma_format[1].strip())
                fo_lst.append(comma_format[2].strip())
                output_lst.append(comma_format[3].strip())
            else:
                l = line.split()
                url_lst.append(l[0].strip())
                out_name = " ".join(l[1:])
                output_lst.append(out_name.strip())
                io_lst.append(beginning)
                fo_lst.append(end)

    else:
        url_lst = [input_uri]
        output_lst = [output]
        io_lst = [beginning]
        fo_lst = [end]

    return zip(url_lst, output_lst, io_lst, fo_lst)


def cmd_call(cmd):
    """Wrapper around sp run to get (or not) the output"""
    if isinstance(cmd, str):
        cmd_list = cmd.split(" ")
        cmd_str = cmd
    else:
        cmd_list = cmd
        cmd_str = " ".join(cmd)
    logger.info(f"Running '~$ {cmd_str}' as: {cmd_list}")
    try:
        res = sp.run(cmd_list, stdout=sp.PIPE)
        if res.returncode != 0:
            logger.error(f"Something went wrong: $?={res.returncode}")
            logger.error(f"Command: {cmd_str}")
            sys.exit(-1)
    except OSError as e:
        if e.errno == ENOENT:
            logger.error(f"{cmd_list[0]} not found in the system, please install it")
            sys.exit(-1)
        raise e

    cmd_output = res.stdout.decode().strip()
    logger.info(cmd_output)
    return cmd_output


def download_youtube(url, file_name=None, dry_run=False):
    """Wrapper around youtube_dl"""
    cmd = ["youtube-dl", "--audio-format", "mp3", "--xattrs", "-x", url]
    if file_name is not None:
        wild_card = ".%(ext)s"
        if ".mp3" not in file_name:
            file_name += ".mp3"
        wild_name = file_name.replace(".mp3", wild_card)
        cmd += ["-o", wild_name]
    else:
        get_name = cmd + ["--get-filename"]
        file_name_raw = cmd_call(get_name)
        file_name = file_name_raw.rsplit(".", 1)[0] + ".mp3"
        logger.info(f"Autodiscovered output name will be: {file_name}")

    if not dry_run:
        _ = cmd_call(cmd)

    output_path = Path(file_name)
    if not output_path.exists():
        logger.warning(
            f"No failure was found, but the output path: {output_path} doesn't exist... maybe something went wrong"
        )

    return output_path


def parse_regular_time(time_str):
    """Parse a min:sec string into miliseconds
    can also accept min:sec.miliseconds
    """
    mstr, sstr = time_str.split(":")
    mstr = int(mstr) * 60 * 1000
    try:
        sstr = int(sstr) * 1000
    except ValueError:
        sstr, milistr = sstr.split(".")
        milistr = int(milistr)
        sstr = int(sstr) * 1000 + milistr
    return mstr + sstr


def cut_audio(file_name, initial=None, end=None):
    """Cut the audio file, remove some time from the beginning and from the end"""
    temp_file = Path(tempfile.mktemp())
    logger.info(f"Using temporary file: {tempfile}")

    if initial is None:
        i_off = 0
    else:
        i_off = parse_regular_time(initial)
        logger.info(f"Cutting {initial} from the beggining")

    if end is None:
        f_off = None
    else:
        f_off = parse_regular_time(end)
        logger.info(f"Cutting at {end}")

    # Get the mp3
    song = AudioSegment.from_mp3(file_name)
    cut_song = song[i_off:f_off]
    # Export it out
    cut_song.export(temp_file, format="mp3")
    # Now move the temporary file back to the right place
    shutil.move(temp_file, file_name)


if __name__ == "__main__":
    args = parse_all_args()
    if args.verbose:
        logger.setLevel(logging.INFO)

    # Parse the input file or url (and other information) into an iterator
    target_iterator = parse_input(args.url, args.output, args.initial_offset, args.final_time)

    for url, output, io, fo in target_iterator:
        # First call youtube_dl
        file_name = download_youtube(url, output, args.dry)

        if io or fo:
            logger.info("Cutting up the output")
            # Use pydub to cut the file
            cut_audio(file_name, initial=io, end=fo)

        if not output and not args.raw:
            # Clean a possible terrible name coming from youtube
            new_name = file_name.as_posix().rsplit("-", 1)[0] + ".mp3"
            shutil.move(file_name, new_name)
