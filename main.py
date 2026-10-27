import datetime
import json
import os
import shutil
import subprocess
import sys
import traceback

import config
import images
import story_generator as sg
import video_creator
import voice
import youtube_uploader


def preflight():
    missing = [n for n, v in (("GEMINI_API_KEY", config.GEMINI_API_KEY), ("CF_ACCOUNT_ID", config.CF_ACCOUNT_ID),
                              ("CF_API_TOKEN", config.CF_API_TOKEN)) if not v]
    if not config.DRY_RUN:
        missing += [n for n in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
                    if not getattr(config, n)]
    if missing:
        raise RuntimeError("Missing secrets: " + ", ".join(missing))
    if not os.path.exists(config.PORTRAIT):
        raise RuntimeError(f"{config.PORTRAIT} is missing (needed for the closing card).")
    fonts = subprocess.run(["fc-list", ":lang=mr"], capture_output=True, text=True).stdout.strip()
    if not fonts:
        raise RuntimeError("No Devanagari (Hindi/Marathi) font installed (apt install fonts-noto-core).")
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            raise RuntimeError(f"{tool} not found.")


def log_upload(entry):
    try:
        with open(config.LOG_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = []
    data.append(entry)
    sg._atomic_write(config.LOG_FILE, data)


def main():
    print("=" * 60, "\nDAILY RAMAYANA SHORT (v2: scenes, voices, hook-first)\n" + "=" * 60)
    preflight()

    print("\n1/5 Choosing episode + writing script")
    episode, previous, following, number = sg.get_next_episode()
    print(f"Episode {number}: {episode['title']}")
    script = sg.generate_script(episode, previous, following)
    print("Title:", script["title"], "| attire:", script["attire"], "| location:", script["location"])

    outdir = os.path.join(config.OUT_DIR, f"ep{number:03d}")
    shutil.rmtree(outdir, ignore_errors=True)
    os.makedirs(outdir)
    with open(os.path.join(outdir, "script.json"), "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    for i, sc in enumerate(script["scenes"], 1):
        print(f"  {i}. [{sc['speaker']}] {sc['text']}")

    print("\n2/5 Drawing scenes + recording voices")
    base_seed = (number * 1009 + datetime.date.today().toordinal()) % 900000 + 1000
    scenes, failed = [], 0
    last_index = len(script["scenes"]) - 1
    for i, sc in enumerate(script["scenes"]):
        img, aud = f"scene{i:02d}.jpg", f"scene{i:02d}.wav"
        img_path = os.path.join(outdir, img)
        if i == last_index:
            images.save_portrait(img_path)                       # closing card = your Rama portrait
        elif not images.make_image(sc, script["attire"], script["location"], img_path, base_seed + i * 101,
                                                    episode.get("age", "adult")):
            failed += 1
            if failed > 3:
                raise RuntimeError("More than 3 pictures failed (Cloudflare quota or outage). Nothing uploaded.")
            if i > 0 and os.path.exists(os.path.join(outdir, f"scene{i - 1:02d}.jpg")):
                shutil.copy(os.path.join(outdir, f"scene{i - 1:02d}.jpg"), img_path)
            else:
                images.save_portrait(img_path)
        dur, profile = voice.synth(sc["text"], os.path.join(outdir, aud), sc["speaker"])
        scenes.append({"image": img, "audio": aud, "dur": dur, "text": sc["text"], "profile": profile,
                       "motion": sc["motion"], "sfx": sc["sfx"]})
        print(f"   scene {i + 1}/{len(script['scenes'])} ready ({dur:.1f}s, voice={profile})")

    total = sum(s["dur"] + config.SCENE_PAD for s in scenes)
    print(f"\nTotal narration: {total:.1f}s")
    if not 20 <= total <= 120:
        raise RuntimeError(f"Video length {total:.1f}s is outside the safe range (20-120s). Nothing uploaded.")

    print("\n3/5 Rendering video")
    final = video_creator.build(scenes, outdir, number)

    if config.DRY_RUN:
        print("\nDRY_RUN: video saved at", final, "- not uploaded, episode not advanced.")
        return 0

    print("\n4/5 Uploading to YouTube")
    vid = youtube_uploader.upload_video(final, script, number, os.path.join(outdir, "scene00.jpg"))

    if config.FIRST_COMMENT:
        youtube_uploader.post_first_comment(vid, script)

    print("\n5/5 Saving progress")
    if config.EPISODE_OVERRIDE:
        print("EPISODE_OVERRIDE used: saved state left unchanged.")
    else:
        sg.save_state(number + 1)
        log_upload({"episode": number, "title": script["title"], "video_id": vid,
                    "date": datetime.date.today().isoformat()})
        print(f"Next episode: {number + 1}")
    print("DONE.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print("\n" + "=" * 60, "\nPIPELINE FAILED:", exc, "\nEpisode state was NOT advanced; the same episode will retry.\n" + "=" * 60)
        traceback.print_exc()
        sys.exit(1)
