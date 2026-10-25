"""Scenes (picture + voice + sfx + camera move) -> one 1080x1920 Short with captions, progress bar and music."""
import os
import shutil

import config
import effects
import voice


def _tracks():
    d = config.MUSIC_DIR
    if not os.path.isdir(d):
        return []
    return [os.path.abspath(os.path.join(d, f)) for f in sorted(os.listdir(d))
            if f.lower().endswith((".mp3", ".wav", ".m4a"))]


def build(scenes, outdir, episode_number):
    """scenes: dicts with image, audio (file names inside outdir), dur, text, profile, motion, sfx."""
    W, H, FPS, PAD = config.WIDTH, config.HEIGHT, config.FPS, config.SCENE_PAD
    clips = []
    for i, sc in enumerate(scenes):
        total = sc["dur"] + PAD
        frames = max(int(round(total * FPS)), 2)
        z, x, y = effects.motion(sc.get("motion", "zoom_in"), frames)
        # picture is scaled up 1.5x before zoompan so the slow zoom stays smooth (no pixel jitter)
        vf = (f"[0:v]scale={int(W * 1.5)}:{int(H * 1.5)}:flags=lanczos,"
              f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS},format=yuv420p[v]")
        cmd = ["ffmpeg", "-y", "-i", sc["image"], "-i", sc["audio"]]
        sfx = sc.get("sfx", "none")
        if sfx in effects.SFX:
            cmd += ["-i", effects.make_sfx(sfx, outdir)]
            af = (f"[1:a]apad=pad_dur={PAD}[a0];[2:a]volume={effects.SFX_GAIN[sfx]}[s];"
                  f"[a0][s]amix=inputs=2:duration=first:normalize=0[a]")
        else:
            af = f"[1:a]apad=pad_dur={PAD}[a]"
        clip = f"clip{i:02d}.mp4"
        cmd += ["-filter_complex", f"{vf};{af}", "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-r", str(FPS),
                "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k", clip]
        effects.run(cmd, outdir)
        clips.append(clip)
        print(f"   clip {i + 1}/{len(scenes)} rendered ({sc['motion']}, sfx={sfx})")

    with open(os.path.join(outdir, "list.txt"), "w") as f:
        f.write("".join(f"file '{c}'\n" for c in clips))
    effects.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "joined.mp4"], outdir)

    total = sum(s["dur"] + PAD for s in scenes)
    with open(os.path.join(outdir, "captions.ass"), "w", encoding="utf-8") as f:
        f.write(effects.build_ass(scenes, episode_number))

    tracks = _tracks()
    if tracks:
        music_in = ["-stream_loop", "-1", "-i", tracks[0]]
        mfx = f"[1:a]volume={config.MUSIC_VOLUME}[m]"
    else:
        music_in = ["-i", effects.make_drone(outdir, total + 1)]
        mfx = f"[1:a]volume={config.MUSIC_VOLUME * 1.6:.3f}[m]"

    bar_y = config.FOREGROUND_TOP + config.FOREGROUND_H            # thin saffron progress bar under the picture
    fc = (f"[0:v]ass=captions.ass[v1];"
          f"color=c=0xFF9933:s={W}x10:r={FPS}:d={total + 1:.2f}[bar];"
          f"[v1][bar]overlay=x='-w+w*t/{total:.3f}':y={bar_y}[v];"
          f"[0:a]aresample=44100[a0];{mfx};"
          f"[a0][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
          f"loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    final = os.path.join(outdir, "final_short.mp4")
    effects.run(["ffmpeg", "-y", "-i", "joined.mp4", *music_in, "-filter_complex", fc,
                 "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                 "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS),
                 "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-t", f"{total:.3f}",
                 "-movflags", "+faststart", "final_short.mp4"], outdir)

    for c in clips:
        os.remove(os.path.join(outdir, c))

    size = os.path.getsize(final)
    real = voice.duration(final)
    if size < 100_000:
        raise RuntimeError(f"Final video is suspiciously small ({size} bytes).")
    if abs(real - total) > 1.0:
        raise RuntimeError(f"Final video length {real:.1f}s does not match narration {total:.1f}s.")
    print(f"   final video: {real:.1f}s, {size / 1024 / 1024:.1f} MB")
    return final
