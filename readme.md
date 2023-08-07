Very simple wrapper around yt-dlp and the python pbackage `pydub`.

- Download video from youtube in the form of an audio file (using yt-dlp and ffmpeg)
- Seeks information about video (basically, end-time, using yt-dlp as well (todo: get more precise results with mutagen))
- Cuts the audio from some offset at the beginning to some offset from the end

Usage:

    ./doancu.py http://some_youtube_url -b 00:04.30 -f 3:57 -o filename.mp3

Will download whatever video is in the url into filename.mp3 and cut from 4 first seconds (and 30 miliseconds) to minute 3 second 57

Instead of using a url, you can compile a text file with urls and filenames
eg:

    http://youtube.blabla Name 1 # Comment

    http://youtube.blabla Some other song
    http://youtube.blabla, 0:45, 4:12, Name # you can also specify the times like this



