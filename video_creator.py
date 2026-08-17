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

TARGET_DURATION = 30.0


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

    title_font = get_font(64)
    episode_font = get_font(42)
    small_font = get_font(30)

    # Outer frame
    draw.rounded_rectangle(
        (
            45,
            45,
            WIDTH - 45,
            HEIGHT - 45
        ),
        radius=35,
        outline=(220, 180, 100),
        width=5
    )

    # Decorative circles
    draw.ellipse(
        (
            120,
            180,
            960,
            1020
        ),
        outline=(220, 180, 100),
        width=6
    )

    draw.ellipse(
        (
            190,
            250,
            890,
            950
        ),
        outline=(150, 110, 70),
        width=3
    )

    # Om symbol
    draw.text(
        (
            WIDTH // 2,
            510
        ),
        "ॐ",
        font=title_font,
        fill=(245, 200, 110),
        anchor="mm"
    )

    # Ramayana
    draw.text(
        (
            WIDTH // 2,
            1110
        ),
        "RAMAYANA",
        font=title_font,
        fill=(245, 220, 170),
        anchor="mm"
    )

    # Episode
    draw.text(
        (
            WIDTH // 2,
            1200
        ),
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
        (
            WIDTH // 2,
            1380
        ),
        wrapped_title,
        font=episode_font,
        fill=(255, 255, 255),
        anchor="mm",
        align="center"
    )

    draw.text(
        (
            WIDTH // 2,
            1740
        ),
        f"Scene {scene_number}",
        font=small_font,
        fill=(190, 185, 185),
        anchor="mm"
    )

    filename = os.path.join(
        TEMP_DIR,
        f"scene_{scene_number}.png"
    )

    image.save(filename)

    return filename


async def generate_voice(
    text,
    audio_file,
    subtitle_file
):

    voice = edge_tts.Communicate(
        text=text,
        voice="en-IN-NeerjaNeural",
        rate="+0%",
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


def make_audio_30_seconds(
    audio_file
):

    duration = get_duration(
        audio_file
    )

    print(
        f"Original narration duration: "
        f"{duration:.2f} seconds"
    )

    if duration <= TARGET_DURATION:

        speed = 1.0

    else:

        speed = (
            duration /
            TARGET_DURATION
        )

    # FFmpeg atempo supports values
    # between 0.5 and 2.0.
    speed = max(
        1.0,
        min(
            2.0,
            speed
        )
    )

    print(
        f"Audio speed adjustment: "
        f"{speed:.3f}x"
    )

    adjusted_audio = os.path.join(
        OUTPUT_DIR,
        "narration_30s.mp3"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        audio_file,
        "-filter:a",
        f"atempo={speed:.6f}",
        "-ar",
        "44100",
        "-ac",
        "2",
        adjusted_audio
    ]

    subprocess.run(
        command,
        check=True
    )

    final_duration = get_duration(
        adjusted_audio
    )

    print(
        f"Adjusted narration duration: "
        f"{final_duration:.2f} seconds"
    )

    return adjusted_audio


def create_video(episode):

    ensure_directories()

    print()
    print("Generating narration...")

    audio_file, subtitle_file = generate_audio(
        episode["story"]
    )

    adjusted_audio = make_audio_30_seconds(
        audio_file
    )

    final_duration = get_duration(
        adjusted_audio
    )

    # We always create exactly four scenes.
    scene_files = []

    for scene_number in range(1, 5):

        scene = create_scene(
            episode["title"],
            episode["episode"],
            scene_number
        )

        scene_files.append(scene)

    # Each scene gets an equal duration.
    scene_duration = (
        final_duration /
        len(scene_files)
    )

    concat_file = os.path.join(
        TEMP_DIR,
        "scenes.txt"
    )

    with open(
        concat_file,
        "w",
        encoding="utf-8"
    ) as f:

        for scene in scene_files:

            absolute_scene = os.path.abspath(
                scene
            )

            f.write(
                f"file '{absolute_scene}'\n"
            )

            f.write(
                f"duration {scene_duration:.6f}\n"
            )

        # concat demuxer needs the last file
        # repeated without a duration.
        f.write(
            f"file '{os.path.abspath(scene_files[-1])}'\n"
        )

    output_file = os.path.join(
        OUTPUT_DIR,
        "final_short.mp4"
    )

    # IMPORTANT:
    # Do NOT escape the colon between the
    # subtitle filename and force_style.
    #
    # This was the problem in the previous version.

    subtitle_path = os.path.abspath(
        subtitle_file
    )

    subtitle_path = subtitle_path.replace(
        "\\",
        "/"
    )

    # Escape characters that matter inside
    # the FFmpeg filter expression.
    subtitle_path = subtitle_path.replace(
        "'",
        r"\'"
    )

    subtitle_filter = (
        "subtitles="
        f"filename='{subtitle_path}'"
        ":force_style="
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

    video_filter = (
        "scale=1080:1920,"
        "format=yuv420p,"
        + subtitle_filter
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
        f"{TARGET_DURATION}",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        output_file
    ]

    print()
    print("Creating 1080x1920 Short...")

    print()
    print("Running FFmpeg...")

    try:

        subprocess.run(
            command,
            check=True
        )

    except subprocess.CalledProcessError:

        print()
        print("=" * 60)
        print("FFMPEG VIDEO CREATION FAILED")
        print("=" * 60)

        print(
            "Command used:"
        )

        print(
            " ".join(command)
        )

        print("=" * 60)

        raise

    print()
    print("=" * 60)
    print("VIDEO CREATED SUCCESSFULLY")
    print("=" * 60)

    print(
        "File:",
        output_file
    )

    print(
        "Duration:",
        f"{TARGET_DURATION:.0f} seconds"
    )

    print(
        "Resolution:",
        "1080x1920"
    )

    print("=" * 60)

    return output_file
