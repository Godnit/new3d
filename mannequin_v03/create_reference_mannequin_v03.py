import bpy
import math
import os
import sys
from mathutils import Vector


def parse_output_dir():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    out = "build"
    for i, arg in enumerate(argv):
        if arg == "--output-dir" and i + 1 < len(argv):
            out = argv[i + 1]
    out = os.path.abspath(out)
    os.makedirs(out, exist_ok=True)
    return out

OUT_DIR = parse_output_dir()
MODEL_NAME = "reference_mannequin_v03"


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def make_material(name, rgba, roughness=0.62):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = rgba
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = rgba
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = 0.0
    return mat


def apply_smooth(obj):
    if obj and obj.type == 'MESH':
        for p in obj.data.polygons:
            p.use_smooth = True


def add_uv_ellipsoid(name, location, scale, material, segments=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_smooth(obj)
    obj.data.materials.append(material)
    return obj


def add_tapered_segment(name, top_joint, bottom_joint, r_top, r_bottom, material, vertices=32):
    a = Vector(top_joint)
    b = Vector(bottom_joint)
    vec = b - a
    length = vec.length
    midpoint = (a + b) * 0.5
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r_bottom, radius2=r_top, depth=length, location=midpoint)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(a - b)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    apply_smooth(obj)
    obj.data.materials.append(material)
    cursor_old = bpy.context.scene.cursor.location.copy()
    bpy.context.scene.cursor.location = a
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.context.scene.cursor.location = cursor_old
    return obj


def add_ring_mesh(name, z_sections, material, vertices=40):
    verts = []
    faces = []
    for z, rx, ry in z_sections:
        for i in range(vertices):
            t = 2.0 * math.pi * i / vertices
            verts.append((rx * math.cos(t), ry * math.sin(t), z))
    n = len(z_sections)
    for s in range(n - 1):
        base = s * vertices
        nxt = (s + 1) * vertices
        for i in range(vertices):
            j = (i + 1) % vertices
            faces.append((base + i, base + j, nxt + j, nxt + i))
    faces.append(tuple(reversed(range(vertices))))
    top_start = (n - 1) * vertices
    faces.append(tuple(top_start + i for i in range(vertices)))
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    apply_smooth(obj)
    bevel = obj.modifiers.new(name='Soft_Edges', type='BEVEL')
    bevel.width = 0.018
    bevel.segments = 3
    return obj


def create_bone(arm_data, name, head, tail, parent=None, connected=False):
    bone = arm_data.edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.parent = parent
    bone.use_connect = connected
    return bone


def bone_parent(obj, armature, bone_name):
    obj.parent = armature
    obj.parent_type = 'BONE'
    obj.parent_bone = bone_name
    obj.matrix_parent_inverse = armature.matrix_world.inverted()


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


clear_scene()
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 900
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

body_mat = make_material('Warm_Salmon_Body', (0.88, 0.39, 0.34, 1.0), 0.68)
joint_mat = make_material('Muted_Rose_Joints', (0.62, 0.24, 0.22, 1.0), 0.72)
light_mat = make_material('Soft_Highlight', (0.95, 0.50, 0.44, 1.0), 0.65)

J = {
    'pelvis': (0.0, 0.0, 0.98),
    'waist': (0.0, 0.0, 1.28),
    'chest': (0.0, 0.0, 1.58),
    'neck': (0.0, 0.0, 1.88),
    'head_top': (0.0, 0.0, 2.28),
    'L_shoulder': (-0.38, 0.0, 1.75),
    'R_shoulder': (0.38, 0.0, 1.75),
    'L_elbow': (-0.43, -0.005, 1.34),
    'R_elbow': (0.43, -0.005, 1.34),
    'L_wrist': (-0.43, -0.015, 0.97),
    'R_wrist': (0.43, -0.015, 0.97),
    'L_hand': (-0.43, -0.025, 0.77),
    'R_hand': (0.43, -0.025, 0.77),
    'L_hip': (-0.18, 0.0, 0.92),
    'R_hip': (0.18, 0.0, 0.92),
    'L_knee': (-0.18, 0.0, 0.42),
    'R_knee': (0.18, 0.0, 0.42),
    'L_ankle': (-0.18, -0.01, 0.03),
    'R_ankle': (0.18, -0.01, 0.03),
}

objects_to_bones = []

torso = add_ring_mesh('Torso_Breastplate', [
    (1.34, 0.14, 0.10),
    (1.43, 0.22, 0.14),
    (1.62, 0.33, 0.17),
    (1.78, 0.42, 0.19),
    (1.84, 0.36, 0.17),
], body_mat)
objects_to_bones.append((torso, 'chest'))

collar = add_uv_ellipsoid('Shoulder_Collar_Plate', (0, 0, 1.79), (0.43, 0.18, 0.055), light_mat)
objects_to_bones.append((collar, 'chest'))

abdomen = add_uv_ellipsoid('Abdomen_Joint', (0, 0, 1.27), (0.18, 0.13, 0.20), joint_mat)
objects_to_bones.append((abdomen, 'spine'))

pelvis = add_uv_ellipsoid('Pelvis_Core', (0, 0, 1.01), (0.28, 0.17, 0.21), body_mat)
objects_to_bones.append((pelvis, 'pelvis'))

for side, sx in [('L', -1), ('R', 1)]:
    hip_guard = add_uv_ellipsoid(f'{side}_Hip_Guard', (0.20*sx, -0.005, 0.95), (0.16, 0.105, 0.075), light_mat)
    hip_guard.rotation_euler[1] = math.radians(-18*sx)
    objects_to_bones.append((hip_guard, 'pelvis'))

neck = add_uv_ellipsoid('Neck_Joint', (0, 0, 1.90), (0.07, 0.065, 0.095), joint_mat)
objects_to_bones.append((neck, 'neck'))
head = add_uv_ellipsoid('Featureless_Egg_Head', (0, 0, 2.10), (0.15, 0.125, 0.23), body_mat)
for v in head.data.vertices:
    if v.co.z < -0.25:
        factor = 0.78 + 0.22 * ((v.co.z + 1.0) / 0.75)
        v.co.x *= factor
        v.co.y *= factor
objects_to_bones.append((head, 'head'))

for side, sx in [('L', -1), ('R', 1)]:
    shoulder = add_uv_ellipsoid(f'{side}_Shoulder_Joint', J[f'{side}_shoulder'], (0.105, 0.105, 0.105), joint_mat)
    objects_to_bones.append((shoulder, f'{side}_upper_arm'))
    upper = add_tapered_segment(f'{side}_Upper_Arm', J[f'{side}_shoulder'], J[f'{side}_elbow'], 0.085, 0.060, body_mat)
    objects_to_bones.append((upper, f'{side}_upper_arm'))
    elbow = add_uv_ellipsoid(f'{side}_Elbow_Joint', J[f'{side}_elbow'], (0.067, 0.065, 0.062), joint_mat)
    objects_to_bones.append((elbow, f'{side}_forearm'))
    fore = add_tapered_segment(f'{side}_Forearm', J[f'{side}_elbow'], J[f'{side}_wrist'], 0.070, 0.045, body_mat)
    objects_to_bones.append((fore, f'{side}_forearm'))
    wrist = add_uv_ellipsoid(f'{side}_Wrist_Joint', J[f'{side}_wrist'], (0.045, 0.043, 0.044), joint_mat)
    objects_to_bones.append((wrist, f'{side}_hand'))
    hand = add_uv_ellipsoid(f'{side}_Palm', J[f'{side}_hand'], (0.066, 0.050, 0.115), body_mat)
    hand.rotation_euler[1] = math.radians(4*sx)
    objects_to_bones.append((hand, f'{side}_hand'))
    thumb = add_uv_ellipsoid(f'{side}_Thumb', (0.054*sx + J[f'{side}_hand'][0], -0.015, J[f'{side}_hand'][2] + 0.02), (0.030, 0.026, 0.070), body_mat, 20, 12)
    thumb.rotation_euler[1] = math.radians(-28*sx)
    objects_to_bones.append((thumb, f'{side}_hand'))

for side, sx in [('L', -1), ('R', 1)]:
    hip = add_uv_ellipsoid(f'{side}_Hip_Joint', J[f'{side}_hip'], (0.105, 0.10, 0.105), joint_mat)
    objects_to_bones.append((hip, f'{side}_thigh'))
    thigh = add_tapered_segment(f'{side}_Thigh', J[f'{side}_hip'], J[f'{side}_knee'], 0.125, 0.085, body_mat)
    objects_to_bones.append((thigh, f'{side}_thigh'))
    knee = add_uv_ellipsoid(f'{side}_Knee_Joint', J[f'{side}_knee'], (0.090, 0.085, 0.080), joint_mat)
    objects_to_bones.append((knee, f'{side}_shin'))
    shin = add_tapered_segment(f'{side}_Shin', J[f'{side}_knee'], J[f'{side}_ankle'], 0.085, 0.052, body_mat)
    objects_to_bones.append((shin, f'{side}_shin'))
    ankle = add_uv_ellipsoid(f'{side}_Ankle_Joint', J[f'{side}_ankle'], (0.052, 0.05, 0.045), joint_mat)
    objects_to_bones.append((ankle, f'{side}_foot'))
    foot = add_uv_ellipsoid(f'{side}_Foot', (0.18*sx, -0.075, -0.02), (0.082, 0.155, 0.060), body_mat)
    foot.rotation_euler[0] = math.radians(4)
    objects_to_bones.append((foot, f'{side}_foot'))

arm_data = bpy.data.armatures.new('Mannequin_Rig_Data')
arm = bpy.data.objects.new('Mannequin_Rig', arm_data)
bpy.context.collection.objects.link(arm)
arm.show_in_front = True
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
root = create_bone(arm_data, 'pelvis', (0,0,0.90), (0,0,1.08))
spine = create_bone(arm_data, 'spine', (0,0,1.08), (0,0,1.42), root, True)
chest_b = create_bone(arm_data, 'chest', (0,0,1.42), (0,0,1.80), spine, True)
neck_b = create_bone(arm_data, 'neck', (0,0,1.80), (0,0,1.96), chest_b, True)
head_b = create_bone(arm_data, 'head', (0,0,1.96), (0,0,2.25), neck_b, True)
for side, sx in [('L', -1), ('R', 1)]:
    clav = create_bone(arm_data, f'{side}_clavicle', (0,0,1.76), J[f'{side}_shoulder'], chest_b, False)
    ua = create_bone(arm_data, f'{side}_upper_arm', J[f'{side}_shoulder'], J[f'{side}_elbow'], clav, False)
    fa = create_bone(arm_data, f'{side}_forearm', J[f'{side}_elbow'], J[f'{side}_wrist'], ua, True)
    hand_b = create_bone(arm_data, f'{side}_hand', J[f'{side}_wrist'], J[f'{side}_hand'], fa, True)
    thigh_b = create_bone(arm_data, f'{side}_thigh', J[f'{side}_hip'], J[f'{side}_knee'], root, False)
    shin_b = create_bone(arm_data, f'{side}_shin', J[f'{side}_knee'], J[f'{side}_ankle'], thigh_b, True)
    foot_b = create_bone(arm_data, f'{side}_foot', J[f'{side}_ankle'], (0.18*sx,-0.16,-0.02), shin_b, False)
bpy.ops.object.mode_set(mode='OBJECT')
arm.select_set(False)

for obj, bone_name in objects_to_bones:
    bone_parent(obj, arm, bone_name)

arm['model_version'] = 'R03'
arm['reference'] = 'three.js stylized articulated mannequin supplied by user'
arm['rig_type'] = 'rigid bone-parented body pieces'

ground_mat = make_material('Warm_White_Background', (0.94, 0.94, 0.91, 1.0), 0.85)
bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,-0.085))
ground = bpy.context.object
ground.name = 'Preview_Ground'
ground.data.materials.append(ground_mat)

world = scene.world or bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.92, 0.92, 0.89, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.75

def add_area(name, loc, energy, size, color):
    data = bpy.data.lights.new(name, type='AREA')
    data.energy = energy
    data.shape = 'DISK'
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    look_at(obj, (0,0,1.1))
    return obj

add_area('Key_Light', (-3.2,-4.0,5.2), 850, 4.0, (1.0,0.78,0.70))
add_area('Fill_Light', (3.2,-2.0,3.0), 420, 3.5, (0.72,0.82,1.0))
add_area('Rim_Light', (0,3.0,4.0), 500, 2.8, (1.0,0.70,0.62))

cam_data = bpy.data.cameras.new('Preview_Camera')
cam = bpy.data.objects.new('Preview_Camera', cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (3.25, -6.2, 2.65)
cam_data.lens = 64
look_at(cam, (0, 0, 1.10))
scene.camera = cam

bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
for obj, _ in objects_to_bones:
    obj.select_set(True)
bpy.context.view_layer.objects.active = arm

blend_path = os.path.join(OUT_DIR, MODEL_NAME + '.blend')
glb_path = os.path.join(OUT_DIR, MODEL_NAME + '.glb')
preview_path = os.path.join(OUT_DIR, MODEL_NAME + '_preview.png')
readme_path = os.path.join(OUT_DIR, 'README.txt')

bpy.ops.wm.save_as_mainfile(filepath=blend_path)

bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format='GLB',
    use_selection=True,
    export_yup=True,
    export_animations=True,
    export_skins=True,
    export_materials='EXPORT',
)

bpy.ops.object.select_all(action='DESELECT')
scene.render.filepath = preview_path
bpy.ops.render.render(write_still=True)

with open(readme_path, 'w', encoding='utf-8') as f:
    f.write('Reference Mannequin R03\n')
    f.write('Generated in Blender from a procedural Python script.\n')
    f.write('Includes: .blend source, articulated .glb, and preview PNG.\n')
    f.write('Rig: rigid body pieces parented to named armature bones.\n')
    f.write('Designed to match the supplied three.js mannequin: slim proportions, egg head, tapered chest, visible joints, long limbs, small feet.\n')

print('BUILD_COMPLETE', OUT_DIR)
