# Streaming Video Downloader

This is a python program to download streaming videos from webpages where HTTP Live Streaming (HLS)
protocol is used to serve a streaming video.

## Instructions

### Instalation:
- Clone this repo into your machine.
- Install the required python packages:
```commandline
$ pip install requirements.txt
```

- Install FFMPEG command line tool:

```https://www.ffmpeg.org/download.html```

### Usage
To download a video, browse to the webpage where the streaming video is located. 
- Open Chrome/Firefox Dev tools
- Go to Network tab
- Refresh the page and in the filter, search (filter) for a request starting with `master.m3u8`
- Right-click on the request and `copy URL`
- Go to command line next to downloader.py and run:
```commandline
python3 ./downloader.py -mp="https://COPIED_URL_FOR_THE_MASTER_PLAYLIST.m3u8&token=XYZ"
```
or
```commandline
python3 ./downloader.py --masterplaylist="https://COPIED_URL_FOR_THE_MASTER_PLAYLIST.m3u8&token=XYZ"
```
- The output video will be saved in the `downloads` folder in the same directory

### What is a Master M3U8 File?
A master M3U8 file, also known as a master playlist, is a type of M3U8 file used in 
HTTP Live Streaming (HLS). It provides multiple versions of the same content at 
different bitrates and resolutions. This allows the client (e.g., a video player) 
to choose the most appropriate stream based on the current network conditions and 
device capabilities. The master playlist does not contain the actual media segments; 
instead, it points to other M3U8 files (media playlists) that contain the segments.