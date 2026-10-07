import numpy as np
import cv2
from pathlib import Path
from starter.datasets import load_frame
from starter.projection import perturb_extrinsic, project_velo_to_image, overlay_points, draw_box2d

def in_box2d(uv, bbox):
    x1, y1, x2, y2 = bbox
    return (uv[:, 0] >= x1) & (uv[:, 0] <= x2) & (uv[:, 1] >= y1) & (uv[:, 1] <= y2)

def main():
    frame_id = "000011"
    data_root = "data/kitti_mini"
    
    fr = load_frame(data_root, frame_id)
    points = fr["points"]
    calib = fr["calib"]
    image = fr["image"]
    labels = fr["labels"]
    
    def count_points_in_boxes(uv):
        in_any_box = np.zeros(len(uv), dtype=bool)
        for obj in labels:
            if obj.type == "DontCare": continue
            in_any_box |= in_box2d(uv, obj.bbox)
        return in_any_box.sum()
        
    configs = [
        {"yaw_deg": 0.0, "tx": 0.0, "name": "Baseline (Không nhiễu)"},
        {"yaw_deg": 1.0, "tx": 0.0, "name": "Lệch Yaw +1.0°"},
        {"yaw_deg": 2.0, "tx": 0.0, "name": "Lệch Yaw +2.0°"},
        {"yaw_deg": 3.0, "tx": 0.0, "name": "Lệch Yaw +3.0°"},
        {"yaw_deg": 0.0, "tx": 0.05, "name": "Lệch Tx +5 cm"},
        {"yaw_deg": 0.0, "tx": 0.10, "name": "Lệch Tx +10 cm"},
    ]
    
    print("| Cấu hình / mức perturb | % điểm inside FOV | % điểm rơi vào 2D box | Ghi chú |")
    print("|---|---|---|---|")
    
    for cfg in configs:
        c = perturb_extrinsic(calib, yaw_deg=cfg["yaw_deg"], t_xyz_m=(cfg["tx"], 0, 0))
        uv, depth, mask = project_velo_to_image(points, c, image.shape)
        
        pct_fov = mask.sum() / len(points) * 100
        
        pts_in_box = count_points_in_boxes(uv)
        pct_in_box = pts_in_box / mask.sum() * 100 if mask.sum() > 0 else 0
        
        note = "Chuẩn" if cfg["name"] == "Baseline (Không nhiễu)" else "Giảm dần"
        print(f"| {cfg['name']} | {pct_fov:.2f}% | {pct_in_box:.2f}% | {note} |")
        
        # Save a failure case image when yaw drift is large
        if cfg["yaw_deg"] == 3.0:
            vis = overlay_points(image, uv, depth)
            for obj in labels:
                if obj.type == "DontCare": continue
                vis = draw_box2d(vis, obj.bbox, label=obj.type)
            
            out = Path("results/figures/fail_yaw_3deg.png")
            out.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(out), vis)

if __name__ == "__main__":
    main()

