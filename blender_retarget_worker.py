import bpy
import sys
import json
import os

def retarget(src_fbx, target_rig_fbx, output_fbx, mapping_json_path):
    print(f"[RETARGET] Starting: {src_fbx} -> {output_fbx}")

    with open(mapping_json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    bone_map = config.get("bone_map", {})

    # Очистка сцены
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 1. Загрузка целевого скелета Arma Reforger
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

    # 2. Загрузка анимации UE
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

    # Выравнивание позиции
    source_armature.location = target_armature.location

    # 3. Настройка костей:
    # В Arma Reforger оси костей (Local Axes / Roll) отличаются от UE.
    # В режиме WORLD с mix_mode='BEFORE_FULL' (или WORLD target & owner)
    # ориентация суставов копируется в реальном мировом пространстве без перекручивания локальных осей.
    bpy.context.view_layer.objects.active = target_armature
    bpy.ops.object.mode_set(mode='POSE')

    for ue_bone, ref_bone in bone_map.items():
        if ref_bone in target_armature.pose.bones and ue_bone in source_armature.pose.bones:
            pbone = target_armature.pose.bones[ref_bone]
            
            # Очистка старых констрейнтов
            for c in pbone.constraints:
                pbone.constraints.remove(c)
                
            if ue_bone.lower() == "pelvis":
                c_loc = pbone.constraints.new('COPY_LOCATION')
                c_loc.target = source_armature
                c_loc.subtarget = ue_bone
                
                c_rot = pbone.constraints.new('COPY_ROTATION')
                c_rot.target = source_armature
                c_rot.subtarget = ue_bone
                c_rot.target_space = 'WORLD'
                c_rot.owner_space = 'WORLD'
            else:
                c_rot = pbone.constraints.new('COPY_ROTATION')
                c_rot.target = source_armature
                c_rot.subtarget = ue_bone
                c_rot.target_space = 'WORLD'
                c_rot.owner_space = 'WORLD'

    # 4. Диапазон кадров
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
