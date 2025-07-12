#!/usr/bin/env python3
import argparse
import json
import math
import time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

#############################
# 摄像头相关辅助类           #
#############################

class CameraReader:
    """摄像头读取基类，定义接口。"""

    def open(self):
        raise NotImplementedError  # 子类需实现打开摄像头的方法

    def read(self):
        """读取一帧，返回(success: bool, frame: np.ndarray)"""
        raise NotImplementedError  # 子类需实现读取帧的方法

    def release(self):
        """释放摄像头资源，默认无操作，子类可重写"""
        pass


class OpenCVCameraReader(CameraReader):
    """基于 OpenCV 的摄像头读取实现。"""

    def __init__(self, cam_index: int, width: int = 640, height: int = 480):
        self.index = cam_index
        self.width = width
        self.height = height
        self.cap: cv2.VideoCapture | None = None

    def open(self):
        """打开摄像头并设置分辨率。"""
        self.cap = cv2.VideoCapture(self.index)
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开摄像头 {self.index}")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def read(self):
        """读取一帧，如果摄像头未打开抛异常。"""
        if self.cap is None:
            raise RuntimeError("摄像头未打开")
        return self.cap.read()

    def release(self):
        """释放摄像头资源。"""
        if self.cap is not None:
            self.cap.release()


#############################
# 数据集相关辅助函数         #
#############################

def _make_episode_name(ep_idx: int) -> str:
    """格式化生成单个 episode 的名称，格式为 episode_000000。"""
    return f"episode_{ep_idx:06d}"


def _init_video_writer(path: Path, fps: int, frame_shape: tuple[int, int, int]):
    """初始化一个视频写入器，编码格式为 mp4v。"""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    height, width, _ = frame_shape
    return cv2.VideoWriter(str(path), fourcc, fps, (width, height))


def _write_info_json(meta_dir: Path, fps: int):
    """写入 info.json，记录帧率和是否使用视频存储。"""
    info = {
        "fps": fps,
        "video": True,  # 标记帧是以视频形式存储，LeRobot loader 会解码视频
    }
    with (meta_dir / "info.json").open("w") as f:
        json.dump(info, f, indent=2)


def _append_jsonl(path: Path, data: dict):
    """向 jsonl 文件追加一行 JSON。"""
    with path.open("a") as f:
        json.dump(data, f)
        f.write("\n")


def record_dataset(args):
    """主录制函数，根据传入参数录制数据集。"""

    # 解析摄像头参数
    cam_specs: dict[str, int] = {}
    if args.camera is None:
        cam_specs = {"front": 0}
    else:
        for spec in args.camera:
            if "=" not in spec:
                raise ValueError(f"--camera 参数格式应为 name=index, 收到: {spec}")
            name, idx = spec.split("=", 1)
            cam_specs[name] = int(idx)
    if len(cam_specs) == 0:
        raise ValueError("至少需要定义一个摄像头")

    # 定义输出目录结构
    out_dir = Path(args.out_dir)
    meta_dir = out_dir / "meta"
    data_dir = out_dir / "data" / "chunk-000"
    video_dir_root = out_dir / "videos" / "chunk-000"

    # 创建所有需要的目录，存在则跳过
    video_dirs = [video_dir_root / f"observation.images.{name}" for name in cam_specs.keys()]
    for d in [meta_dir, data_dir, *video_dirs]:
        d.mkdir(parents=True, exist_ok=True)

    # 只写入一次 info.json
    _write_info_json(meta_dir, args.fps)

    # 如果 tasks.jsonl 不存在，写入默认任务（单任务）
    if not (meta_dir / "tasks.jsonl").exists():
        _append_jsonl(meta_dir / "tasks.jsonl", {"task_index": 0, "task": args.task})

    if len(cam_specs) == 0:
        raise ValueError("至少需要定义一个摄像头")

    # 创建并打开摄像头
    cam_readers: dict[str, OpenCVCameraReader] = {}
    for name, idx in cam_specs.items():
        reader = OpenCVCameraReader(idx, args.width, args.height)
        reader.open()
        cam_readers[name] = reader

    try:
        for ep in range(args.episodes):
            ep_name = _make_episode_name(ep)
            print(f"开始录制 {ep_name} …")
            rows = []  # 用于存储当前 episode 的帧元数据

            # 视频写入器，延迟初始化直到第一帧成功读取
            vw_writers = {name: None for name in cam_specs.keys()}

            start_t = time.time()
            frame_count = 0
            max_frames = math.ceil(args.duration * args.fps)
            while frame_count < max_frames:
                loop_start = time.time()

                # 从所有摄像头读取帧
                frames = []
                success = True
                for name, reader in cam_readers.items():
                    ok, frame = reader.read()
                    if not ok:
                        print(f"⚠️  摄像头 {name} 读取帧失败")
                        success = False
                        break
                    frames.append(frame)
                
                if not success:
                    continue

                # 初始化视频写入器（第一次成功读取帧时）
                if any(vw is None for vw in vw_writers.values()):
                    for cam_name, frame in zip(cam_specs.keys(), frames):
                        vw_writers[cam_name] = _init_video_writer(
                            (video_dir_root / f"observation.images.{cam_name}" / f"{ep_name}.mp4"),
                            args.fps,
                            frame.shape,
                        )

                # 写入视频帧
                for cam_name, frame in zip(cam_specs.keys(), frames):
                    vw_writers[cam_name].write(frame)

                # 记录当前帧时间戳和帧序号
                timestamp = time.time() - start_t
                rows.append({
                    "timestamp": timestamp,
                    "frame": frame_count,  # 对应视频中的帧索引
                })

                frame_count += 1

                # 检查是否达到最小帧数要求
                if frame_count >= args.min_frames:
                    print(f"已达到最小帧数要求 ({frame_count}/{args.min_frames})，结束当前 episode")
                    break

                # 控制帧率，忙等待直到下一个采样时间
                dt = 1 / args.fps - (time.time() - loop_start)
                if dt > 0:
                    time.sleep(dt)

            # 释放视频写入器
            for vw in vw_writers.values():
                vw.release()

            # 将元数据保存为 parquet 文件
            table = pa.Table.from_pandas(pd.DataFrame(rows))
            pq.write_table(table, data_dir / f"{ep_name}.parquet")

            # 追加当前 episode 的元数据到 episodes.jsonl
            _append_jsonl(meta_dir / "episodes.jsonl", {
                "episode_index": ep,
                "episode_length": frame_count,
                "tasks": [0],  # 关联任务索引
            })

            # 追加简单统计信息到 episodes_stats.jsonl（这里仅记录长度）
            _append_jsonl(meta_dir / "episodes_stats.jsonl", {
                "episode_index": ep,
                "stats": {"length": frame_count},
            })

            print(f"完成 {ep_name}，共录制 {frame_count} 帧")

    finally:
        # 确保摄像头资源释放
        for r in cam_readers.values():
            r.release()


def parse_args():
    """解析命令行参数。"""
    p = argparse.ArgumentParser(description="多摄像头 LeRobot 兼容数据集录制工具")
    p.add_argument("--out_dir", required=True, help="输出数据集根目录")
    p.add_argument("--episodes", type=int, default=10, help="录制的 episode 数量")
    p.add_argument("--duration", type=float, default=10, help="每个 episode 时长（秒）")
    p.add_argument("--min_frames", type=int, default=50, help="每个 episode 的最小帧数要求")
    p.add_argument("--fps", type=int, default=30, help="视频帧率")
    p.add_argument("--camera", action="append", metavar="NAME=IDX", help="摄像头定义，可以重复，例如 --camera front=0 --camera wrist=2 。不指定时默认为 front=0")
    p.add_argument("--width", type=int, default=640, help="视频宽度")
    p.add_argument("--height", type=int, default=480, help="视频高度")
    p.add_argument("--task", type=str, default="Custom task", help="任务的自然语言描述")
    return p.parse_args()


if __name__ == "__main__":
    record_dataset(parse_args())