import bpy
import sys
import json
import os
import mathutils

def retarget(src_fbx, target_rig_fbx, output_fbx, mapping_json_path):
    print(f"[RETARGET] Starting: {src_fbx} -> {output_fbx}")

    with open(mapping_json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    bone_map = config.get("bone_map", {})

    # 1. Очистка всей сцены
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 2. Импорт целевого скелета Arma Reforger
    bpy.ops.import_scene.fbx(filepath=target_rig_fbx)
    
    target_armature = None
    target_meshes = []
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            target_armature = obj
        elif obj.type == 'MESH':
            target_meshes.append(obj)
            
    if not target_armature:
        print("[ERROR] Target armature not found!")
        return False
        
    target_armature.name = "Arma_Target"

    # 3. Импорт анимации источника UE
    bpy.ops.import_scene.fbx(filepath=src_fbx)
    
    source_armature = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE' and obj != target_armature:
            source_armature = obj
            break
            
    if not source_armature:
        print("[ERROR] Source armature not found!")
        return False
        
    source_armature.name = "UE_Source"

    # Сохраняем исходные матрицы покоя (Rest Pose) для вычисления дельты
    rest_diff_rotations = {}
    
    for ue_bone, ref_bone in bone_map.items():
        if ref_bone in target_armature.data.bones and ue_bone in source_armature.data.bones:
            t_rest_q = target_armature.data.bones[ref_bone].matrix_local.to_quaternion()
            s_rest_q = source_armature.data.bones[ue_bone].matrix_local.to_quaternion()
            
            # Дельта разницы между базовыми позами в Edit Mode
            delta = t_rest_q @ s_rest_q.inverted()
            rest_diff_rotations[ref_bone] = (ue_bone, delta)

    # 4. Создаем Action для анимации на целевом скелете
    if not target_armature.animation_data:
        target_armature.animation_data_create()

    target_action = bpy.data.actions.new(name=f"Retarget_{os.path.basename(src_fbx)}")
    target_armature.animation_data.action = target_action

    # Диапазон кадров
    if source_armature.animation_data and source_armature.animation_data.action:
        act = source_armature.animation_data.action
        frame_start = int(act.frame_range[0])
        frame_end = int(act.frame_range[1])
    else:
        frame_start = int(bpy.context.scene.frame_start)
        frame_end = int(bpy.context.scene.frame_end)

    print(f"[RETARGET] Transferring keyframes with rest offset from {frame_start} to {frame_end}...")

    # 5. Кадровый перенос с компенсацией Rest Pose
    bpy.context.view_layer.objects.active = target_armature
    bpy.ops.object.mode_set(mode='POSE')

    for f in range(frame_start, frame_end + 1):
        bpy.context.scene.frame_set(f)
        
        for ref_bone, (ue_bone, delta) in rest_diff_rotations.items():
            s_pbone = source_armature.pose.bones[ue_bone]
            t_pbone = target_armature.pose.bones[ref_bone]
            
            # Текущее локальное вращение из анимации
            src_anim_rot = s_pbone.matrix_basis.to_quaternion()
            
            # Применяем скорректированное вращение
            final_rot = delta @ src_anim_rot @ delta.inverted()
            
            t_pbone.rotation_mode = 'QUATERNION'
            t_pbone.rotation_quaternion = final_rot
            t_pbone.keyframe_insert(data_path="rotation_quaternion", frame=f)
            
            # Для таза также переносим смещение
            if ue_bone.lower() == "pelvis":
                t_pbone.location = s_pbone.location
                t_pbone.keyframe_insert(data_path="location", frame=f)

    # 6. Удаляем скелет источника
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects.remove(source_armature, do_unlink=True)

    # 7. Экспорт
    bpy.ops.object.select_all(action='DESELECT')
    target_armature.select_set(True)
    for m in target_meshes:
        m.select_set(True)
        
    bpy.context.view_layer.objects.active = target_armature
    
    os.makedirs(os.path.dirname(os.path.abspath(output_fbx)), exist_ok=True)

    bpy.ops.export_scene.fbx(
        filepath=output_fbx,
        use_selection=True,
        bake_anim=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True,
        add_leaf_bones=False,
        armature_nodetype='NULL'
    )

    print(f"[RETARGET] Successfully written: {output_fbx}")
    return True

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:]
    src_fbx = args[0]
    target_rig_fbx = args[1]
    output_fbx = args[2]
    mapping_json_path = args[3]

    retarget(src_fbx, target_rig_fbx, output_fbx, mapping_json_path)
