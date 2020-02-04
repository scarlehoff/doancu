#!/usr/bin/env python3

""" DOwnload ANd CUt video from youtube (or any youtube-dl supported source) """

import subprocess as sp
import errno
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
    parser.add_argument("--dry", help = "Skip the download of the video (ie, assume it is already there)", action = "store_true")

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
            print("~$ {0}".format(" ".join(cmd_list)))
            sys.exit(-1)
    except OSError as e:
        if e.errno == errno.ENOENT:
            print("Program \"{0}\" was not found in the system. Please install in order to use this script".format(cmd_list[0]))
            sys.exit(-1)
        else:
            raise
    
    if get_output:
        return res.stdout.decode().strip()
    else:
        return res.returncode

def download_audio(url, file_name = None, dry_run = False):
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
        file_name = file_name_raw.rsplit(".",1)[0] + ".mp3"
    if not dry_run:
        cmd_call(cmd)
    return file_name


def cut_audio(file_name, beginning, end = None):
    temp_file = "temp_{0}".format(file_name)
    if not beginning:
        beginning = "0:00"
    if not end:
        end = "999999:00"
    cmd = ["cutmp3", "-q", "-i", file_name, "-a", beginning, "-b", end, "-O", temp_file]
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

def parse_file(input_file, output, default_beginning, default_end):
    url_lst = []
    output_lst = []
    io_lst = [] # initial_offsets
    fo_lst = [] # final_offsets
    if "http" in input_file:
        url_lst = [input_file]
        output_lst = [output]
        io_lst = [default_beginning]
        fo_lst = [default_end]
    else:
        with open(args.url) as f:
            for line_raw in f:
                # First remove comments and skip empty lines
                line = line_raw.split("#",1)[0]
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
                    io_lst.append(default_beginning)
                    fo_lst.append(default_end)

    return zip(url_lst, output_lst, io_lst, fo_lst)


if __name__ == "__main__":

    args = parse_all_args()

    data = parse_file(args.url, args.output, args.initial_offset, args.final_offset)

    for url, output, io, fo in data:
        # Call youtube_dl
        file_name = download_audio(url, output, args.dry)

        if io or fo:
            if fo:
                audio_duration = get_audio_duration(url)
                final_offset = compute_offset(audio_duration, fo)
            else:
                final_offset = "99999:00"

            # Call cutmp3 to cut the video
            cut_audio(file_name, io, final_offset)

        if not output and not args.raw:
            file_name = clean_name(file_name)
        print("Done: {0}".format(file_name))
