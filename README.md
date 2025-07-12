# LeRobot Dataset Recording Tool - LeRobot_CamRec

<div>

[![LeRobot_CamRec](https://img.shields.io/badge/LeRobot_CamRec-v1.0.0-blueviolet)](https://github.com/AIResearcherHZ/LeRobot_CamRec)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green)](https://github.com/AIResearcherHZ/LeRobot_CamRec/blob/main/LICENSE)

</div>

[Chinese Version](README_zh.md) | [English Version](README_en.md)

## Table of Contents
- [Introduction](#introduction)
- [Installation](#installation)
- [Preparatory Step: Camera Detection](#preparatory-step-camera-detection)
- [Usage Example](#usage-example)
- [Generated Directory Structure](#generated-directory-structure)
- [Dataset Loading](#dataset-loading)
- [Extended Notes](#extended-notes)

## Introduction
LeRobot_CamRec is a multi-camera data collection tool designed to save captured data in the folder structure of the LeRobot dataset. This tool supports efficient and ordered synchronous recording of multi-camera video streams, facilitating dataset management and subsequent loading/usage on the LeRobot platform.

## Installation
### Dependency Requirements
It does not rely on the complete `lerobot` framework. Only the following Python libraries need to be installed:

```bash
pip install opencv-python pandas pyarrow
```

## Preparatory Step: Camera Detection
Before starting recording, it is recommended to first run `find_camera.py` to detect available camera ports:

```bash
python find_camera.py
```

Example output:
```
Detected available cameras:
- Camera 0: Intel(R) RealSense(TM) Depth Camera 435
- Camera 1: Logitech Webcam C920
```

Record the indices of the cameras to be used (e.g., 0 and 1 in the example) for subsequent recording.

## Usage Example
```bash
python record_custom_dataset.py \
    --out_dir /home/xhz/lerobot/my_dataset \
    --episodes 10 \
    --duration 8 \
    --fps 30 \
    --front_cam 0 \
    --wrist_cam 2
```

## Generated Directory Structure
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

## Dataset Loading
The dataset can be loaded via LeRobot subsequently:

```python
from lerobot.datasets import LeRobotDataset
# Load the dataset (root parameter is the project root directory, optional)
ds = LeRobotDataset("my_dataset", root="/path/to/lerobot")
```

## Extended Notes
The program only writes the minimum metadata fields required by the LeRobot loader. Users can extend additional robot state or action data as needed.