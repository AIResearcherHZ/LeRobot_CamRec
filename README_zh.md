# LeRobot 数据集录制工具——LeRobot_CamRec

<div>

[![LeRobot_CamRec](https://img.shields.io/badge/LeRobot_CamRec-v1.0.0-blueviolet)](https://github.com/AIResearcherHZ/LeRobot_CamRec)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green)](https://github.com/AIResearcherHZ/LeRobot_CamRec/blob/main/LICENSE)

</div>

[英文版](README.md) | [中文版](README_zh.md)

## 目录
- [简介](#简介)
- [安装](#安装)
- [前置准备：检测摄像头](#前置准备检测摄像头)
- [使用示例](#使用示例)
- [生成的文件夹结构](#生成的文件夹结构)
- [数据集加载](#数据集加载)
- [扩展说明](#扩展说明)

## 简介
LeRobot_CamRec 是一个多摄像头数据采集工具，能够按照 LeRobot 数据集的文件夹结构保存采集到的数据。该工具支持高效、有序地同步录制多摄像头视频流，便于数据集的管理及后续在 LeRobot 平台上的加载与使用。

## 安装
### 依赖要求
不依赖完整的 `lerobot` 框架，仅需安装以下Python库：

```bash
pip install opencv-python pandas pyarrow
```

## 前置准备：检测摄像头
在开始录制前，建议先运行 `find_camera.py` 检测可用摄像头端口：

```bash
python find_camera.py
```

输出示例：
```
检测到可用摄像头：
- 摄像头0: Intel(R) RealSense(TM) Depth Camera 435
- 摄像头1: Logitech Webcam C920
```

记录需要使用的摄像头索引（如示例中的0和1），后续录制时使用。

## 使用示例
```bash
python record_custom_dataset.py \
    --out_dir /home/xhz/lerobot/my_dataset \
    --episodes 10 \
    --duration 8 \
    --fps 30 \
    --front_cam 0 \
    --wrist_cam 2
```

## 生成的文件夹结构
```
my_dataset/
    meta/
        info.json
        tasks.jsonl
        episodes.jsonl
    data/
        chunk-000/
            episode_000000.parquet
            ...
    videos/
        chunk-000/
            observation.images.front/episode_000000.mp4
            observation.images.wrist/episode_000000.mp4
```

## 数据集加载
后续可通过 LeRobot 加载数据集：
```python
from lerobot.datasets import LeRobotDataset
# 加载数据集（root参数为项目根目录，可选）
ds = LeRobotDataset("my_dataset", root="/path/to/lerobot")
```

## 扩展说明
程序仅写入 LeRobot 加载器需要的最小元数据字段，用户可根据需求扩展额外机器人状态或动作数据。