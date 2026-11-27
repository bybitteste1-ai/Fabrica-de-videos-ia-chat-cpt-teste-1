import argparse
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

def args_after_dashes():
    argv = sys.argv
    return argv[argv.index("--") + 1:] if "--" in argv else []

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--job", required=True)
    p.add_argument("--frames", required=True)
    p.add_argument("--engine", default="BLENDER_EEVEE")
    p.add_argument("--device", default="GPU")
    return p.parse_args(args_after_dashes())

def material(name, color, metallic=0.0, roughness=0.55):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return m

def add_uv_sphere(name, location, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.shade_smooth()
    obj.data.materials.append(mat)
    return obj

def main():
    args = parse_args()
    job = json.loads(Path(args.job).read_text(encoding="utf-8"))
    frames_dir = Path(args.frames)
    frames_dir.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    scene = bpy.context.scene
    scene.render.engine = args.engine
    scene.render.resolution_x = int(job["width"])
    scene.render.resolution_y = int(job["height"])
    scene.render.resolution_percentage = 100
    scene.render.fps = int(job["fps"])
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = tuple(job.get("background", [0.025, 0.045, 0.09]))

    # Ambient background
    world = bpy.data.worlds.new("World") if not bpy.data.worlds else bpy.data.worlds[0]
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (*job.get("background", [0.025, 0.045, 0.09]), 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.7

    red = material("Character warm color", job.get("character_color", [0.95, 0.28, 0.12]), roughness=0.38)
    cream = material("Face", [1.0, 0.72, 0.48], roughness=0.65)
    dark = material("Eyes", [0.025, 0.02, 0.035], roughness=0.25)
    ground_mat = material("Ground", [0.025, 0.18, 0.15], roughness=0.9)
    gold = material("Accent", [1.0, 0.62, 0.08], metallic=0.1)

    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -1.15))
    ground = bpy.context.object
    ground.name = "Ground"
    ground.data.materials.append(ground_mat)

    body = add_uv_sphere("Character body", (0, 0, 0), (0.72, 0.48, 0.9), red)
    head = add_uv_sphere("Character head", (0, 0, 1.12), (0.62, 0.55, 0.62), cream)
    hair = add_uv_sphere("Stylized hair", (0, 0.05, 1.55), (0.66, 0.58, 0.34), red)
    eye1 = add_uv_sphere("Eye L", (-0.22, -0.49, 1.18), (0.07, 0.035, 0.10), dark)
    eye2 = add_uv_sphere("Eye R", (0.22, -0.49, 1.18), (0.07, 0.035, 0.10), dark)
    nose = add_uv_sphere("Nose", (0, -0.55, 1.03), (0.08, 0.06, 0.07), gold)

    # Simple stylized spikes
    for i in range(7):
        angle = (i / 7.0) * math.tau
        loc = (math.cos(angle) * 0.42, math.sin(angle) * 0.32, 1.72 + (0.08 if i % 2 else 0))
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.17, radius2=0.015, depth=0.48, location=loc)
        spike = bpy.context.object
        spike.name = f"Hair spike {i}"
        spike.data.materials.append(red)

    # Floating accent spheres
    for i, x in enumerate([-1.45, 1.45]):
        orb = add_uv_sphere(f"Floating accent {i}", (x, 0.1, 0.55), (0.16, 0.16, 0.16), gold)
        orb.keyframe_insert(data_path="location", frame=1)
        orb.location.z += 0.35
        orb.keyframe_insert(data_path="location", frame=int(job["duration_seconds"] * job["fps"]))

    # Character bob and turn
    for obj in [body, head, hair, eye1, eye2, nose]:
        original = obj.location.copy()
        obj.keyframe_insert(data_path="location", frame=1)
        obj.location.z += 0.13
        obj.keyframe_insert(data_path="location", frame=max(2, int(job["duration_seconds"] * job["fps"] / 2)))
        obj.location = original
        obj.keyframe_insert(data_path="location", frame=int(job["duration_seconds"] * job["fps"]))
    body.rotation_euler[2] = -0.12
    body.keyframe_insert(data_path="rotation_euler", frame=1)
    body.rotation_euler[2] = 0.12
    body.keyframe_insert(data_path="rotation_euler", frame=int(job["duration_seconds"] * job["fps"]))

    # Lighting
    bpy.ops.object.light_add(type="AREA", location=(4, -5, 7))
    key = bpy.context.object
    key.data.energy = 950
    key.data.shape = "DISK"
    key.data.size = 5
    bpy.ops.object.light_add(type="AREA", location=(-4, 1, 4))
    fill = bpy.context.object
    fill.data.energy = 500
    fill.data.size = 4

    # Camera: vertical composition
    bpy.ops.object.camera_add(location=(0, -8.5, 2.2))
    camera = bpy.context.object
    direction = Vector((0, 0, 0.45)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 52
    scene.camera = camera

    scene.frame_start = 1
    scene.frame_end = int(job["duration_seconds"] * job["fps"])
    scene.render.filepath = str(frames_dir / "frame_")
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.display.shading.light = "STUDIO"

    # Render on CPU by default for broad compatibility; GPU enablement is configured later.
    scene.render.threads_mode = "AUTO"
    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        scene.render.filepath = str(frames_dir / f"frame_{frame:05d}.png")
        bpy.ops.render.render(write_still=True)

if __name__ == "__main__":
    main()
