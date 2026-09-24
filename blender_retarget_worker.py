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

    # Очистка сцены
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 1. Импорт целевого скелета Arma Reforger
    bpy.ops.import_scene.fbx(
        filepath=target_rig_fbx,
        automatic_bone_orientation=False,
        force_connect_children=False
    )
    
    target_armature = None
    target_meshes = []
    
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            target_armature = obj
        elif obj.type == 'MESH':
            target_meshes.append(obj)
    
    if not target_armature:
        print("[ERROR] Target armature not found in rig FBX!")
        return False

    target_armature.name = "Arma_Target"
    
    # Применяем масштабы целевого скелета и мешей
    bpy.context.view_layer.objects.active = target_armature
    bpy.ops.object.select_all(action='DESELECT')
    target_armature.select_set(True)
    for m in target_meshes:
        m.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # 2. Импорт анимации источника UE
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.fbx(
        filepath=src_fbx,
        automatic_bone_orientation=False,
        force_connect_children=False
    )
    
    source_armature = None
    for obj in bpy.context.selected_objects:
        if obj.type == 'ARMATURE' and obj != target_armature:
            source_armature = obj
            break

    if not source_armature:
        print("[ERROR] Source armature not found in animation FBX!")
        return False

    source_armature.name = "UE_Source"

    # Масштабирование UE скелета к Reforger (если в UE масштаб x100 или x0.01)
    # Выравниваем масштаб по Pelvis Z
    target_pelvis = target_armature.pose.bones.get("Spine1") or target_armature.pose.bones.get("Pelvis")
    source_pelvis = source_armature.pose.bones.get("Pelvis") or source_armature.pose.bones.get("pelvis")
    
    if target_pelvis and source_pelvis:
        t_z = (target_armature.matrix_world @ target_pelvis.head).z
        s_z = (source_armature.matrix_world @ source_pelvis.head).z
        if s_z > 0.001 and t_z > 0.001:
            scale_ratio = t_z / s_z
            if abs(scale_ratio - 1.0) > 0.05:
                print(f"[SCALE] Adjusting UE skeleton scale ratio: {scale_ratio}")
                source_armature.scale *= scale_ratio
                bpy.context.view_layer.objects.active = source_armature
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # 3. Настройка Bone Constraints (Маппинг костей в LOCAL с инверсией разницы поз)
    bpy.context.view_layer.objects.active = target_armature
    bpy.ops.object.mode_set(mode='POSE')

    for ue_bone, reforger_bone in bone_map.items():
        if reforger_bone in target_armature.pose.bones and ue_bone in source_armature.pose.bones:
            pbone = target_armature.pose.bones[reforger_bone]
            
            # Очищаем старые констрейнты
            for c in pbone.constraints:
                pbone.constraints.remove(c)

            if ue_bone.lower() == "pelvis":
                # Перенос смещения и вращения таза
                c = pbone.constraints.new('COPY_TRANSFORMS')
                c.target = source_armature
                c.subtarget = ue_bone
                c.target_space = 'WORLD'
                c.owner_space = 'WORLD'
            else:
                # Вращение остальных костей
                c = pbone.constraints.new('COPY_ROTATION')
                c.target = source_armature
                c.subtarget = ue_bone
                c.target_space = 'LOCAL_WITH_PARENT'
                c.owner_space = 'LOCAL_WITH_PARENT'

    # 4. Определение диапазона кадров
    if source_armature.animation_data and source_armature.animation_data.action:
        act = source_armature.animation_data.action
        frame_start = int(act.frame_range[0])
        frame_end = int(act.frame_range[1])
    else:
        frame_start = int(bpy.context.scene.frame_start)
        frame_end = int(bpy.context.scene.frame_end)

    print(f"[RETARGET] Baking frames {frame_start} to {frame_end}...")

    # 5. Запекание (Bake Action)
    bpy.ops.nla.bake(
        frame_start=frame_start,
        frame_end=frame_end,
        only_selected=False,
        visual_keying=True,
        clear_constraints=True,
        bake_types={'POSE'}
    )

    # 6. Удаляем временный скелет UE
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects.remove(source_armature, do_unlink=True)

    # 7. Экспорт ТОЛЬКО скелета (или скелет + меш без искажения масштаба)
    bpy.ops.object.select_all(action='DESELECT')
    target_armature.select_set(True)
    for m in target_meshes:
        m.select_set(True)
    
    bpy.context.view_layer.objects.active = target_armature

    os.makedirs(os.path.dirname(os.path.abspath(output_fbx)), exist_ok=True)

    bpy.ops.export_scene.fbx(
        filepath=output_fbx,
        use_selection=True,
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Z',
        axis_up='Y',
        apply_unit_scale=True,
        bake_anim=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True,
        add_leaf_bones=False,
        armature_nodetype='NULL'
    )

    print(f"[RETARGET] Success exported to: {output_fbx}")
    return True

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:]
    src_fbx = args[0]
    target_rig_fbx = args[1]
    output_fbx = args[2]
    mapping_json_path = args[3]

    retarget(src_fbx, target_rig_fbx, output_fbx, mapping_json_path)
