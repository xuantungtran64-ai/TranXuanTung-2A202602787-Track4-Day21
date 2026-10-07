import numpy as np
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
from starter.datasets import load_frame
from starter.projection import perturb_extrinsic, project_velo_to_image, overlay_points, draw_box2d

def get_alignment_score(pts, calib, img_shape, labels, yaw_deg):
    c = perturb_extrinsic(calib, yaw_deg=yaw_deg)
    uv, depth, mask = project_velo_to_image(pts, c, img_shape)
    
    valid_pts = 0
    for obj in labels:
        if obj.type == 'DontCare': continue
        x1, y1, x2, y2 = obj.bbox
        obj_z = obj.location[2]
        
        in_box = (uv[:, 0] >= x1) & (uv[:, 0] <= x2) & (uv[:, 1] >= y1) & (uv[:, 1] <= y2)
        valid_depth = np.abs(depth - obj_z) < 3.0
        valid_pts += np.sum(in_box & valid_depth)
        
    return valid_pts, uv, depth

def main():
    yaws = np.linspace(0, 3, 10)
    
    # Process success case
    fr11 = load_frame('data/kitti_mini', '000011')
    base_11, _, _ = get_alignment_score(fr11['points'], fr11['calib'], fr11['image'].shape, fr11['labels'], 0)
    scores_11 = []
    for y in yaws:
        v, _, _ = get_alignment_score(fr11['points'], fr11['calib'], fr11['image'].shape, fr11['labels'], y)
        scores_11.append(v / base_11 if base_11 > 0 else 0)
        
    # Process failure case
    fr21 = load_frame('data/kitti_mini', '000021')
    base_21, _, _ = get_alignment_score(fr21['points'], fr21['calib'], fr21['image'].shape, fr21['labels'], 0)
    scores_21 = []
    fail_uv = fail_depth = None
    for y in yaws:
        v, uv, depth = get_alignment_score(fr21['points'], fr21['calib'], fr21['image'].shape, fr21['labels'], y)
        scores_21.append(v / base_21 if base_21 > 0 else 0)
        if y == 3.0:
            fail_uv, fail_depth = uv, depth

    # Plot
    plt.figure(figsize=(8, 5))
    plt.plot(yaws, scores_11, marker='o', label='Frame 000011 (Normal object)')
    plt.plot(yaws, scores_21, marker='x', label='Frame 000021 (Failure case)')
    plt.axhline(y=0.7, color='r', linestyle='--', label='Cảnh báo Threshold (0.7)')
    plt.title('Alignment Score vs Yaw Drift')
    plt.xlabel('Yaw Drift (Degrees)')
    plt.ylabel('Alignment Score (Tỉ lệ điểm trong Box)')
    plt.legend()
    plt.grid(True)
    
    out_dir = Path("results/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_dir / "advanced_plot.png")
    
    # Save failure case image
    vis = overlay_points(fr21['image'], fail_uv, fail_depth)
    for obj in fr21['labels']:
        if obj.type == 'DontCare': continue
        vis = draw_box2d(vis, obj.bbox, label=obj.type)
    cv2.imwrite(str(out_dir / "fail_advanced.png"), vis)
    
    import csv
    with open(out_dir / "advanced_scores.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Yaw_Drift_Deg", "Score_Frame_000011", "Score_Frame_000021"])
        for y, s11, s21 in zip(yaws, scores_11, scores_21):
            writer.writerow([f"{y:.2f}", f"{s11:.4f}", f"{s21:.4f}"])
            
    print("Xong! Đã lưu plot, csv và failure case.")

if __name__ == '__main__':
    main()

