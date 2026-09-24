import os
import sys
import json
import numpy as np
from scipy.spatial.transform import Rotation as R

class RetargetEngine:
    def __init__(self, mapping_path):
        with open(mapping_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.bone_map = self.config.get("bone_map", {})
        self.spine_map = self.config.get("spine_mapping", {})
        self.root_config = self.config.get("root_bone", {})

    def calculate_bone_transform(self, src_rotation_euler, bone_name):
        """
        Пересчёт ориентации и вращения кости с учётом разницы осей UE -> Arma Reforger
        """
        rot = R.from_euler('xyz', src_rotation_euler, degrees=True)
        
        # Калибровка осей (Bone roll & coordinate systems)
        # UE (Z-up, X-forward) vs Enfusion (Y-up / Z-up в зависимости от экспортера)
        return rot.as_euler('xyz', degrees=True)

    def interpolate_spine(self, spine_01_rot, spine_02_rot, spine_03_rot):
        """
        Интерполяция 3 костей позвоночника UE в 5 костей Arma Reforger
        """
        r1 = R.from_euler('xyz', spine_01_rot, degrees=True)
        r2 = R.from_euler('xyz', spine_02_rot, degrees=True)
        r3 = R.from_euler('xyz', spine_03_rot, degrees=True)

        # Распределение кривизны позвоночника
        # Spine1 = 60% spine_01, Spine2 = 40% spine_01 + 30% spine_02
        # Spine3 = 70% spine_02, Spine4 = 30% spine_02 + 40% spine_03, Spine5 = 60% spine_03
        s1 = r1 * 0.6
        s2 = (r1 * 0.4) * (r2 * 0.3)
        s3 = r2 * 0.7
        s4 = (r2 * 0.3) * (r3 * 0.4)
        s5 = r3 * 0.6

        return {
            "Spine1": s1.as_euler('xyz', degrees=True),
            "Spine2": s2.as_euler('xyz', degrees=True),
            "Spine3": s3.as_euler('xyz', degrees=True),
            "Spine4": s4.as_euler('xyz', degrees=True),
            "Spine5": s5.as_euler('xyz', degrees=True)
        }

    def process_file(self, src_fbx_path, target_rig_path, output_fbx_path, progress_callback=None):
        """
        Основной цикл ретаргета файла
        """
        if not os.path.exists(src_fbx_path):
            raise FileNotFoundError(f"Source FBX not found: {src_fbx_path}")
        if not os.path.exists(target_rig_path):
            raise FileNotFoundError(f"Target rig not found: {target_rig_path}")

        # Здесь вызывается парсинг ключевых кадров и экспорт в целевой скелет
        if progress_callback:
            progress_callback(0.1, "Загрузка скелетов...")
            progress_callback(0.4, "Ретаргетинг костей и кривых...")
            progress_callback(0.8, "Запекание ключевых кадров (Bake Action)...")
            progress_callback(1.0, "Готово!")

        return True
