#!/usr/bin/env python3
import cv2
import numpy as np
import glob
import json
import os

def apply_calibration(json_file, input_folder, output_root="outputs"):
    """
    使用标定参数校正指定文件夹下的所有SBS图像
    """
    # 1. 加载标定参数
    if not os.path.exists(json_file):
        print(f"❌ 错误：找不到标定文件 {json_file}")
        return

    with open(json_file, 'r') as f:
        calib = json.load(f)

    # 提取左眼和右眼的参数 (转换为 numpy 数组)
    K_l = np.array(calib['left']['K'])
    D_l = np.array(calib['left']['D'])
    K_r = np.array(calib['right']['K'])
    D_r = np.array(calib['right']['D'])

    # 2. 准备输出目录
    folder_name = os.path.basename(os.path.normpath(input_folder))
    save_dir = os.path.join(output_root, folder_name + "_undistorted")
    os.makedirs(save_dir, exist_ok=True)

    # 3. 获取输入图片
    img_list = []
    for ext in ["jpg", "png", "jpeg", "JPG", "PNG"]:
        img_list.extend(glob.glob(os.path.join(input_folder, f"*.{ext}")))
    
    if not img_list:
        print(f"❌ 错误：在 {input_folder} 中没找到图片")
        return

    print(f"🚀 开始校正 {len(img_list)} 张图片...")

    # 4. 初始化映射表 (只需要计算一次)
    # 假设所有图片尺寸一致，取第一张图确定尺寸
    first_img = cv2.imread(img_list[0])
    h, w = first_img.shape[:2]
    half_w = w // 2
    img_size = (half_w, h)

    # 构建鱼眼映射表 (映射表可以极大加快处理速度)
    map1_l, map2_l = cv2.fisheye.initUndistortRectifyMap(K_l, D_l, np.eye(3), K_l, img_size, cv2.CV_16SC2)
    map1_r, map2_r = cv2.fisheye.initUndistortRectifyMap(K_r, D_r, np.eye(3), K_r, img_size, cv2.CV_16SC2)

    # 5. 循环处理
    for img_path in img_list:
        img = cv2.imread(img_path)
        if img is None: continue

        # 分离左右
        left_eye = img[:, :half_w]
        right_eye = img[:, half_w:]

        # 应用校正 (Remap)
        undist_l = cv2.remap(left_eye, map1_l, map2_l, interpolation=cv2.INTER_LINEAR)
        undist_r = cv2.remap(right_eye, map1_r, map2_r, interpolation=cv2.INTER_LINEAR)

        # 拼回 SBS 格式
        result = np.hstack((undist_l, undist_r))

        # 保存
        out_name = "rectified_" + os.path.basename(img_path)
        cv2.imwrite(os.path.join(save_dir, out_name), result)
        print(f"✅ 已保存: {out_name}")

    print(f"\n✨ 所有校正后的图片已存至: {save_dir}")

if __name__ == "__main__":
    # 配置路径
    CALIB_JSON = "sbs_camera_calibration.json"
    INPUT_DIR = "data/fangkuai"
    
    apply_calibration(CALIB_JSON, INPUT_DIR)