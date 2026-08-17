import asyncio
import os
import subprocess
import textwrap

import edge_tts
from PIL import Image, ImageDraw, ImageFont


OUTPUT_DIR = "output"
TEMP_DIR = "temp"

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920


def ensure_directories():

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)


def find_font():

    possible_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for font in possible_fonts:
        if os.path.exists(font):
            return font

    return None


def create_scene_image(title, episode_number, scene_number):

    ensure_directories()

    filename = os.path.join(
        TEMP_DIR,
        f"scene_{scene_number}.png"
    )

    image = Image.new(
        "RGB",
        (VIDEO_WIDTH, VIDEO_HEIGHT),
        (18, 12, 35)
    )

    draw = ImageDraw.Draw(image)

    font_path = find_font()

    if font_path:
        title_font = ImageFont.truetype(font_path, 70)
        episode_font = ImageFont.truetype(font_path, 42)
        small_font = ImageFont.truetype(font_path, 34)
    else:
        title_font = ImageFont.load_default()
        episode_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Decorative circles
    draw.ellipse(
        (100, 200, 980, 1080),
        outline=(220, 170, 80),
        width=8
    )

    draw.ellipse(
        (180, 280, 900, 1000),
        outline=(180, 130, 70),
        width=3
    )

    # Om symbol
    om_font = title_font

    draw.text(
        (540, 480),
        "ॐ",
        font=om_font,
        fill=(240, 190, 90),
        anchor="mm"
    )

    draw.text(
        (540, 1180),
        f"RAMAYANA",
        font=title_font,
        fill=(240, 210, 150),
        anchor="mm"
    )

    draw.text(
        (540, 1280),
        f"EPISODE {episode_number}",
        font=episode_font,
        fill=(220, 190, 140),
        anchor="mm"
    )

    wrapped = textwrap.fill(title, width=24)

    draw.text(
        (540, 1430),
        wrapped,
        font=small_font,
        fill=(255, 255, 255),
        anchor="mm",
        align="center"
    )

    draw.text(
        (540, 1760),
        "A journey of Dharma • Courage • Devotion",
        font=small_font,
        fill=(190, 180, 180),
        anchor="mm"
    )

    image.save(filename)

    return filename


async def generate_voice(text, output_file, subtitle_file):

    communicate = edge_tts.Communicate(
        text=text,
        voice="en-IN-NeerjaNeural",
        rate="-5%",
        volume="+0%"
    )

    await communicate.save(
        output_file,
        subtitle_file
    )


def generate_voice_sync(text):

    ensure_directories()

    audio_file = os.path.join(
        OUTPUT_DIR,
        "narration.mp3"
    )

    subtitle_file = os.path.join(
        OUTPUT_DIR,
        "narration.srt"
    )

    asyncio.run(
        generate_voice(
            text,
            audio_file,
            subtitle_file
        )
    )

    return audio_file, subtitle_file


def get_audio_duration(audio_file):

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        audio_file
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True
    )

    return float(result.stdout.strip())


def create_video(episode):

    ensure_directories()

    print("Generating narration...")

    audio_file, subtitle_file = generate_voice_sync(
        episode["narration"]
    )

    print("Voice created:", audio_file)

    duration = get_audio_duration(audio_file)

    # Ensure at least a short visual duration
    duration = max(duration, 10)

    print(f"Audio duration: {duration:.2f} seconds")

    scene_files = []

    # Create 4 visual scenes
    for i in range(1, 5):

        scene = create_scene_image(
            episode["title"],
            episode["episode"],
            i
        )

        scene_files.append(scene)

    output_file = os.path.join(
        OUTPUT_DIR,
        "final_short.mp4"
    )

    # Each scene gets an equal portion of the narration.
    scene_duration = duration / len(scene_files)

    concat_file = os.path.join(
        TEMP_DIR,
        "concat.txt"
    )

    with open(concat_file, "w", encoding="utf-8") as f:

        for scene in scene_files:

            f.write(
                f"file '{os.path.abspath(scene)}'\n"
            )

            f.write(
                f"duration {scene_duration}\n"
            )

        # Repeat final frame so ffmpeg respects the duration
        f.write(
            f"file '{os.path.abspath(scene_files[-1])}'\n"
        )

    command = [
        "ffmpeg",
        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        concat_file,

        "-i",
        audio_file,

        "-vf",
        (
            "scale=1080:1920,"
            "format=yuv420p"
        ),

        "-map",
        "0:v:0",

        "-map",
        "1:a:0",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-shortest",

        output_file
    ]

    print("Creating final video...")

    subprocess.run(
        command,
        check=True
    )

    print("Video created:", output_file)

    return output_file
