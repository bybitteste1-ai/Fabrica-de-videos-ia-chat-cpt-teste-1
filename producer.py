import argparse
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def load_config():
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

def load_job(path):
    job_path = Path(path)
    if not job_path.is_absolute():
        job_path = ROOT / job_path
    data = json.loads(job_path.read_text(encoding="utf-8"))
    required = ["id", "duration_seconds", "fps", "width", "height", "output_name"]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"Campos ausentes no job: {', '.join(missing)}")
    if not (1 <= int(data["duration_seconds"]) <= 120):
        raise ValueError("duration_seconds deve ficar entre 1 e 120 nesta versão.")
    if int(data["fps"]) not in (24, 25, 30):
        raise ValueError("Use fps 24, 25 ou 30.")
    if int(data["width"]) < 256 or int(data["height"]) < 256:
        raise ValueError("Resolução mínima: 256x256.")
    return data

def executable(name, configured):
    found = shutil.which(configured)
    if not found:
        raise RuntimeError(f"Não encontrei '{configured}'. Instale {name} e configure config.json.")
    return found

def run_job(job_file):
    cfg = load_config()
    job = load_job(job_file)
    blender = executable("Blender", cfg["blender_executable"])
    ffmpeg = executable("FFmpeg", cfg["ffmpeg_executable"])

    out_dir = ROOT / cfg["output_dir"]
    tmp_dir = ROOT / cfg["temp_dir"] / job["id"]
    log_dir = ROOT / cfg["log_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=log_dir / f'{job["id"]}.log',
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    frames_dir = tmp_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    blend_cmd = [
        blender, "-b", "-noaudio", "--python", str(ROOT / "blender" / "render_scene.py"),
        "--", "--job", str((ROOT / job_file).resolve() if not Path(job_file).is_absolute() else Path(job_file)),
        "--frames", str(frames_dir),
        "--engine", cfg.get("render_engine", "BLENDER_EEVEE"),
        "--device", cfg.get("device", "GPU")
    ]
    logging.info("Iniciando Blender: %s", " ".join(blend_cmd))
    subprocess.run(blend_cmd, check=True)

    output_path = out_dir / job["output_name"]
    ffmpeg_cmd = [
        ffmpeg, "-y", "-framerate", str(job["fps"]),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-r", str(job["fps"]),
        str(output_path)
    ]
    logging.info("Iniciando FFmpeg: %s", " ".join(ffmpeg_cmd))
    subprocess.run(ffmpeg_cmd, check=True)
    logging.info("Job concluído: %s", output_path)
    print(f"Vídeo criado: {output_path}")
    print("Confira o arquivo antes de publicar.")

def list_jobs():
    for p in sorted((ROOT / "jobs").glob("*.json")):
        print(p.relative_to(ROOT))

def main():
    parser = argparse.ArgumentParser(description="Orquestrador inicial da fábrica de vídeos")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="Lista os jobs disponíveis")
    val = sub.add_parser("validate", help="Valida um arquivo de job")
    val.add_argument("job")
    run = sub.add_parser("run", help="Renderiza e exporta um job")
    run.add_argument("job")
    args = parser.parse_args()

    try:
        if args.command == "list":
            list_jobs()
        elif args.command == "validate":
            job = load_job(args.job)
            print(f"OK: {job['id']} — {job['duration_seconds']}s, {job['width']}x{job['height']} a {job['fps']} fps")
        elif args.command == "run":
            run_job(args.job)
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
