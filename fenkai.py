#!/usr/bin/env python3
import cv2
import os
import glob

def split_sbs_images(input_folder, output_root="outputs"):
    """
    将SBS拼接图像对半切分，并存入对应的 zuo/you 文件夹
    """
    # 1. 自动推导文件夹名称
    # 假设输入路径是 outputs/pipe0，提取出 'pipe0'
    base_folder_name = os.path.basename(os.path.normpath(input_folder))
    
    # 拼接新的输出文件夹名
    left_dir = os.path.join(output_root, f"{base_folder_name}_zuo_yuan")
    right_dir = os.path.join(output_root, f"{base_folder_name}_you_yuan")
    
    # 创建文件夹
    os.makedirs(left_dir, exist_ok=True)
    os.makedirs(right_dir, exist_ok=True)

    # 2. 获取所有校正后的图片
    img_list = []
    for ext in ["jpg", "png", "jpeg", "JPG", "PNG"]:
        img_list.extend(glob.glob(os.path.join(input_folder, f"*.{ext}")))

    if not img_list:
        print(f"❌ 在 {input_folder} 中未找到校正后的图片。")
        return

    print(f"🚀 开始切分 {len(img_list)} 张图片...")

    # 3. 执行切分逻辑
    for img_path in img_list:
        img = cv2.imread(img_path)
        if img is None: continue
        
        h, w = img.shape[:2]
        half_w = w // 2
        
        # 左右对半切分
        img_left = img[:, :half_w]
        img_right = img[:, half_w:]
        
        # 保持原始文件名
        file_name = os.path.basename(img_path)
        
        # 存储
        cv2.imwrite(os.path.join(left_dir, file_name), img_left)
        cv2.imwrite(os.path.join(right_dir, file_name), img_right)
        
        print(f"✅ 已处理: {file_name}")

    print(f"\n✨ 切分完成！")
    print(f"📁 左侧图片存至: {left_dir}")
    print(f"📁 右侧图片存至: {right_dir}")

if __name__ == "__main__":
    # 配置你的输入目录
    # 根据你的描述，校正后的图片放在 outputs/pipe0 
    INPUT_FOLDER = "data/pipe0"
    
    split_sbs_images(INPUT_FOLDER)
