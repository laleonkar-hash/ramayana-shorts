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

# Used only as a preferred target.
# The actual video duration follows the FULL narration.
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
# CHECK RAM IMAGE
# ============================================================

def check_ram_image():

    if not os.path.exists(RAM_IMAGE):

        raise RuntimeError(
            "Lord Rama image was not found.\n"
            f"Expected file: {RAM_IMAGE}\n\n"
            "Make sure your repository contains:\n"
            "assets/shree-ram.png"
        )

    file_size = os.path.getsize(
        RAM_IMAGE
    )

    if file_size < 10000:

        raise RuntimeError(
            "assets/shree-ram.png appears to be "
            f"invalid or too small ({file_size} bytes)."
        )

    print(
        "Lord Rama image found:",
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

    # Normalize whitespace
    text = " ".join(
        text.split()
    )

    if not text:

        raise RuntimeError(
            "Generated story is empty."
        )

    # Reject punctuation-only responses
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

    # Count meaningful characters
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
# GET MEDIA DURATION
# ============================================================

def get_duration(filename):

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
# GENERATE MARATHI NARRATION
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


def generate_narration(story):

    story = validate_story(
        story
    )

    audio_file = os.path.join(
        OUTPUT_DIR,
        "narration.mp3"
    )

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
        "Story word count:",
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

    # Prevent the previous "." / 3-second problem
    if duration < 5:

        raise RuntimeError(
            "Narration is only "
            f"{duration:.2f} seconds long.\n"
            "The generated story is probably invalid.\n"
            "Pipeline stopped to prevent uploading "
            "a bad Short."
        )

    print(
        "Marathi narration generated successfully."
    )

    return audio_file


# ============================================================
# OPTIONAL AUDIO SPEED ADJUSTMENT
#
# IMPORTANT:
# We NEVER cut the audio.
#
# If narration is already <= 60 sec, we keep it complete.
# If it is slightly longer than 60 sec, we gently speed it up.
# ============================================================

def adjust_audio(audio_file):

    duration = get_duration(
        audio_file
    )

    print()
    print(
        f"Original narration: "
        f"{duration:.2f} seconds"
    )

    # --------------------------------------------------------
    # Ideal case:
    # Keep the complete natural narration.
    # --------------------------------------------------------

    if duration <= 60:

        print(
            "Narration is within Shorts length."
        )

        print(
            "Keeping complete natural narration."
        )

        return audio_file

    # --------------------------------------------------------
    # Longer than 60 sec.
    #
    # We try to bring it below 60 seconds,
    # but NEVER cut the narration.
    # --------------------------------------------------------

    required_speed = (
        duration / 59.0
    )

    # Maximum speed increase
    max_speed = 1.25

    speed = min(
        required_speed,
        max_speed
    )

    # If even 1.25x cannot bring it under 60 sec,
    # do not cut it. Keep the complete narration.
    if duration / speed > 60:

        print(
            "Narration is longer than 60 seconds "
            "even after safe speed adjustment."
        )

        print(
            "Keeping complete narration."
        )

        return audio_file

    adjusted_file = os.path.join(
        OUTPUT_DIR,
        "narration_adjusted.mp3"
    )

    if os.path.exists(
        adjusted_file
    ):

        os.remove(
            adjusted_file
        )

    print(
        f"Adjusting narration speed to "
        f"{speed:.2f}x"
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
            "Marathi narration."
        ) from error

    adjusted_duration = get_duration(
        adjusted_file
    )

    print(
        f"Adjusted narration duration: "
        f"{adjusted_duration:.2f} seconds"
    )

    return adjusted_file


# ============================================================
# CREATE VIDEO
# ============================================================

def create_video(episode):

    ensure_directories()

    print()
    print("=" * 60)
    print("CREATING RAMAYANA SHORT")
    print("=" * 60)

    # --------------------------------------------------------
    # Check image
    # --------------------------------------------------------

    check_ram_image()

    # --------------------------------------------------------
    # Get episode information
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

    print()
    print(
        f"Episode: {episode_number}"
    )

    print(
        f"Title: {title}"
    )

    # --------------------------------------------------------
    # Generate Marathi narration
    # --------------------------------------------------------

    narration_file = generate_narration(
        story
    )

    # --------------------------------------------------------
    # Adjust only if absolutely necessary
    # --------------------------------------------------------

    narration_file = adjust_audio(
        narration_file
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Get the FINAL audio duration.
    # The video will have exactly this duration.
    # --------------------------------------------------------

    narration_duration = get_duration(
        narration_file
    )

    print()
    print("=" * 60)
    print("FULL NARRATION DURATION")
    print("=" * 60)

    print(
        f"{narration_duration:.2f} seconds"
    )

    print(
        "The video will use the COMPLETE narration."
    )

    print(
        "Audio will NOT be cut."
    )

    print(
        "Video will NOT be cut before narration ends."
    )

    print("=" * 60)

    # --------------------------------------------------------
    # Output file
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
    # Gentle cinematic zoom
    #
    # The Rama image remains visible for the entire
    # narration duration.
    # --------------------------------------------------------

    zoom_filter = (
        "scale="
        "1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "zoompan="
        "z='min(zoom+0.0006,1.12)':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        "d=1:"
        "s=1080x1920:"
        "fps=30"
    )

    # --------------------------------------------------------
    # FFmpeg
    #
    # IMPORTANT:
    #
    # - No -shortest
    # - No forced 30-second -t
    #
    # The image is looped for the full audio duration.
    # --------------------------------------------------------

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
        # Complete Marathi audio
        # ----------------------------------------------------

        "-i",
        narration_file,

        # ----------------------------------------------------
        # Video filter
        # ----------------------------------------------------

        "-vf",
        zoom_filter,

        # ----------------------------------------------------
        # Map video
        # ----------------------------------------------------

        "-map",
        "0:v:0",

        # ----------------------------------------------------
        # Map audio
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
        # EXACTLY the full narration duration
        #
        # This is NOT a cut.
        #
        # It tells FFmpeg how long the image should continue.
        # ----------------------------------------------------

        "-t",
        f"{narration_duration:.3f}",

        # ----------------------------------------------------
        # YouTube optimization
        # ----------------------------------------------------

        "-movflags",
        "+faststart",

        output_file
    ]

    print()
    print("=" * 60)
    print("RUNNING FFMPEG")
    print("=" * 60)

    print(
        "Image:",
        RAM_IMAGE
    )

    print(
        "Audio:",
        narration_file
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
        f"Video duration: "
        f"{narration_duration:.2f} seconds"
    )

    print()
    print(
        "Creating video..."
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

    # --------------------------------------------------------
    # Check final video duration
    # --------------------------------------------------------

    final_video_duration = get_duration(
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
        f"Audio duration: "
        f"{narration_duration:.2f} seconds"
    )

    print(
        f"Video duration: "
        f"{final_video_duration:.2f} seconds"
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

    # --------------------------------------------------------
    # Final duration safety check
    #
    # The video should not be substantially shorter than
    # the narration.
    # --------------------------------------------------------

    duration_difference = abs(
        final_video_duration
        -
        narration_duration
    )

    if duration_difference > 0.5:

        raise RuntimeError(
            "Video/audio duration mismatch.\n"
            f"Audio: {narration_duration:.2f}s\n"
            f"Video: {final_video_duration:.2f}s"
        )

    print()
    print(
        "Duration check: PASSED"
    )

    print(
        "Complete narration preserved: YES"
    )

    print(
        "Audio cut: NO"
    )

    print(
        "Video cut: NO"
    )

    print("=" * 60)

    return output_file


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "video_creator.py"
    )

    print(
        "Lord Rama image:"
    )

    print(
        RAM_IMAGE
    )

    if os.path.exists(
        RAM_IMAGE
    ):

        print(
            "Image status: FOUND"
        )

    else:

        print(
            "Image status: NOT FOUND"
        )
