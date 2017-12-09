Very simple wrapper around youtube-dl and cutmp3 (basically, a bash script made into a python one just becareturn 

- Download video from youtube in the form of an audio file (using youtube-dl and ffmpeg)
- Seeks information about video (basically, end-time, using youtube-dl as well (todo: get more precise results with mutagen))
- Cuts the audio from some offset at the beginning to some offset from the end

Usage:

    ./doancu.py http://some_youtube_url -i 00:04 -f 00:20 -o filename.mp3

Will download whatever video is in the url into filename.mp3 and cut the 4 first seconds and the last 20.

Instead of using a url, you can compile a text file with urls and filenames
eg:

   http://youtube.blabla Name 1
   http://youtube.blabla Some other song


