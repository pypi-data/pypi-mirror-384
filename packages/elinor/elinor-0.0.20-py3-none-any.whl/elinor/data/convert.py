import os
import sys
import ffmpeg
from concurrent.futures import ThreadPoolExecutor

import logging
import argparse
from timeit import default_timer as timer
import csv


def timeit(func):
    def wrapper(*args, **kwargs):
        start = timer()
        result = func(*args, **kwargs)
        end = timer()
        logging.info(f"Function {func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper


def convert_mp4_to_mp3(input_video, output_audio, cmd='ffmpeg'):
    logging.info(f"{input_video} converting...")
    if os.path.exists(output_audio):
        logging.info(f"{output_audio} already exists.")
        return 0
    
    try:
        (
            ffmpeg
            .input(input_video)
            .output(
                output_audio,
                **{
                    'q:a': 2,          # 2表示较好质量，范围0-9
                    'c:a': 'libmp3lame',
                    # 'preset': 'fast',  # 编码预设
                    'threads': '2',    # 分配2个线程
                    'vn': None         # 禁用视频流处理
                }
            )
            # .overwrite_output()  # 如果输出文件已存在，则覆盖
            .run(quiet=True, cmd=cmd)           # 禁用控制台输出
        )
        logging.info(f"{output_audio} created successfully.")
        return 0
    except Exception as e:
        logging.error(f"Error converting {input_video}: {e}")
        return 1


@timeit
def convert_videos_in_folder(input_folder, output_folder, cmd='ffmpeg'):
    files = []
    for filename in os.listdir(input_folder):
        if filename.endswith(".mp4"):
            input_video = os.path.join(input_folder, filename)
            output_audio = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.mp3")
            files.append((input_video, output_audio, cmd))
    
    max_workers = os.cpu_count() * 2 if os.cpu_count() else 4
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(convert_mp4_to_mp3, *file) for file in files]
        for future in futures:
            result = future.result()


def ffprobe_get_duration(input_video, cmd='ffprobe'):
    try:
        probe = ffmpeg.probe(input_video, cmd=cmd)
        duration = float(probe['format']['duration'])
        return duration
    except ffmpeg.Error as e:
        logging.error(f"Error probing {input_video}: {e}")
        return None


def cos_to_csv(input_path, output_path, sep="\x1F"):
    with open(input_path, 'r', encoding='utf-8') as f:
        raw = f.readlines()
    csv_part = raw[2: -3]  # remove the first two and last three lines
    
    tmp = []
    for i, line in enumerate(csv_part):
        parts = line.rsplit("|", 5)
        if len(parts) == 6:
            tmp.append(parts)
        else:
            raise ValueError(f"Line {i+2} does not have exactly 6 parts: {line}")

    with open(output_path, "w", newline='') as f:
        writer = csv.writer(f, delimiter=sep)
        writer.writerow(["KEY", "TYPE", "LAST MODIFIED", "ETAG", "SIZE", "RESTORESTATUS"])
        writer.writerows(tmp)