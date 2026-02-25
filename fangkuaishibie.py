#!/usr/bin/env python3
import cv2
import numpy as np
import glob
import os

def detect_square_corners(img_path, output_dir):
    # 1. 读取图像
    img = cv2.imread(img_path)
    if img is None: return
    
    display_img = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. 预处理
    # 增加对比度并进行高斯模糊，减少白纸表面的杂质干扰
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 二值化：黑方块在白纸上，使用自适应阈值或大津法
    # 因为平拍可能会有光照不均，自适应阈值效果更好
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)

    # 3. 轮廓检测
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    found_squares = 0
    for cnt in contours:
        # 筛选：面积不能太小
        area = cv2.contourArea(cnt)
        if area < 1000: continue 
        
        # 周长逼近
        peri = cv2.arcLength(cnt, True)
        # 核心：多边形拟合。0.02~0.05 是精度参数，越小越贴合轮廓
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)

        # 4. 如果拟合结果是 4 个点，则认为是方块
        if len(approx) == 4:
            found_squares += 1
            # 整理角点坐标
            pts = approx.reshape(4, 2)
            
            # 为四个点排序（左上、右上、右下、左下）
            rect = np.zeros((4, 2), dtype="float32")
            s = pts.sum(axis=1)
            rect[0] = pts[np.argmin(s)]
            rect[2] = pts[np.argmax(s)]
            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]
            rect[3] = pts[np.argmax(diff)]

            # 绘制轮廓和角点
            cv2.drawContours(display_img, [approx], -1, (0, 255, 0), 2)
            for i, (x, y) in enumerate(rect):
                cv2.circle(display_img, (int(x), int(y)), 8, (0, 0, 255), -1)
                cv2.putText(display_img, f"P{i}", (int(x), int(y)-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

            print(f"📍 在 {os.path.basename(img_path)} 中检测到方块角点: \n{rect}")

    # 5. 保存结果
    if found_squares > 0:
        out_path = os.path.join(output_dir, "detected_" + os.path.basename(img_path))
        cv2.imwrite(out_path, display_img)
    else:
        print(f"❓ {os.path.basename(img_path)} 未能识别到方块")

def main():
    # 指向你刚才校正后的图片文件夹
    INPUT_DIR = "outputs/fangkuai_undistorted"
    RESULT_DIR = "outputs/detected_corners"
    os.makedirs(RESULT_DIR, exist_ok=True)

    img_list = []
    for ext in ["jpg", "png", "jpeg"]:
        img_list.extend(glob.glob(os.path.join(INPUT_DIR, f"*.{ext}")))

    if not img_list:
        print("❌ 找不到校正后的图片，请检查路径")
        return

    for path in img_list:
        detect_square_corners(path, RESULT_DIR)

if __name__ == "__main__":
    main()