#!/usr/bin/env python3
import cv2
import numpy as np
import glob
import json
import os
import matplotlib.pyplot as plt

def calibrate_sbs_cameras(images_folder, pattern_size, square_size, output_file):
    """
    标定SBS图像中的左右相机内参，输出误差到终端并生成误差图
    """
    # 路径映射
    folder_name = os.path.basename(os.path.normpath(images_folder))
    vis_output_dir = os.path.join("outputs", folder_name)
    os.makedirs(vis_output_dir, exist_ok=True)

    # 准备对象点 (3D points)
    objp = np.zeros((1, pattern_size[0] * pattern_size[1], 3), np.float32)
    objp[0, :, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)
    objp *= square_size

    obj_points_left, img_points_left = [], []
    obj_points_right, img_points_right = [], []
    valid_fnames = [] 

    # 获取图像文件
    image_patterns = [os.path.join(images_folder, f"*.{ext}") for ext in ["jpg", "png", "jpeg", "JPG", "PNG", "JPEG"]]
    images = []
    for pattern in image_patterns:
        images.extend(glob.glob(pattern))
    images.sort()

    if not images:
        print(f"❌ 错误：未找到图片文件！")
        return None

    # --- 阶段 1: 角点检测 ---
    for fname in images:
        img = cv2.imread(fname)
        if img is None: continue
        h, w = img.shape[:2]
        half_w = w // 2
        img_left, img_right = img[:, :half_w], img[:, half_w:]
        
        gray_l = cv2.cvtColor(img_left, cv2.COLOR_BGR2GRAY)
        gray_r = cv2.cvtColor(img_right, cv2.COLOR_BGR2GRAY)

        ret_l, cor_l = cv2.findChessboardCorners(gray_l, pattern_size, cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE)
        ret_r, cor_r = cv2.findChessboardCorners(gray_r, pattern_size, cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE)
        
        if ret_l and ret_r:
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            cor_l = cv2.cornerSubPix(gray_l, cor_l, (11, 11), (-1, -1), criteria)
            cor_r = cv2.cornerSubPix(gray_r, cor_r, (11, 11), (-1, -1), criteria)
            obj_points_left.append(objp); img_points_left.append(cor_l)
            obj_points_right.append(objp); img_points_right.append(cor_r)
            valid_fnames.append(os.path.basename(fname))

    if len(obj_points_left) < 5:
        print("❌ 成功检测数太少，无法标定")
        return None

    image_size = (half_w, h)

    # --- 阶段 2: 标定与误差计算 ---
    def run_calib(obj_pts, img_pts, label):
        K = np.zeros((3, 3)); D = np.zeros((4, 1))
        # 鱼眼标定
        ret, K, D, rvecs, tvecs = cv2.fisheye.calibrate(
            obj_pts, img_pts, image_size, K, D,
            flags=cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC + cv2.fisheye.CALIB_FIX_SKEW,
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6)
        )
        
        # 精确计算每张图的重投影误差
        errors = []
        for i in range(len(obj_pts)):
            reproj_pts, _ = cv2.fisheye.projectPoints(obj_pts[i], rvecs[i], tvecs[i], K, D)
            # 解决形状不匹配报错
            p_orig = img_pts[i].reshape(-1, 2)
            p_repro = reproj_pts.reshape(-1, 2)
            err = cv2.norm(p_orig, p_repro, cv2.NORM_L2) / len(p_repro)
            errors.append(err)
        
        mean_err = np.mean(errors)
        print(f"📊 {label}相机平均重投影误差: {mean_err:.5f} 像素")
        return K, D, errors, mean_err

    print(f"\n--- 开始标定计算 ({folder_name}) ---")
    K_l, D_l, err_list_l, mean_l = run_calib(obj_points_left, img_points_left, "左眼")
    K_r, D_r, err_list_r, mean_r = run_calib(obj_points_right, img_points_right, "右眼")

    # --- 阶段 3: 绘制误差分布图 ---
    plt.figure(figsize=(12, 6))
    x = np.arange(len(valid_fnames))
    plt.bar(x - 0.2, err_list_l, 0.4, label=f'Left (Mean: {mean_l:.3f})', color='royalblue')
    plt.bar(x + 0.2, err_list_r, 0.4, label=f'Right (Mean: {mean_r:.3f})', color='darkorange')
    
    # 画平均值参考线
    plt.axhline(y=mean_l, color='blue', linestyle='--', alpha=0.4)
    plt.axhline(y=mean_r, color='orange', linestyle='--', alpha=0.4)
    
    plt.xticks(x, valid_fnames, rotation=45, ha='right', fontsize=8)
    plt.ylabel("Reprojection Error (pixels)")
    plt.title(f"Reprojection Error Per Image - {folder_name}")
    plt.legend()
    plt.tight_layout()
    
    plot_path = os.path.join(vis_output_dir, "reprojection_error.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"📈 误差分布图已保存至: {plot_path}")

    # --- 阶段 4: 保存去畸变对比图 (前10张) ---
    map1_l, map2_l = cv2.fisheye.initUndistortRectifyMap(K_l, D_l, np.eye(3), K_l, image_size, cv2.CV_16SC2)
    map1_r, map2_r = cv2.fisheye.initUndistortRectifyMap(K_r, D_r, np.eye(3), K_r, image_size, cv2.CV_16SC2)

    for i in range(min(10, len(valid_fnames))):
        fname = os.path.join(images_folder, valid_fnames[i])
        img = cv2.imread(fname)
        u_l = cv2.remap(img[:, :half_w], map1_l, map2_l, cv2.INTER_LINEAR)
        u_r = cv2.remap(img[:, half_w:], map1_r, map2_r, cv2.INTER_LINEAR)
        cv2.imwrite(os.path.join(vis_output_dir, "undistorted_" + valid_fnames[i]), np.hstack((u_l, u_r)))

    # 保存 JSON
    res = {"left": {"K": K_l.tolist(), "D": D_l.tolist(), "avg_err": float(mean_l)},
           "right": {"K": K_r.tolist(), "D": D_r.tolist(), "avg_err": float(mean_r)}}
    with open(output_file, 'w') as f:
        json.dump(res, f, indent=4)
    
    print(f"✅ 标定 JSON 已保存: {output_file}")
    return res

def main():
    SBS_IMAGES_FOLDER = "data/pipe0"
    OUTPUT_FILE = "sbs_camera_calibration.json"
    PATTERN_SIZE = (14, 14)
    SQUARE_SIZE = 0.025 

    if not os.path.exists(SBS_IMAGES_FOLDER):
        print(f"❌ 找不到数据文件夹: {SBS_IMAGES_FOLDER}")
        return

    calibrate_sbs_cameras(SBS_IMAGES_FOLDER, PATTERN_SIZE, SQUARE_SIZE, OUTPUT_FILE)

if __name__ == "__main__":
    main()