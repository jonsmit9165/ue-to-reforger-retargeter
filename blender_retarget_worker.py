import bpy
import sys
import json
import os

def retarget(src_fbx, target_rig_fbx, output_fbx, mapping_json_path):
    print(f"[RETARGET] Starting: {src_fbx} -> {output_fbx}")
    
    with open(mapping_json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    bone_map = config.get("bone_map", {})
    spine_map = config.get("spine_mapping", {})

    # Очистка сцены
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 1. Импорт целевого скелета Arma Reforger
    bpy.ops.import_scene.fbx(filepath=target_rig_fbx)
    target_armature = None
    for obj in bpy.context.selected_objects:
        if obj.type == 'ARMATURE':
            target_armature = obj
            break
    
    if not target_armature:
        print("[ERROR] Target armature not found in rig FBX!")
        return False

    target_armature.name = "Arma_Target"

    # 2. Импорт анимации источника UE
    bpy.ops.import_scene.fbx(filepath=src_fbx)
    source_armature = None
    for obj in bpy.context.selected_objects:
        if obj.type == 'ARMATURE' and obj != target_armature:
            source_armature = obj
            break

    if not source_armature:
        print("[ERROR] Source armature not found in animation FBX!")
        return False

    source_armature.name = "UE_Source"

    # 3. Настройка Bone Constraints (Маппинг костей)
    bpy.context.view_layer.objects.active = target_armature
    bpy.ops.object.mode_set(mode='POSE')

    # Накладываем Copy Transforms / Rotation
    for ue_bone, reforger_bone in bone_map.items():
        if reforger_bone in target_armature.pose.bones and ue_bone in source_armature.pose.bones:
            pbone = target_armature.pose.bones[reforger_bone]
            
            # Для Pelvis / Корня переносим трансформацию целиком со смещением
            if ue_bone.lower() == "pelvis":
                c = pbone.constraints.new('COPY_TRANSFORMS')
                c.target = source_armature
                c.subtarget = ue_bone
            else:
                c = pbone.constraints.new('COPY_ROTATION')
                c.target = source_armature
                c.subtarget = ue_bone
                c.target_space = 'WORLD'
                c.owner_space = 'WORLD'

    # Определение диапазона кадров анимации
    if source_armature.animation_data and source_armature.animation_data.action:
        act = source_armature.animation_data.action
        frame_start = int(act.frame_range[0])
        frame_end = int(act.frame_range[1])
    else:
        frame_start = int(bpy.context.scene.frame_start)
        frame_end = int(bpy.context.scene.frame_end)

    print(f"[RETARGET] Baking frames {frame_start} to {frame_end}...")

    # 4. Запекание анимации на скелет Arma (Bake Action)
    bpy.ops.nla.bake(
        frame_start=frame_start,
        frame_end=frame_end,
        only_selected=False,
        visual_keying=True,
        clear_constraints=True,
        bake_types={'POSE'}
    )

    # 5. Удаляем исходный скелет UE перед экспортом
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects.remove(source_armature, do_unlink=True)

    # 6. Выбираем только целевой скелет и экспортируем в FBX
    bpy.context.view_layer.objects.active = target_armature
    target_armature.select_set(True)

    os.makedirs(os.path.dirname(os.path.abspath(output_fbx)), exist_ok=True)

    bpy.ops.export_scene.fbx(
        filepath=output_fbx,
        use_selection=True,
        bake_anim=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True,
        add_leaf_bones=False,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        armature_nodetype='NULL'
    )

    print(f"[RETARGET] Success exported to: {output_fbx}")
    return True

if __name__ == "__main__":
    # Аргументы командной строки: -- src target out mapping
    args = sys.argv[sys.argv.index("--") + 1:]
    src_fbx = args[0]
    target_rig_fbx = args[1]
    output_fbx = args[2]
    mapping_json_path = args[3]

    retarget(src_fbx, target_rig_fbx, output_fbx, mapping_json_path)
