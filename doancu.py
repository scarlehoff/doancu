#!/usr/bin/env python3

""" DOwnload ANd CUt video from youtube (or any youtube-dl supported source """

import subprocess as sp
import os
import sys
from datetime import datetime

def parse_all_args():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("url", help = "url we want to download")

    parser.add_argument("-b","--initial_offset", help = "Offset to cut at the beginning of the video in the format minutes:seconds")
    parser.add_argument("-f","--final_offset", help = "Offset to cut at the end of the video")

    parser.add_argument("-o", "--output", help = "Output name. If unset, use whatever name comes from youtube")

    parser.add_argument("--raw", help = "Don't remove the -blabla youtube-dl writes if -o not given", action = "store_true")

    args = parser.parse_args()

    return args

def cmd_call(cmd_list, verbose = False, get_output = False):
    if verbose:
        print("Running: {0}".format(" ".join(cmd_list)))
        print("as: {0}".format(cmd_list))
    if get_output:
        output_pipe = sp.PIPE
    else:
        output_pipe = sp.DEVNULL
    try:
        res = sp.run(cmd_list, stdout=output_pipe)
        if res.returncode != 0:
            print("Something went wrong tring to execute the following command: $?={0}".format(res.returncode))
            print("~$ {0}".format(cmd_str))
            sys.exit(-1)
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            print("Program {0} not found".format(cmd_list[0]))
            sys.exit(-1)
        else:
            raise
    
    if get_output:
        return res.stdout.decode().strip()
    else:
        return res.returncode

def download_audio(url, file_name = None):
    cmd = ["youtube-dl", "--audio-format", "mp3", "--xattrs", "-x", url]
    if file_name:
        wild_card = ".%(ext)s"
        if ".mp3" not in file_name:
            file_name += ".mp3"
        wild_name = file_name.replace(".mp3", wild_card)
        cmd += ["-o", wild_name]
    else:
        get_name = cmd + ["--get-filename"]
        file_name_raw = cmd_call(get_name, get_output = True)
        file_name = file_name_raw.rsplit(".",-1)[0] + ".mp3"
    cmd_call(cmd)
    return file_name


def cut_audio(file_name, begining, end = None):
    temp_file = "temp_{0}".format(file_name)
    cmd = ["cutmp3", "-q", "-i", file_name, "-a", begining, "-b", end, "-O", temp_file]
    cmd_call(cmd, verbose=False)
    cmd = ["mv", temp_file, file_name]
    return cmd_call(cmd)


def get_audio_duration(url):
    cmd = ["youtube-dl", "--get-duration", url]
    total_time = cmd_call(cmd, get_output = True)
    return total_time

def compute_offset(total_duration, final_offset = None):
    format_time = "%M:%S" #.%f
    total_time = datetime.strptime(total_duration, format_time)
    if not final_offset:
        final_offset = "00:00"
    offset = datetime.strptime(final_offset, format_time)
    final_time = str(total_time - offset)
    # Why don't timedelta allow for a format string :( ?
    return ":".join(final_time.split(":")[-2:])

def clean_name(file_name):
    new_name = file_name.rsplit("-",1)[0]
    new_name_mp3 = new_name + ".mp3"
    cmd = ["mv", file_name, new_name_mp3]
    cmd_call(cmd, verbose = False)
    return new_name_mp3


if __name__ == "__main__":

    args = parse_all_args()

    if "http" in args.url:
        url_lst = [args.url]
        output_names = [args.output]
    else:
        url_lst = []
        output_names = []
        with open(args.url) as f:
            for line in f:
                if line.strip() == "":
                    continue
                l = line.split()
                url_lst.append(l[0])
                if len(l) > 1:
                    output_names.append(" ".join(l[1:]))
                else:
                    output_names.append(None)

    for url, output in zip(url_lst, output_names):
        # Call youtube_dl
        file_name = download_audio(url, output)

        if args.initial_offset or args.final_offset:
            if args.final_offset:
                audio_duration = get_audio_duration(url)
                final_offset = compute_offset(audio_duration, args.final_offset)
            else:
                final_offset = "99999:00"

            # Call cutmp3 to cut the video
            cut_audio(file_name, args.initial_offset, final_offset)

        if not output and not args.raw:
            file_name = clean_name(file_name)
        print("Done: {0}".format(file_name))
