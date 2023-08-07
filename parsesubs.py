"""
    Utilities to parse the subtitules from a youtube video into a simple .lrc file 

    Uses the library webvtt
        pip install webvtt-py
"""
from dataclasses import dataclass
from pathlib import Path

import webvtt


@dataclass
class _Caption:
    text: str
    time: str

    @classmethod
    def from_vttcaption(cls, vtt_caption):
        return cls(vtt_caption.text, vtt_caption.start)

    def lrc(self):
        """Return the caption in srt format"""
        return f"[{self.lrc_time}] {self.clean_text}"

    @property
    def clean_text(self):
        """Remove possible line breaks in the middle of the text"""
        return self.text.strip().replace("\n", " ")

    @property
    def lrc_time(self):
        """The lrc format expects min:sec.XX while the vtt format we have encounterd
        are hh:mm:ss:XXX, this justs removes the 3 first characters and the last one
        """
        return self.time.strip()[3:-1]

    def __repr__(self):
        return self.lrc()


def _parse_caption(vtt_file):
    """Utilize webvtt library to parse captions from youtube"""
    parsed_vtt = webvtt.read(vtt_file)

    # The first caption needs no checks
    c = _Caption.from_vttcaption(parsed_vtt.captions[0])
    parsed_captions = [c]

    for caption in parsed_vtt.captions[1:]:
        if caption.text == parsed_captions[-1].text:
            continue

        parsed_captions.append(_Caption.from_vttcaption(caption))

    return parsed_captions


def vtt_to_lrc(vtt_file):
    """Converts a vtt file into a lrc format"""
    captions = _parse_caption(vtt_file)
    output_file = Path(vtt_file.stem).with_suffix(".lrc")
    output_file.write_text("\n".join(i.lrc() for i in captions))
