# GMSL 双目相机标定与图像处理系统

这是一个用于 GMSL 双目相机（Side-by-Side 格式）的标定和图像处理工具集，支持鱼眼镜头畸变校正、图像分离和方块角点检测。

## 项目概述

本项目主要用于处理双目相机拍摄的 SBS（Side-by-Side）格式图像，提供完整的相机标定、畸变校正和图像分析功能。适用于需要精确相机内参标定的计算机视觉应用场景。

## 功能特性

- 🎯 双目相机内参标定（支持鱼眼镜头）
- 📊 重投影误差可视化分析
- 🔧 图像畸变校正（去畸变）
- ✂️ SBS 图像左右分离
- 🔍 方块角点自动检测

## 项目结构

```
.
├── Gmsl camera calibration.py    # 主标定程序
├── jiaozhengdaima.py             # 畸变校正程序
├── fenkai.py                     # 图像分离程序
├── fangkuaishibie.py             # 方块角点检测程序
├── requirements.txt              # Python 依赖包
├── sbs_camera_calibration.json   # 标定结果文件
├── data/                         # 数据目录
│   ├── pipe0/                    # 标定用棋盘格图像
│   └── fangkuai/                 # 待处理的方块图像
└── outputs/                      # 输出结果目录
```

## 文件说明

### 核心程序文件

#### 1. `Gmsl camera calibration.py`
**功能**: 双目相机内参标定主程序

**主要特性**:
- 自动检测 SBS 图像中的棋盘格角点
- 使用鱼眼相机模型进行标定
- 计算并输出每张图像的重投影误差
- 生成误差分布图表
- 保存前 10 张去畸变对比图
- 输出标定参数到 JSON 文件

**关键参数**:
- `PATTERN_SIZE`: 棋盘格内角点数量 (默认: 14x14)
- `SQUARE_SIZE`: 棋盘格方格实际尺寸 (默认: 0.025 米)
- `SBS_IMAGES_FOLDER`: 标定图像文件夹路径
- `OUTPUT_FILE`: 标定结果保存路径

**输出**:
- `sbs_camera_calibration.json`: 左右相机的内参矩阵 K、畸变系数 D 和平均误差
- `outputs/<folder_name>/reprojection_error.png`: 重投影误差分布图
- `outputs/<folder_name>/undistorted_*.jpg`: 去畸变对比图

#### 2. `jiaozhengdaima.py`
**功能**: 使用标定参数对图像进行畸变校正

**工作流程**:
1. 加载标定参数文件 (`sbs_camera_calibration.json`)
2. 读取待校正的 SBS 图像
3. 分离左右图像
4. 应用鱼眼去畸变映射
5. 重新拼接为 SBS 格式并保存

**输出**:
- `outputs/<folder_name>_undistorted/rectified_*.jpg`: 校正后的图像

#### 3. `fenkai.py`
**功能**: 将 SBS 拼接图像分离为独立的左右图像

**工作流程**:
1. 读取 SBS 格式图像
2. 按中线对半切分
3. 分别保存到左眼和右眼文件夹

**输出**:
- `outputs/<folder_name>_zuo_yuan/`: 左眼图像
- `outputs/<folder_name>_you_yuan/`: 右眼图像

#### 4. `fangkuaishibie.py`
**功能**: 检测图像中的方块并标记四个角点

**技术方案**:
- 自适应阈值二值化
- 轮廓检测与多边形拟合
- 四边形筛选与角点排序
- 可视化标注

**输出**:
- `outputs/detected_corners/detected_*.jpg`: 标注了角点的图像
- 终端输出角点坐标

### 配置文件

#### `requirements.txt`
项目 Python 依赖包列表:
- `opencv-python>=4.5.0`: 计算机视觉库
- `numpy>=1.19.0`: 数值计算库
- `matplotlib>=3.3.0`: 数据可视化（标定程序需要）

#### `sbs_camera_calibration.json`
标定结果文件，包含:
- `left.K`: 左相机内参矩阵 (3x3)
- `left.D`: 左相机畸变系数 (4x1)
- `left.avg_err`: 左相机平均重投影误差
- `right.K`: 右相机内参矩阵 (3x3)
- `right.D`: 右相机畸变系数 (4x1)
- `right.avg_err`: 右相机平均重投影误差

## 环境要求

- Python 3.7 或更高版本
- Linux / macOS / Windows 操作系统

## 安装步骤

### 1. 克隆或下载项目

```bash
git clone <repository_url>
cd <project_directory>
```

### 2. 创建虚拟环境（推荐）

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖包

```bash
pip install -r requirements.txt
```

### 4. 验证安装

```bash
python -c "import cv2; import numpy as np; print('OpenCV 版本:', cv2.__version__)"
```

## 使用方法

### 完整工作流程

#### 步骤 1: 相机标定

准备标定数据:
- 使用棋盘格标定板（推荐 14x14 内角点）
- 拍摄 15-30 张不同角度和位置的 SBS 格式图像
- 将图像放入 `data/pipe0/` 目录

运行标定程序:

```bash
python "Gmsl camera calibration.py"
```

**输出结果**:
- 终端显示左右相机的平均重投影误差
- 生成 `sbs_camera_calibration.json` 标定文件
- 在 `outputs/pipe0/` 生成误差分析图和去畸变对比图

**标定质量评估**:
- 重投影误差 < 0.5 像素: 优秀
- 重投影误差 0.5-1.0 像素: 良好
- 重投影误差 > 1.0 像素: 需要重新标定

#### 步骤 2: 图像畸变校正

将待处理的 SBS 图像放入 `data/fangkuai/` 目录，然后运行:

```bash
python jiaozhengdaima.py
```

**输出**: `outputs/fangkuai_undistorted/` 目录下的校正图像

#### 步骤 3: 图像分离（可选）

如果需要将 SBS 图像分离为独立的左右图像:

```bash
python fenkai.py
```

**输出**:
- `outputs/pipe0_zuo_yuan/`: 左眼图像
- `outputs/pipe0_you_yuan/`: 右眼图像

#### 步骤 4: 方块角点检测（可选）

对校正后的图像进行方块检测:

```bash
python fangkuaishibie.py
```

**输出**: `outputs/detected_corners/` 目录下标注了角点的图像

### 自定义配置

#### 修改标定参数

编辑 `Gmsl camera calibration.py` 中的参数:

```python
PATTERN_SIZE = (14, 14)      # 棋盘格内角点数量
SQUARE_SIZE = 0.025          # 方格实际尺寸（米）
SBS_IMAGES_FOLDER = "data/pipe0"  # 标定图像路径
```

#### 修改校正输入路径

编辑 `jiaozhengdaima.py`:

```python
CALIB_JSON = "sbs_camera_calibration.json"  # 标定文件路径
INPUT_DIR = "data/fangkuai"                 # 待校正图像路径
```

#### 修改分离输入路径

编辑 `fenkai.py`:

```python
INPUT_FOLDER = "data/pipe0"  # SBS 图像路径
```

## 数据目录说明

### `data/pipe0/`
存放用于相机标定的棋盘格 SBS 图像。图像命名格式示例:
- `pipe0_2560x800_<timestamp>_stitched.jpg`

### `data/fangkuai/`
存放待处理的方块图像，包含:
- 原始 SBS 拼接图像 (`*_stitched.jpg`)
- 左右分离图像 (`*_left.jpg`, `*_right.jpg`)
- 子目录 `photo/` 存放额外的图像数据

## 输出目录说明

### `outputs/<folder_name>/`
标定程序输出:
- `reprojection_error.png`: 重投影误差柱状图
- `undistorted_*.jpg`: 前 10 张去畸变对比图

### `outputs/<folder_name>_undistorted/`
校正程序输出:
- `rectified_*.jpg`: 去畸变后的 SBS 图像

### `outputs/<folder_name>_zuo_yuan/` 和 `outputs/<folder_name>_you_yuan/`
分离程序输出:
- 独立的左眼和右眼图像

### `outputs/detected_corners/`
角点检测程序输出:
- `detected_*.jpg`: 标注了方块角点的图像

## 常见问题

### Q1: 标定失败，提示"成功检测数太少"
**解决方案**:
- 确保棋盘格清晰可见，光照均匀
- 检查 `PATTERN_SIZE` 参数是否与实际棋盘格匹配
- 增加标定图像数量（建议 20 张以上）
- 确保图像包含不同角度和位置的棋盘格

### Q2: 重投影误差过大
**解决方案**:
- 重新拍摄标定图像，确保棋盘格平整
- 增加标定图像的多样性（不同角度、距离、位置）
- 检查相机是否稳定，避免运动模糊
- 确认 `SQUARE_SIZE` 参数与实际尺寸一致

### Q3: 找不到图片文件
**解决方案**:
- 检查图像文件路径是否正确
- 确认图像格式为 jpg/png/jpeg
- 检查文件权限

### Q4: 方块检测失败
**解决方案**:
- 确保方块与背景对比度足够高
- 调整 `fangkuaishibie.py` 中的阈值参数
- 确保输入图像已经过畸变校正

## 技术细节

### 标定算法
- 使用 OpenCV 的 `cv2.fisheye.calibrate` 进行鱼眼相机标定
- 采用棋盘格角点亚像素精度优化
- 支持自动重投影误差计算和可视化

### 畸变模型
- 鱼眼镜头畸变模型（4 参数）
- 内参矩阵 K (3x3): 包含焦距和主点坐标
- 畸变系数 D (4x1): k1, k2, k3, k4

### 图像处理
- 使用 `cv2.remap` 进行高效的畸变校正
- 预计算映射表以加速批量处理
- 支持双线性插值

## 许可证

请根据项目实际情况添加许可证信息。

## 贡献

欢迎提交 Issue 和 Pull Request。

## 联系方式

如有问题或建议，请通过以下方式联系:
- 提交 GitHub Issue
- 发送邮件至 [email]

---

**最后更新**: 2026-02-25
