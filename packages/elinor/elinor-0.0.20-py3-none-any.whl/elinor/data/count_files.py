import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from functools import partial


def _count_files_in_dir(ends, args):
    root, files = args
    return sum(1 for file in files if file.lower().endswith(ends))


def count_files_by_end(directory, ends=".png", workers=None):
    """
    统计目录下所有文件的数量，支持多线程并行处理。
    该函数会遍历指定目录及其子目录，统计所有文件的数量。
    Args:
        directory: 要扫描的目录路径
        workers: 并行工作线程数(默认使用CPU核心数)
    """

    if workers is None:
        from multiprocessing import cpu_count
        workers = max(cpu_count() - 1, 1)  # 保留一个核心用于其他任务

    # 收集所有目录和文件
    walk_results = [(root, files) for root, _, files in os.walk(directory)]

    func = partial(_count_files_in_dir, ends)

    total = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(func, args) for args in walk_results]
        for f in tqdm(as_completed(futures), total=len(futures), desc="Scanning Dirs", unit="dir", mininterval=1):
            total += f.result()

    return total


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="Directory to scan")
    parser.add_argument("-j", "--workers", type=int, default=None,
                        help="Number of worker threads")
    parser.add_argument("-e", "--ends", type=str, default=".png",
                        help="File extension to count (default: .png)")
    args = parser.parse_args()

    files_count = count_files_by_end(args.directory, ends=args.ends, workers=args.workers)
    print(f"Total files: {files_count}")