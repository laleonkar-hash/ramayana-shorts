import asyncio
import os
import subprocess
import textwrap

import edge_tts
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_DIR = "output"
TEMP_DIR = "temp"

WIDTH = 1080
HEIGHT = 1920

TARGET_DURATION = 30.0

# Marathi female voice
TTS_VOICE = "mr-IN-AarohiNeural"


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
# CREATE VISUAL SCENE
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

    # Episode number

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
# STORY VALIDATION
# ============================================================

def validate_story(text):

    if text is None:

        raise RuntimeError(
            "Story is empty."
        )

    text = str(text).strip()

    # Remove whitespace

    cleaned = " ".join(
        text.split()
    )

    # Reject punctuation-only stories

    meaningful_characters = [
        c for c in cleaned
        if c.isalnum()
        or
        ("\u0900" <= c <= "\u097F")
    ]

    if len(meaningful_characters) < 20:

        raise RuntimeError(
            "Generated story is invalid or too short. "
            f"Received: {repr(text)}"
        )

    words = cleaned.split()

    if len(words) < 20:

        raise RuntimeError(
            "Generated story contains too few words. "
            f"Only {len(words)} words were received."
        )

    # Explicitly reject the problem we saw

    if cleaned in [
        ".",
        "।",
        "...",
        "...."
    ]:

        raise RuntimeError(
            "Story contains only punctuation."
        )

    return cleaned


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

        # IMPORTANT:
        # Marathi voice
        voice=TTS_VOICE,

        rate="+0%",

        volume="+0%"
    )

    await communicate.save(
        audio_file,
        subtitle_file
    )


def generate_audio(text):

    ensure_directories()

    # --------------------------------------------------------
    # Validate BEFORE TTS
    # --------------------------------------------------------

    text = validate_story(
        text
    )

    print()
    print("=" * 60)
    print("MARATHI TEXT TO SPEECH")
    print("=" * 60)

    print(
        "Voice:",
        TTS_VOICE
    )

    print(
        "Story word count:",
        len(text.split())
    )

    print()
    print(
        "Story:"
    )

    print(text)

    print("=" * 60)

    audio_file = os.path.join(
        OUTPUT_DIR,
        "narration.mp3"
    )

    subtitle_file = os.path.join(
        OUTPUT_DIR,
        "narration.srt"
    )

    # Remove old files

    for filename in [
        audio_file,
        subtitle_file
    ]:

        if os.path.exists(filename):

            os.remove(filename)

    print()
    print(
        "Generating Marathi narration..."
    )

    try:

        asyncio.run(
            generate_voice(
                text,
                audio_file,
                subtitle_file
            )
        )

    except Exception as error:

        raise RuntimeError(
            "Marathi TTS generation failed: "
            f"{error}"
        ) from error

    if not os.path.exists(
        audio_file
    ):

        raise RuntimeError(
            "Edge TTS did not create narration.mp3"
        )

    duration = get_duration(
        audio_file
    )

    print(
        f"Generated narration duration: "
        f"{duration:.2f} seconds"
    )

    # A real 20+ word story should never be
    # only a few seconds.

    if duration < 5:

        raise RuntimeError(
            "Narration is suspiciously short "
            f"({duration:.2f} seconds). "
            "The pipeline will stop instead of "
            "uploading a bad video."
        )

    print(
        "Marathi narration created successfully."
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

    value = result.stdout.strip()

    if not value:

        raise RuntimeError(
            "Could not determine audio duration."
        )

    return float(value)


# ============================================================
# ADJUST NARRATION
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

    # --------------------------------------------------------
    # If narration is shorter than 30 sec:
    #
    # DO NOT speed it up.
    #
    # We keep the natural Marathi narration speed.
    # The video will be extended to 30 sec.
    # --------------------------------------------------------

    if duration <= TARGET_DURATION:

        print(
            "Narration is shorter than 30 seconds."
        )

        print(
            "Keeping natural Marathi speaking speed."
        )

        return audio_file

    # --------------------------------------------------------
    # If narration is longer than 30 sec:
    # Slightly increase speaking speed.
    # --------------------------------------------------------

    speed = (
        duration /
        TARGET_DURATION
    )

    # Don't make Marathi narration unnaturally fast.

    speed = min(
        speed,
        1.25
    )

    print(
        f"Adjusting narration speed to "
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


# ============================================================
# CREATE CONCAT FILE
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
        TARGET_DURATION /
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

            f.write(
                f"file '{absolute_path}'\n"
            )

            f.write(
                f"duration {scene_duration:.6f}\n"
            )

        # Repeat last frame

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

def create_video(
    episode
):

    ensure_directories()

    print()
    print("=" * 60)
    print("CREATING RAMAYANA MARATHI SHORT")
    print("=" * 60)

    # --------------------------------------------------------
    # Story
    # --------------------------------------------------------

    story = episode.get(
        "story",
        ""
    )

    title = episode.get(
        "title",
        "रामायण कथा"
    )

    episode_number = episode.get(
        "episode",
        1
    )

    # --------------------------------------------------------
    # Generate Marathi narration
    # --------------------------------------------------------

    audio_file, subtitle_file = generate_audio(
        story
    )

    # --------------------------------------------------------
    # Adjust narration
    # --------------------------------------------------------

    adjusted_audio = make_audio_30_seconds(
        audio_file
    )

    narration_duration = get_duration(
        adjusted_audio
    )

    print()
    print(
        f"Narration duration: "
        f"{narration_duration:.2f} seconds"
    )

    # --------------------------------------------------------
    # Create scenes
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
            title,
            episode_number,
            scene_number
        )

        scene_files.append(
            scene_file
        )

    # --------------------------------------------------------
    # Create concat file
    # --------------------------------------------------------

    concat_file = create_scenes_file(
        scene_files,
        TARGET_DURATION
    )

    # --------------------------------------------------------
    # Final video
    # --------------------------------------------------------

    output_file = os.path.join(
        OUTPUT_DIR,
        "final_short.mp4"
    )

    # IMPORTANT:
    # Subtitles are intentionally NOT burned in here.
    # This avoids the previous FFmpeg subtitle error.

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

    try:

        subprocess.run(
            command,
            check=True
        )

    except subprocess.CalledProcessError as error:

        raise RuntimeError(
            "FFmpeg failed while creating "
            "the final video."
        ) from error

    # --------------------------------------------------------
    # Verify output
    # --------------------------------------------------------

    if not os.path.exists(
        output_file
    ):

        raise RuntimeError(
            "final_short.mp4 was not created."
        )

    file_size = os.path.getsize(
        output_file
    )

    if file_size < 10000:

        raise RuntimeError(
            "final_short.mp4 appears to be invalid."
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
        f"Size: {file_size / 1024 / 1024:.2f} MB"
    )

    print(
        "Resolution: 1080x1920"
    )

    print(
        "Audio: Marathi"
    )

    print("=" * 60)

    return output_file
