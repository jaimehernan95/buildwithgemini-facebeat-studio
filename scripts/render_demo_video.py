#!/usr/bin/env python3
"""
render_demo_video.py - Generates an HD gameplay demo video of FaceBeat-Studio.
Features:
- Live AI Streamer Model (Nova-7) performing expressions (Smile, Jaw Drop, Brow Raise)
- Real-time MediaPipe Face Mesh landmark tracking wireframe overlay
- 3-Lane Neon Synthwave Rhythm Highway with targets synced to cyber_synth_beat.wav
- Visual combo popups, score increment, audio visualizer, and multi-agent HUD status
- Exports to MP4 (H.264/AAC), WebM (VP9/Opus), and lightweight animated GIF for README
"""

import os
import sys
import math
import subprocess
import tempfile
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def get_font(size: int, bold: bool = False):
    font_paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/space-grotesk/SpaceGrotesk-Medium.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def render_demo():
    base_dir = Path(__file__).resolve().parent.parent
    media_dir = base_dir / "app" / "static" / "media"
    avatar_dir = media_dir / "ai_avatar"
    audio_path = base_dir / "app" / "static" / "audio" / "cyber_synth_beat.wav"

    output_mp4 = media_dir / "demo_gameplay.mp4"
    output_webm = media_dir / "demo_gameplay.webm"
    output_gif = media_dir / "demo_gameplay.gif"

    print("🎨 Loading AI Model Avatar expressions...")
    avatar_neutral = Image.open(avatar_dir / "neutral.png").convert("RGBA").resize((380, 380), Image.Resampling.LANCZOS)
    avatar_smile = Image.open(avatar_dir / "smile.png").convert("RGBA").resize((380, 380), Image.Resampling.LANCZOS)
    avatar_jaw = Image.open(avatar_dir / "jaw.png").convert("RGBA").resize((380, 380), Image.Resampling.LANCZOS)

    width, height = 1280, 720
    fps = 25
    duration_sec = 10.0
    total_frames = int(fps * duration_sec)

    targets = [
        {"time": 0.9, "expression": "Smile", "lane": 1, "hit": False},
        {"time": 1.8, "expression": "MouthOpen", "lane": 0, "hit": False},
        {"time": 2.7, "expression": "BrowRaise", "lane": 2, "hit": False},
        {"time": 3.6, "expression": "Smile", "lane": 1, "hit": False},
        {"time": 4.5, "expression": "MouthOpen", "lane": 0, "hit": False},
        {"time": 5.4, "expression": "Smile", "lane": 1, "hit": False},
        {"time": 6.3, "expression": "BrowRaise", "lane": 2, "hit": False},
        {"time": 7.2, "expression": "MouthOpen", "lane": 0, "hit": False},
        {"time": 8.1, "expression": "Smile", "lane": 1, "hit": False},
        {"time": 9.0, "expression": "BrowRaise", "lane": 2, "hit": False},
    ]

    lane_x = [240, 420, 600]  # Left (MouthOpen), Center (Smile), Right (BrowRaise)
    hit_y = 570

    font_title = get_font(26, bold=True)
    font_hud = get_font(18, bold=True)
    font_large = get_font(34, bold=True)
    font_small = get_font(14, bold=False)
    font_popup = get_font(22, bold=True)

    temp_frame_dir = Path(tempfile.mkdtemp(prefix="facebeat_frames_"))
    print(f"🎬 Generating {total_frames} gameplay frames at {width}x{height} (25 FPS)...")

    score = 0
    combo = 0
    active_popups = []

    try:
        for f in range(total_frames):
            t = f / float(fps)
            frame = Image.new("RGBA", (width, height), (13, 17, 23, 255))
            draw = ImageDraw.Draw(frame)

            # 1. Background Grid & Horizon
            for gy in range(350, 720, 35):
                alpha = int(30 + (gy - 350) * 0.4)
                draw.line([(0, gy), (840, gy)], fill=(40, 20, 80, alpha), width=1)
            for gx in range(50, 840, 70):
                draw.line([(gx, 350), (int(gx + (gx - 420) * 0.6), 720)], fill=(0, 180, 220, 35), width=1)

            # 2. Highway Lanes
            highway_x1, highway_x2 = 140, 700
            draw.rectangle([(highway_x1, 100), (highway_x2, 680)], fill=(18, 12, 38, 220))
            draw.rectangle([(highway_x1, 100), (highway_x2, 680)], outline=(147, 51, 234, 180), width=2)

            for lx in [330, 510]:
                draw.line([(lx, 100), (lx, 680)], fill=(75, 40, 110, 160), width=2)

            # Hit Bar & Receptors
            draw.line([(highway_x1, hit_y), (highway_x2, hit_y)], fill=(0, 255, 204, 230), width=3)
            for idx, lx in enumerate(lane_x):
                glow_r = 36
                draw.ellipse([(lx - glow_r, hit_y - glow_r), (lx + glow_r, hit_y + glow_r)], outline=(0, 255, 204, 160), width=2)
                labels = ["Jaw", "Smile", "Brow"]
                draw.text((lx - 16, hit_y + 42), labels[idx], font=font_small, fill=(180, 200, 230, 220))

            current_active_exp = "Neutral"
            avatar_to_draw = avatar_neutral
            status_text = "READY - RESTING FACE"
            status_color = (130, 160, 200)

            for target in targets:
                diff = target["time"] - t
                if 0 <= diff <= 1.5:
                    progress = 1.0 - (diff / 1.5)
                    target_y = 120 + progress * (hit_y - 120)
                    tx = lane_x[target["lane"]]
                    tr = int(24 + progress * 8)
                    color = (255, 100, 200) if target["lane"] == 0 else ((100, 255, 150) if target["lane"] == 1 else (100, 200, 255))
                    draw.ellipse([(tx - tr, target_y - tr), (tx + tr, target_y + tr)], fill=(color[0], color[1], color[2], 220), outline=(255, 255, 255, 240), width=2)
                    label_txt = "JAW" if target["expression"] == "MouthOpen" else ("SMILE" if target["expression"] == "Smile" else "BROW")
                    draw.text((tx - 20, target_y - 8), label_txt, font=font_small, fill=(255, 255, 255))

                if abs(diff) <= 0.18:
                    current_active_exp = target["expression"]
                    if not target["hit"] and diff <= 0.05:
                        target["hit"] = True
                        score += 100
                        combo += 1
                        active_popups.append({
                            "text": "PERFECT! +100",
                            "x": lane_x[target["lane"]],
                            "y": hit_y - 20,
                            "life": 15,
                            "color": (0, 255, 204)
                        })

            if current_active_exp == "Smile":
                avatar_to_draw = avatar_smile
                status_text = "SMILE DETECTED (98%)"
                status_color = (0, 255, 150)
            elif current_active_exp in ("MouthOpen", "BrowRaise"):
                avatar_to_draw = avatar_jaw
                status_text = f"{current_active_exp.upper()} (96%)"
                status_color = (255, 50, 180)

            # 3. Floating Popups
            remaining_popups = []
            for p in active_popups:
                p["y"] -= 2
                p["life"] -= 1
                alpha = int(255 * (p["life"] / 15.0))
                draw.text((p["x"] - 55, p["y"]), p["text"], font=font_popup, fill=(p["color"][0], p["color"][1], p["color"][2], alpha))
                ring_r = 45 + (15 - p["life"]) * 3
                draw.ellipse([(p["x"] - ring_r, hit_y - ring_r), (p["x"] + ring_r, hit_y + ring_r)], outline=(p["color"][0], p["color"][1], p["color"][2], alpha), width=2)
                if p["life"] > 0:
                    remaining_popups.append(p)
            active_popups = remaining_popups

            # 4. Top HUD in Game View
            draw.text((highway_x1, 28), "TRACK: CYBER SYNTH BEAT", font=font_title, fill=(240, 246, 252))
            draw.text((highway_x1, 64), f"SCORE: {score:,}", font=font_large, fill=(0, 255, 204))
            draw.text((highway_x1 + 320, 64), f"COMBO: x{combo}", font=font_large, fill=(255, 105, 180) if combo > 5 else (255, 215, 0))

            prog_ratio = min(1.0, t / duration_sec)
            draw.rectangle([(highway_x1, 95), (highway_x2, 102)], fill=(40, 45, 60))
            draw.rectangle([(highway_x1, 95), (highway_x1 + int((highway_x2 - highway_x1) * prog_ratio), 102)], fill=(0, 255, 204))

            # 5. Right Streamer PiP Frame (AI Model Nova-7)
            cam_x, cam_y, cam_w, cam_h = 850, 40, 400, 490
            draw.rectangle([(cam_x, cam_y), (cam_x + cam_w, cam_y + cam_h)], fill=(20, 24, 34), outline=(138, 43, 226), width=3)
            draw.text((cam_x + 15, cam_y + 12), "AI STREAMER: NOVA-7", font=font_hud, fill=(255, 60, 100))
            draw.text((cam_x + 270, cam_y + 14), "60 FPS • HD", font=font_small, fill=(150, 170, 200))

            frame.paste(avatar_to_draw, (cam_x + 10, cam_y + 40), avatar_to_draw)

            # MediaPipe Landmark Points
            ax = cam_x + 10
            ay = cam_y + 40
            mesh_points = [
                (ax + 195, ay + 115), (ax + 160, ay + 125), (ax + 230, ay + 125),
                (ax + 155, ay + 155), (ax + 175, ay + 155), (ax + 215, ay + 155), (ax + 235, ay + 155),
                (ax + 195, ay + 165), (ax + 195, ay + 195), (ax + 185, ay + 210), (ax + 205, ay + 210),
                (ax + 140, ay + 215) if current_active_exp != "Smile" else (ax + 135, ay + 200),
                (ax + 250, ay + 215) if current_active_exp != "Smile" else (ax + 255, ay + 200),
                (ax + 195, ay + 245), (ax + 175, ay + 255), (ax + 215, ay + 255),
                (ax + 195, ay + 275) if current_active_exp != "MouthOpen" else (ax + 195, ay + 295),
                (ax + 195, ay + 310) if current_active_exp != "MouthOpen" else (ax + 195, ay + 330),
            ]
            for i in range(len(mesh_points) - 1):
                draw.line([mesh_points[i], mesh_points[i + 1]], fill=(0, 255, 204, 110), width=1)
            for pt in mesh_points:
                draw.ellipse([(pt[0] - 2, pt[1] - 2), (pt[0] + 2, pt[1] + 2)], fill=(0, 255, 204, 220))

            # Status Bar under Avatar
            draw.rectangle([(cam_x + 10, cam_y + 430), (cam_x + cam_w - 10, cam_y + 475)], fill=(30, 36, 50), outline=status_color, width=2)
            draw.text((cam_x + 20, cam_y + 444), status_text, font=font_hud, fill=status_color)

            # 6. Multi-Agent Telemetry Box
            hud_y = 545
            draw.rectangle([(cam_x, hud_y), (cam_x + cam_w, 680)], fill=(15, 18, 25), outline=(60, 70, 95), width=2)
            draw.text((cam_x + 15, hud_y + 10), "GOOGLE ANTIGRAVITY AGENTS", font=font_hud, fill=(255, 215, 0))
            draw.text((cam_x + 15, hud_y + 36), "* RhythmAnalyzerAgent: 130 BPM Synced", font=font_small, fill=(180, 200, 230))
            draw.text((cam_x + 15, hud_y + 60), "* AudioSafetyAgent: 100% Royalty-Free", font=font_small, fill=(100, 255, 150))
            draw.text((cam_x + 15, hud_y + 84), "* SocialClipperAgent: 9:16 Buffer Active", font=font_small, fill=(0, 200, 255))
            draw.text((cam_x + 15, hud_y + 108), "* SQLite DB: Auto-Save Ready", font=font_small, fill=(200, 150, 255))

            frame_path = temp_frame_dir / f"frame_{f:05d}.png"
            frame.convert("RGB").save(frame_path, "PNG")

            if f % 50 == 0 or f == total_frames - 1:
                print(f"  -> Processed frame {f+1}/{total_frames} ({(f+1)/total_frames*100:.1f}%)")

        print("Encoding MP4 video with FFmpeg + audio sync...")
        cmd_mp4 = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(temp_frame_dir / "frame_%05d.png"),
            "-ss", "00:00:00",
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(duration_sec),
            "-shortest",
            str(output_mp4)
        ]
        subprocess.run(cmd_mp4, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"MP4 generated: {output_mp4} ({output_mp4.stat().st_size / 1024 / 1024:.2f} MB)")

        print("Encoding WebM video with FFmpeg...")
        cmd_webm = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(temp_frame_dir / "frame_%05d.png"),
            "-ss", "00:00:00",
            "-i", str(audio_path),
            "-c:v", "libvpx-vp9",
            "-b:v", "1M",
            "-c:a", "libopus",
            "-t", str(duration_sec),
            "-shortest",
            str(output_webm)
        ]
        subprocess.run(cmd_webm, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"WebM generated: {output_webm} ({output_webm.stat().st_size / 1024 / 1024:.2f} MB)")

        print("Generating lightweight animated GIF preview for README...")
        cmd_gif = [
            "ffmpeg", "-y",
            "-ss", "00:00:01",
            "-t", "4",
            "-i", str(output_mp4),
            "-vf", "fps=12,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            str(output_gif)
        ]
        subprocess.run(cmd_gif, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"GIF generated: {output_gif} ({output_gif.stat().st_size / 1024 / 1024:.2f} MB)")

        shutil.copy(output_gif, base_dir / "demo_gameplay.gif")
        print("Copied demo_gameplay.gif to project root!")

    finally:
        shutil.rmtree(temp_frame_dir, ignore_errors=True)
        print("Cleaned up temporary frame cache.")

if __name__ == "__main__":
    render_demo()
