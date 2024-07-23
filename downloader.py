#!/usr/bin/python
import os
import sys
import shutil
import logging
from datetime import datetime

import m3u8
import requests
import argparse

logging.basicConfig(level=logging.INFO)

def clear_line():
    # Move the cursor to the beginning of the line and clear it
    print('\r', end='')
    print('\033[K', end='')

class StreamingVideoDownloader():
    def __init__(self, masterM3u8Url):
        self.masterM3u8Url = masterM3u8Url

    def clear_temp_files(self):
        logging.info("Cleaning up the temp directory ...")
        try:
            shutil.rmtree("temp")
        except FileNotFoundError:
            logging.info("Temp folder already clean.")

        temp_dir = 'temp'
        os.makedirs(temp_dir, exist_ok=True)

    def get_master_playlist(self):
        # Download the master playlist
        logging.info("Retrieving the Master playlist ...")
        response = requests.get(self.masterM3u8Url)

        if response.status_code != 200:
            logging.error("Master playlist file cannot be found or credentials are missing")
            exit()

        master_playlist = m3u8.loads(response.text)
        if not master_playlist.playlists or len(master_playlist.playlists) == 0:
            logging.error("Invalid Master playlist file.")
            exit()

        return master_playlist

    def download_video_segments(self, video_playlist_uri):
        logging.info("Downloading Video segments ...")
        video_segments_dir = 'temp/video_segments'
        os.makedirs(video_segments_dir, exist_ok=True)

        video_playlist_resp = requests.get(video_playlist_uri).text
        video_playlist = m3u8.loads(video_playlist_resp)

        for i, segment in enumerate(video_playlist.segments):
            clear_line()
            url = segment.absolute_uri
            response = requests.get(url)
            with open(f'{video_segments_dir}/segment_{i:04d}.ts', 'wb') as f:
                f.write(response.content)
            print(f"Downloaded video segment {i + 1}/{len(video_playlist.segments)}", end='')

        return video_playlist

    def download_audio_segments(self, audio_uris):
        logging.info("Downloading Audio segments ...")
        audio_segments_dir = 'temp/audio_segments'
        os.makedirs(audio_segments_dir, exist_ok=True)

        audio_playlist_resp = requests.get(audio_uris[0]).text
        audio_playlist = m3u8.loads(audio_playlist_resp)

        for i, segment in enumerate(audio_playlist.segments):
            clear_line()
            url = segment.absolute_uri
            response = requests.get(url)
            with open(f'{audio_segments_dir}/segment_{i:04d}.aac', 'wb') as f:
                f.write(response.content)
            print(f"Downloaded audio segment {i + 1}/{len(audio_playlist.segments)}", end='')

        return audio_playlist

    def generate_segments_lists(self, audio_playlist, video_playlist):
        logging.info("Generating Segments list to be combined by FFMPEG ...")
        with open('temp/video_segments_list.txt', 'w') as f:
            for i in range(len(video_playlist.segments)):
                f.write(f"file 'video_segments/segment_{i:04d}.ts'\n")
        with open('temp/audio_segments_list.txt', 'w') as f:
            for i in range(len(audio_playlist.segments)):
                f.write(f"file 'audio_segments/segment_{i:04d}.aac'\n")

    def generate_final_video(self):
        combine_video_segments_cmd = 'ffmpeg -loglevel error -stats -f concat -safe 0 -i temp/video_segments_list.txt -c copy temp/combined_video.ts'
        logging.info(f"Combining Video Segments:\n {combine_video_segments_cmd}")
        os.system(combine_video_segments_cmd)

        # Combine Audio segments into one
        combine_audio_segments_cmd = 'ffmpeg -loglevel error -stats -f concat -safe 0 -i temp/audio_segments_list.txt -c copy temp/combined_audio.aac'
        logging.info(f"Combining Audio Segments:\n {combine_audio_segments_cmd}")
        os.system(combine_audio_segments_cmd)

        # Combine video and audio using FFMPEG
        os.makedirs("downloads", exist_ok=True)
        datetime_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        muxing_cmd = f"ffmpeg -loglevel error -stats -i temp/combined_video.ts -i temp/combined_audio.aac -c copy downloads/output_video_{datetime_stamp}.mp4"
        logging.info(f"Multiplexing Audio and Video. Generating final video:\n {muxing_cmd}")
        os.system(muxing_cmd)

        return datetime_stamp


    def download(self):
        logging.info("Starting download.")
        self.clear_temp_files()

        # Get the master playlist
        master_playlist = self.get_master_playlist()

        # Get the video playlist with the highest quality
        logging.info("Retrieving Video playlist from master list ...")
        video_playlist_uri = max(master_playlist.playlists, key=lambda video: video.stream_info.bandwidth).absolute_uri

        # Get available Audio playlists
        logging.info("Retrieving Audio playlist from master list ...")
        audio_uris = []
        for media in master_playlist.media:
            if media.type == 'AUDIO':
                audio_uris.append(media.uri)

        # Download the Video segments
        video_playlist = self.download_video_segments(video_playlist_uri)

        # Download the Audio segments
        audio_playlist = self.download_audio_segments(audio_uris)

        # Generate the list of segments to be used by FFMPEG to combine segments
        self.generate_segments_lists(audio_playlist, video_playlist)

        # Combine Video segments into one
        datetime_stamp = self.generate_final_video()

        logging.info(f"Video and Audio merged successfully into MP4 file: downloads/output_video_{datetime_stamp}.mp4")





if __name__ == "__main__":
    # ToDo: Add more error handling
    parser = argparse.ArgumentParser()
    parser.add_argument('-mp', '--masterplaylist', type=str, help='URL for the master playlist with m3u8 extension')

    args = parser.parse_args()
    masterM3U8Url = args.masterplaylist

    if not masterM3U8Url:
        logging.error("Missing or invalid master playlist URL")

    downloader = StreamingVideoDownloader(masterM3U8Url)
    downloader.download()

