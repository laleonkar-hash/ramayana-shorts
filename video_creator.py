import asyncio
import os
import subprocess

import edge_tts


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_DIR = "output"
TEMP_DIR = "temp"

RAM_IMAGE = os.path.join(
    "assets",
    "shree-ram.png"
)

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920

TARGET_DURATION = 30.0

# Marathi female voice
TTS_VOICE = "mr-IN-AarohiNeural"


# ============================================================
# DIRECTORY SETUP
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
# CHECK REQUIRED FILES
# ============================================================

def check_ram_image():

    if not os.path.exists(
        RAM_IMAGE
    ):

        raise RuntimeError(
            "Lord Rama image was not found.\n"
            f"Expected file: {RAM_IMAGE}\n\n"
            "Please make sure your GitHub repository "
            "contains:\n"
            "assets/shree-ram.png"
        )

    file_size = os.path.getsize(
        RAM_IMAGE
    )

    if file_size < 10000:

        raise RuntimeError(
            "assets/shree-ram.png appears to be invalid "
            f"or too small ({file_size} bytes)."
        )

    print(
        "Lord Rama image found:"
    )

    print(
        RAM_IMAGE
    )


# ============================================================
# STORY VALIDATION
# ============================================================

def validate_story(text):

    if text is None:

        raise RuntimeError(
            "Story is empty."
        )

    text = str(
        text
    ).strip()

    # Remove extra whitespace

    text = " ".join(
        text.split()
    )

    # --------------------------------------------------------
    # Reject empty story
    # --------------------------------------------------------

    if not text:

        raise RuntimeError(
            "Story is empty."
        )

    # --------------------------------------------------------
    # Reject punctuation-only story
    # --------------------------------------------------------

    if text in [
        ".",
        "।",
        "...",
        "....",
        "....."
    ]:

        raise RuntimeError(
            "Generated story contains only punctuation."
        )

    # --------------------------------------------------------
    # Count meaningful characters
    # --------------------------------------------------------

    meaningful_characters = [
        character
        for character in text
        if character.isalnum()
        or
        (
            "\u0900"
            <= character
            <= "\u097F"
        )
    ]

    if len(
        meaningful_characters
    ) < 20:

        raise RuntimeError(
            "Generated story is too short or invalid."
        )

    # --------------------------------------------------------
    # Word count
    # --------------------------------------------------------

    word_count = len(
        text.split()
    )

    if word_count < 20:

        raise RuntimeError(
            "Generated story contains only "
            f"{word_count} words. "
            "At least 20 words are required."
        )

    return text


# ============================================================
# AUDIO DURATION
# ============================================================

def get_duration(
    filename
):

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        filename
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True
    )

    duration_text = (
        result.stdout.strip()
    )

    if not duration_text:

        raise RuntimeError(
            f"Could not determine duration of {filename}"
        )

    return float(
        duration_text
    )


# ============================================================
# GENERATE MARATHI AUDIO
# ============================================================

async def _generate_tts(
    text,
    output_file
):

    communicate = edge_tts.Communicate(
        text=text,
        voice=TTS_VOICE,
        rate="+0%",
        volume="+0%"
    )

    await communicate.save(
        output_file
    )


def generate_narration(
    story
):

    story = validate_story(
        story
    )

    audio_file = os.path.join(
        OUTPUT_DIR,
        "narration.mp3"
    )

    # Remove previous audio

    if os.path.exists(
        audio_file
    ):

        os.remove(
            audio_file
        )

    print()
    print("=" * 60)
    print("MARATHI NARRATION")
    print("=" * 60)

    print(
        "Voice:",
        TTS_VOICE
    )

    print(
        "Word count:",
        len(story.split())
    )

    print()
    print("Story:")
    print(story)

    print("=" * 60)

    try:

        asyncio.run(
            _generate_tts(
                story,
                audio_file
            )
        )

    except Exception as error:

        raise RuntimeError(
            "Marathi voice generation failed: "
            f"{error}"
        ) from error

    if not os.path.exists(
        audio_file
    ):

        raise RuntimeError(
            "Marathi narration file was not created."
        )

    duration = get_duration(
        audio_file
    )

    print()
    print(
        f"Original narration duration: "
        f"{duration:.2f} seconds"
    )

    # --------------------------------------------------------
    # Catch the previous 3-second problem
    # --------------------------------------------------------

    if duration < 5:

        raise RuntimeError(
            "Narration is only "
            f"{duration:.2f} seconds long.\n"
            "The story was probably not generated correctly.\n"
            "The pipeline has been stopped to prevent "
            "uploading a bad Short."
        )

    print(
        "Marathi narration generated successfully."
    )

    return audio_file


# ============================================================
# ADJUST AUDIO TO APPROXIMATELY 30 SECONDS
# ============================================================

def adjust_audio(
    audio_file
):

    duration = get_duration(
        audio_file
    )

    # Already approximately 30 sec

    if (
        duration >= 27
        and
        duration <= 30
    ):

        print(
            "Narration already has a good duration."
        )

        return audio_file

    # --------------------------------------------------------
    # Shorter than 30 sec
    #
    # DO NOT artificially stretch the voice.
    # We keep natural narration and allow the video
    # to use the remaining seconds.
    # --------------------------------------------------------

    if duration < 27:

        print(
            f"Narration is {duration:.2f} seconds."
        )

        print(
            "Keeping natural Marathi speaking speed."
        )

        return audio_file

    # --------------------------------------------------------
    # Longer than 30 sec
    # --------------------------------------------------------

    speed = (
        duration /
        TARGET_DURATION
    )

    # Maximum 1.25x to keep narration natural

    if speed > 1.25:

        speed = 1.25

    print()
    print(
        f"Narration is {duration:.2f} seconds."
    )

    print(
        f"Adjusting narration speed to "
        f"{speed:.2f}x"
    )

    adjusted_file = os.path.join(
        OUTPUT_DIR,
        "narration_30s.mp3"
    )

    if os.path.exists(
        adjusted_file
    ):

        os.remove(
            adjusted_file
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

        adjusted_file
    ]

    try:

        subprocess.run(
            command,
            check=True
        )

    except subprocess.CalledProcessError as error:

        raise RuntimeError(
            "FFmpeg failed while adjusting "
            "the Marathi narration."
        ) from error

    final_duration = get_duration(
        adjusted_file
    )

    print(
        f"Adjusted narration duration: "
        f"{final_duration:.2f} seconds"
    )

    return adjusted_file


# ============================================================
# CREATE FINAL VIDEO
# ============================================================

def create_video(
    episode
):

    ensure_directories()

    print()
    print("=" * 60)
    print("CREATING RAMAYANA SHORT")
    print("=" * 60)

    # --------------------------------------------------------
    # Check Rama image
    # --------------------------------------------------------

    check_ram_image()

    # --------------------------------------------------------
    # Get story
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

    narration = generate_narration(
        story
    )

    # --------------------------------------------------------
    # Adjust narration
    # --------------------------------------------------------

    narration_file = adjust_audio(
        narration
    )

    narration_duration = get_duration(
        narration_file
    )

    print()
    print(
        f"Final narration duration: "
        f"{narration_duration:.2f} seconds"
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    output_file = os.path.join(
        OUTPUT_DIR,
        "final_short.mp4"
    )

    if os.path.exists(
        output_file
    ):

        os.remove(
            output_file
        )

    # --------------------------------------------------------
    # Determine video duration
    #
    # Always make a 30-second Short.
    # If narration is shorter, remaining time is silent.
    # --------------------------------------------------------

    video_duration = TARGET_DURATION

    # --------------------------------------------------------
    # FFmpeg filter
    #
    # The Rama image:
    #
    # 1. Is scaled to fill 1080x1920
    # 2. Has a gentle zoom effect
    # 3. Is converted to 30fps
    #
    # This creates movement instead of a completely
    # static image.
    # --------------------------------------------------------

    zoom_filter = (
        "scale="
        "1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "zoompan="
        "z='min(zoom+0.0008,1.12)':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        "d=1:"
        "s=1080x1920:"
        "fps=30"
    )

    command = [
        "ffmpeg",
        "-y",

        # ----------------------------------------------------
        # Rama image
        # ----------------------------------------------------

        "-loop",
        "1",

        "-i",
        RAM_IMAGE,

        # ----------------------------------------------------
        # Marathi narration
        # ----------------------------------------------------

        "-i",
        narration_file,

        # ----------------------------------------------------
        # Video filter
        # ----------------------------------------------------

        "-vf",
        zoom_filter,

        # ----------------------------------------------------
        # Video duration
        # ----------------------------------------------------

        "-t",
        str(video_duration),

        # ----------------------------------------------------
        # Video mapping
        # ----------------------------------------------------

        "-map",
        "0:v:0",

        # ----------------------------------------------------
        # Audio mapping
        # ----------------------------------------------------

        "-map",
        "1:a:0",

        # ----------------------------------------------------
        # Video codec
        # ----------------------------------------------------

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        # ----------------------------------------------------
        # Audio codec
        # ----------------------------------------------------

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-ar",
        "44100",

        # ----------------------------------------------------
        # Prevent audio/video from exceeding target
        # ----------------------------------------------------

        "-shortest",

        # ----------------------------------------------------
        # YouTube optimization
        # ----------------------------------------------------

        "-movflags",
        "+faststart",

        output_file
    ]

    print()
    print("=" * 60)
    print("CREATING 1080x1920 SHORT")
    print("=" * 60)

    print(
        "Image:",
        RAM_IMAGE
    )

    print(
        "Voice:",
        TTS_VOICE
    )

    print(
        "Resolution:",
        "1080x1920"
    )

    print(
        "Target duration:",
        "30 seconds"
    )

    print()
    print(
        "Running FFmpeg..."
    )

    try:

        subprocess.run(
            command,
            check=True
        )

    except subprocess.CalledProcessError as error:

        print()
        print("=" * 60)
        print("FFMPEG FAILED")
        print("=" * 60)

        print(
            "Command:"
        )

        print(
            " ".join(command)
        )

        print("=" * 60)

        raise RuntimeError(
            "FFmpeg failed while creating "
            "the final Ramayana Short."
        ) from error

    # --------------------------------------------------------
    # Verify output
    # --------------------------------------------------------

    if not os.path.exists(
        output_file
    ):

        raise RuntimeError(
            "FFmpeg completed but "
            "final_short.mp4 was not created."
        )

    file_size = os.path.getsize(
        output_file
    )

    if file_size < 10000:

        raise RuntimeError(
            "Generated video is invalid or too small."
        )

    final_duration = get_duration(
        output_file
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
        f"Size: "
        f"{file_size / 1024 / 1024:.2f} MB"
    )

    print(
        f"Duration: "
        f"{final_duration:.2f} seconds"
    )

    print(
        "Resolution: 1080x1920"
    )

    print(
        "Visual: Lord Rama"
    )

    print(
        "Audio: Marathi"
    )

    print("=" * 60)

    return output_file


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "video_creator.py is ready."
    )

    print(
        "Expected Rama image:"
    )

    print(
        RAM_IMAGE
    )

    if os.path.exists(
        RAM_IMAGE
    ):

        print(
            "Rama image: FOUND"
        )

    else:

        print(
            "Rama image: NOT FOUND"
        )
