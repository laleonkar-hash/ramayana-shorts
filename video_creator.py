import asyncio
import os
import subprocess
import textwrap

import edge_tts

from PIL import Image, ImageDraw, ImageFont


OUTPUT_DIR = "output"
TEMP_DIR = "temp"

WIDTH = 1080
HEIGHT = 1920


def ensure_directories():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    os.makedirs(
        TEMP_DIR,
        exist_ok=True
    )


def get_font(size):

    fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]

    for path in fonts:

        if os.path.exists(path):

            return ImageFont.truetype(
                path,
                size
            )

    return ImageFont.load_default()


def create_scene(
    title,
    story,
    episode,
    scene_number
):

    ensure_directories()

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        (18, 12, 35)
    )

    draw = ImageDraw.Draw(
        image
    )

    title_font = get_font(70)
    episode_font = get_font(44)
    story_font = get_font(40)
    small_font = get_font(30)

    # Decorative frame
    draw.rounded_rectangle(
        (55, 55, WIDTH - 55, HEIGHT - 55),
        radius=35,
        outline=(220, 180, 100),
        width=5
    )

    # Decorative circles
    draw.ellipse(
        (120, 180, 960, 1020),
        outline=(220, 180, 100),
        width=6
    )

    draw.ellipse(
        (190, 250, 890, 950),
        outline=(150, 110, 70),
        width=3
    )

    # Om
    draw.text(
        (WIDTH // 2, 510),
        "ॐ",
        font=title_font,
        fill=(245, 200, 110),
        anchor="mm"
    )

    draw.text(
        (WIDTH // 2, 1110),
        "RAMAYANA",
        font=title_font,
        fill=(245, 220, 170),
        anchor="mm"
    )

    draw.text(
        (WIDTH // 2, 1200),
        f"EPISODE {episode}",
        font=episode_font,
        fill=(220, 190, 140),
        anchor="mm"
    )

    wrapped_title = textwrap.fill(
        title,
        width=22
    )

    draw.text(
        (WIDTH // 2, 1370),
        wrapped_title,
        font=story_font,
        fill=(255, 255, 255),
        anchor="mm",
        align="center"
    )

    draw.text(
        (WIDTH // 2, 1740),
        f"Scene {scene_number}",
        font=small_font,
        fill=(190, 185, 185),
        anchor="mm"
    )

    filename = os.path.join(
        TEMP_DIR,
        f"scene_{scene_number}.png"
    )

    image.save(
        filename
    )

    return filename


async def generate_voice(
    text,
    audio_file,
    subtitle_file
):

    voice = edge_tts.Communicate(
        text=text,
        voice="en-IN-NeerjaNeural",
        rate="-2%",
        volume="+0%"
    )

    await voice.save(
        audio_file,
        subtitle_file
    )


def generate_audio(text):

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

    return (
        audio_file,
        subtitle_file
    )


def get_duration(audio_file):

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

    return float(
        result.stdout.strip()
    )


def create_video(episode):

    ensure_directories()

    print()
    print("Generating narration...")

    audio_file, subtitle_file = generate_audio(
        episode["story"]
    )

    duration = get_duration(
        audio_file
    )

    print(
        f"Original narration duration: "
        f"{duration:.2f} seconds"
    )

    # Keep the target around 30 seconds.
    # Small speed adjustment is used instead of cutting words.
    target_duration = 30.0

    speed = duration / target_duration

    # Keep speed adjustment within reasonable limits.
    speed = max(
        0.85,
        min(1.15, speed)
    )

    adjusted_audio = os.path.join(
        OUTPUT_DIR,
        "narration_30s.mp3"
    )

    audio_command = [
        "ffmpeg",
        "-y",
        "-i",
        audio_file,
        "-filter:a",
        f"atempo={speed:.4f}",
        "-ar",
        "44100",
        adjusted_audio
    ]

    subprocess.run(
        audio_command,
        check=True
    )

    final_duration = get_duration(
        adjusted_audio
    )

    print(
        f"Adjusted narration duration: "
        f"{final_duration:.2f} seconds"
    )

    scene_files = []

    for i in range(1, 5):

        scene_files.append(
            create_scene(
                episode["title"],
                episode["story"],
                episode["episode"],
                i
            )
        )

    concat_file = os.path.join(
        TEMP_DIR,
        "scenes.txt"
    )

    scene_duration = (
        final_duration / len(scene_files)
    )

    with open(
        concat_file,
        "w",
        encoding="utf-8"
    ) as f:

        for scene in scene_files:

            f.write(
                f"file '{os.path.abspath(scene)}'\n"
            )

            f.write(
                f"duration {scene_duration}\n"
            )

        f.write(
            f"file '{os.path.abspath(scene_files[-1])}'\n"
        )

    output_file = os.path.join(
        OUTPUT_DIR,
        "final_short.mp4"
    )

    # Convert SRT path for FFmpeg subtitles.
    subtitle_path = os.path.abspath(
        subtitle_file
    ).replace(
        "\\",
        "/"
    ).replace(
        ":",
        "\\:"
    )

    video_filter = (
        "scale=1080:1920,"
        "format=yuv420p,"
        f"subtitles='{subtitle_path}':"
        "force_style="
        "'FontName=DejaVu Sans,"
        "FontSize=18,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=2,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=160'"
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
        adjusted_audio,

        "-vf",
        video_filter,

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

        "-t",
        "30",

        "-movflags",
        "+faststart",

        output_file
    ]

    print()
    print("Creating 1080x1920 Short...")

    subprocess.run(
        command,
        check=True
    )

    print()
    print("=" * 60)
    print("VIDEO CREATED")
    print("=" * 60)
    print(output_file)
    print("=" * 60)

    return output_file
