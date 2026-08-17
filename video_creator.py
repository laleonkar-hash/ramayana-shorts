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


# ============================================================
# DIRECTORIES
# ============================================================

def ensure_directories():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    os.makedirs(
        TEMP_DIR,
        exist_ok=True
    )


# ============================================================
# FONT
# ============================================================

def get_font(size):

    fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]

    for font_path in fonts:

        if os.path.exists(font_path):

            return ImageFont.truetype(
                font_path,
                size
            )

    return ImageFont.load_default()


# ============================================================
# CREATE IMAGE SCENE
# ============================================================

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

    # Border

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

    # Decorative circle

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

    # Om

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

    # RAMAYANA

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

    # Title

    wrapped_title = textwrap.fill(
        str(title),
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

    # Scene number

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

    image.save(
        filename
    )

    return filename


# ============================================================
# TEXT TO SPEECH
# ============================================================

async def generate_voice(
    text,
    audio_file,
    subtitle_file
):

    communicate = edge_tts.Communicate(
        text=text,
        voice="en-IN-NeerjaNeural",
        rate="+0%",
        volume="+0%"
    )

    await communicate.save(
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

    print()
    print(
        "Generating voice narration..."
    )

    asyncio.run(
        generate_voice(
            text,
            audio_file,
            subtitle_file
        )
    )

    if not os.path.exists(
        audio_file
    ):

        raise RuntimeError(
            "Edge TTS did not create narration.mp3"
        )

    print(
        "Narration created:",
        audio_file
    )

    return (
        audio_file,
        subtitle_file
    )


# ============================================================
# AUDIO DURATION
# ============================================================

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


# ============================================================
# MAKE AUDIO APPROXIMATELY 30 SECONDS
# ============================================================

def make_audio_30_seconds(
    audio_file
):

    duration = get_duration(
        audio_file
    )

    print()
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

    # Keep voice speed within reasonable limits.

    speed = max(
        1.0,
        min(
            2.0,
            speed
        )
    )

    print(
        f"Voice speed: {speed:.3f}x"
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

    print(
        "Adjusting narration..."
    )

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


# ============================================================
# CREATE SCENES FILE
# ============================================================

def create_scenes_file(
    scene_files,
    duration
):

    concat_file = os.path.join(
        TEMP_DIR,
        "scenes.txt"
    )

    scene_duration = (
        duration /
        len(scene_files)
    )

    with open(
        concat_file,
        "w",
        encoding="utf-8"
    ) as f:

        for scene_file in scene_files:

            absolute_path = os.path.abspath(
                scene_file
            )

            # FFmpeg concat files can have
            # problems with certain characters.
            #
            # Our generated filenames are simple,
            # so this is safe.

            f.write(
                f"file '{absolute_path}'\n"
            )

            f.write(
                f"duration {scene_duration:.6f}\n"
            )

        # FFmpeg concat demuxer needs the last
        # file repeated.

        last_file = os.path.abspath(
            scene_files[-1]
        )

        f.write(
            f"file '{last_file}'\n"
        )

    return concat_file


# ============================================================
# CREATE FINAL VIDEO
# ============================================================

def create_video(episode):

    ensure_directories()

    print()
    print("=" * 60)
    print("CREATING RAMAYANA SHORT")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Generate narration
    # --------------------------------------------------------

    audio_file, subtitle_file = generate_audio(
        episode["story"]
    )

    # --------------------------------------------------------
    # 2. Adjust audio
    # --------------------------------------------------------

    adjusted_audio = make_audio_30_seconds(
        audio_file
    )

    # --------------------------------------------------------
    # 3. Determine duration
    # --------------------------------------------------------

    duration = get_duration(
        adjusted_audio
    )

    print(
        f"Final audio duration: "
        f"{duration:.2f} seconds"
    )

    # --------------------------------------------------------
    # 4. Create scenes
    # --------------------------------------------------------

    print()
    print(
        "Creating visual scenes..."
    )

    scene_files = []

    for scene_number in range(
        1,
        5
    ):

        scene_file = create_scene(
            episode["title"],
            episode["episode"],
            scene_number
        )

        scene_files.append(
            scene_file
        )

    # --------------------------------------------------------
    # 5. Create concat file
    # --------------------------------------------------------

    concat_file = create_scenes_file(
        scene_files,
        duration
    )

    print(
        "Scenes file:",
        concat_file
    )

    # --------------------------------------------------------
    # 6. Final output
    # --------------------------------------------------------

    output_file = os.path.join(
        OUTPUT_DIR,
        "final_short.mp4"
    )

    # ========================================================
    # IMPORTANT:
    #
    # NO SUBTITLE FILTER HERE.
    #
    # We are intentionally removing subtitles for now.
    # First we need to make sure FFmpeg successfully creates
    # the video.
    # ========================================================

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

        "-map",
        "0:v:0",

        "-map",
        "1:a:0",

        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

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
    print("=" * 60)
    print("RUNNING FFMPEG")
    print("=" * 60)

    print(
        "Creating:",
        output_file
    )

    print(
        "Resolution:",
        "1080x1920"
    )

    print(
        "Subtitles:",
        "TEMPORARILY DISABLED"
    )

    print("=" * 60)

    try:

        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )

    except subprocess.CalledProcessError as error:

        print()
        print("=" * 60)
        print("FFMPEG FAILED")
        print("=" * 60)

        print(
            "Exit code:",
            error.returncode
        )

        print()
        print(
            "FFmpeg output:"
        )

        print(
            error.stdout
        )

        print(
            error.stderr
        )

        print("=" * 60)

        raise RuntimeError(
            "FFmpeg failed while creating "
            "the video."
        ) from error

    # --------------------------------------------------------
    # 7. Verify output
    # --------------------------------------------------------

    if not os.path.exists(
        output_file
    ):

        raise RuntimeError(
            "FFmpeg finished but final_short.mp4 "
            "was not created."
        )

    file_size = os.path.getsize(
        output_file
    )

    if file_size < 10000:

        raise RuntimeError(
            "final_short.mp4 was created but "
            "the file appears to be invalid."
        )

    print()
    print("=" * 60)
    print("VIDEO CREATED SUCCESSFULLY")
    print("=" * 60)

    print(
        "File:",
        output_file
    )

    print(
        "Size:",
        f"{file_size / 1024 / 1024:.2f} MB"
    )

    print(
        "Resolution:",
        "1080x1920"
    )

    print("=" * 60)

    return output_file
