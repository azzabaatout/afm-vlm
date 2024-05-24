from __future__ import print_function

import csv
import json
import math
import os
import shlex
import subprocess

import pandas as pd
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from tqdm import tqdm

# The rest of the functions remain unchanged

# Removed the main() and if __name__ == "__main__" block


def split_by_manifest(
    filename,
    manifest,
    output_dir,
    vcodec="copy",
    acodec="copy",
    extra="",
    **kwargs,
):
    """Split video into segments based on the given manifest file.

    Arguments:
        filename (str)      - Location of the video.
        manifest (str)      - Location of the manifest file.
        vcodec (str)        - Controls the video codec for the ffmpeg video
                            output.
        acodec (str)        - Controls the audio codec for the ffmpeg video
                            output.
        extra (str)         - Extra options for ffmpeg.
    """
    if not os.path.exists(manifest):
        print("File does not exist: %s" % manifest)
        raise SystemExit

    with open(manifest) as manifest_file:
        manifest_type = manifest.split(".")[-1]
        if manifest_type == "json":
            config = json.load(manifest_file)
        elif manifest_type == "csv":
            config = csv.DictReader(manifest_file)
        else:
            print("Format not supported. File must be a csv or json file")
            raise SystemExit

        split_cmd = [
            "ffmpeg",
            "-i",
            filename,
            "-vcodec",
            vcodec,
            "-acodec",
            acodec,
            "-y",
        ] + shlex.split(extra)
        try:
            fileext = filename.split(".")[-1]
        except IndexError as e:
            raise IndexError("No . in filename. Error: " + str(e))
        for video_config in config:
            split_args = []
            try:
                split_start = video_config["start_time"]
                split_length = video_config.get("end_time", None)
                if not split_length:
                    split_length = video_config["length"]
                filebase = video_config["rename_to"]
                if fileext in filebase:
                    filebase = ".".join(filebase.split(".")[:-1])

                split_args += [
                    "-ss",
                    str(split_start),
                    "-t",
                    str(split_length),
                    filebase + "." + fileext,
                ]
                print("########################################################")
                print("About to run: " + " ".join(split_cmd + split_args))
                print("########################################################")
                subprocess.check_output(split_cmd + split_args)
            except KeyError as e:
                print("############# Incorrect format ##############")
                if manifest_type == "json":
                    print("The format of each json array should be:")
                    print("{start_time: <int>, length: <int>, rename_to: <string>}")
                elif manifest_type == "csv":
                    print("start_time,length,rename_to should be the first line ")
                    print("in the csv file.")
                print("#############################################")
                print(e)
                raise SystemExit


def get_video_length(filename):
    output = subprocess.check_output(
        (
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            filename,
        )
    ).strip()
    video_length = int(float(output))
    print("Video length in seconds: " + str(video_length))

    return video_length


def ceildiv(a, b):
    return int(math.ceil(a / float(b)))


def split_by_seconds(
    filename,
    split_length,
    output_dir,
    vcodec="copy",
    acodec="copy",
    extra="",
    video_length=None,
    **kwargs,
):
    if split_length and split_length <= 0:
        print("Split length can't be 0")
        raise SystemExit

    if not video_length:
        video_length = get_video_length(filename)
    split_count = ceildiv(video_length, split_length)
    if split_count == 1:
        print("Video length is less then the target split length.")
        raise SystemExit

    split_cmd = [
        "ffmpeg",
        "-i",
        filename,
        "-vcodec",
        vcodec,
        "-acodec",
        acodec,
    ] + shlex.split(extra)
    # Ensure the output directory exists

    try:
        filebase = filename.split("/")[-1].split(".")[0]
        filebase = os.path.join(output_dir, filebase)
        fileext = filename.split(".")[-1]
    except IndexError as e:
        raise IndexError("No . in filename. Error: " + str(e))

    for n in range(0, split_count):
        split_args = []
        if n == 0:
            split_start = 0
        else:
            split_start = split_length * n

        output_filename = f"{filebase}-{n + 1}-of-{split_count}.{fileext}"
        output_filepath = os.path.join(output_dir, output_filename)

        split_args += [
            "-ss",
            str(split_start),
            "-t",
            str(split_length),
            output_filepath,
        ]
        print("About to run: " + " ".join(split_cmd + split_args))
        subprocess.check_output(split_cmd + split_args)


def split_video(filename, split_length=None, manifest=None, output_dir=None, **kwargs):
    """
    Entry function to split video either by seconds or using a manifest file.
    Args:
        filename (str): Path to the video file.
        split_length (int, optional): Length of each segment in seconds.
        manifest (str, optional): Path to a JSON or CSV manifest file.
        output_dir (str, optional): Path to put the chunks in.
        **kwargs: Additional keyword arguments for video codec settings.
    """
    if manifest:
        split_by_manifest(filename, manifest, output_dir, **kwargs)
    else:
        if not split_length:
            video_length = get_video_length(filename)
            split_by_seconds(
                filename, split_length, output_dir, video_length=video_length, **kwargs
            )
        else:
            split_by_seconds(filename, split_length, output_dir, **kwargs)


def split_mp3(input_file, output_dir, split_length):
    """
    Split an MP3 file into multiple snippets of a specified length.

    Args:
        input_file (str): The path to the input MP3 file.
        output_dir (str): The directory where the snippets will be saved.
        split_length (int): The length of each snippet in seconds.

    Returns:
        None
    """

    print(f"Output_dir_audio: {output_dir}")
    # os.chmod(output_dir, 0o777)
    # os.makedirs(output_dir, exist_ok=True)

    # Load the input MP3 file
    audio = AudioSegment.from_mp3(input_file)

    # Calculate the length of snippets in milliseconds
    snippet_length_ms = split_length * 1000

    # Initialize the starting and ending positions for slicing
    start_time = 0
    end_time = snippet_length_ms

    print(f"Audio length: {len(audio)}")
    print(f"Audio duration: {audio.duration_seconds}")

    print(f"End time: {end_time}")

    # Initialize snippet count
    snippet_count = 1

    while end_time <= len(audio):
        # Extract the snippet
        snippet = audio[start_time:end_time]
        print(f"Snippet: {snippet}")

        # Define the output file name
        output_file = os.path.join(output_dir, f"snippet_{snippet_count}.mp3")

        # Export the snippet as an MP3 file
        snippet.export(output_file, format="mp3")

        # Update start and end times for the next snippet
        start_time = end_time
        print(f"Start time:{start_time}")
        end_time = start_time + snippet_length_ms
        print(f"Start time:{end_time}")

        # Increment the snippet count
        snippet_count += 1

    print(f"Split {snippet_count - 1} snippets from {input_file}.")


def extract_and_store_audio(video_dir, audio_dir):
    """
    Extract audio from each video in the video_dir and store it in audio_dir.
    """
    os.makedirs(audio_dir, exist_ok=True)  # Ensure the audio directory exists
    video_files = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]

    for video_file in tqdm(video_files):
        video_path = os.path.join(video_dir, video_file)
        audio_path = os.path.join(audio_dir, video_file.replace(".mp4", ".wav"))

        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path, codec="pcm_s16le", fps=44100)
        print(f"Audio extracted and saved as {audio_path}")


def transcribe_audio_files(audio_dir, transcriptions_dir, model, lang="en"):
    """
    Transcribe each audio file in the audio_dir and save transcriptions to transcriptions_dir.
    """
    os.makedirs(transcriptions_dir, exist_ok=True)
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith(".wav")]

    for audio_file in tqdm(audio_files):
        audio_path = os.path.join(audio_dir, audio_file)
        result = model.transcribe(audio_path, task="translate", language=lang)
        # Create Subtitle dataframe and save it
        dict1 = {"start": [], "end": [], "text": []}
        for segment in result["segments"]:
            dict1["start"].append(int(segment["start"]))
            dict1["end"].append(int(segment["end"]))
            dict1["text"].append(segment["text"])
        df = pd.DataFrame.from_dict(dict1)
        df.to_csv(os.path.join(transcriptions_dir, audio_file.replace(".wav", ".csv")))
        print(f"Transcription for {audio_file} saved in {transcriptions_dir}")
        audio_path = os.path.join(audio_dir, audio_file)
        result = model.transcribe(audio_path, task="translate", language=lang)

        # Create Subtitle dataframe and save it
        dict1 = {"start": [], "end": [], "text": []}
        for segment in result["segments"]:
            dict1["start"].append(int(segment["start"]))
            dict1["end"].append(int(segment["end"]))
            dict1["text"].append(segment["text"])

        df = pd.DataFrame.from_dict(dict1)
        df.to_csv(os.path.join(transcriptions_dir, audio_file.replace(".wav", ".csv")))

        print(f"Transcription for {audio_file} saved in {transcriptions_dir}")
