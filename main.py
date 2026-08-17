import os
import sys
import traceback

from story_generator import get_next_episode
from video_creator import create_video
from youtube_uploader import upload_video


# ============================================================
# CONFIGURATION
# ============================================================

MIN_STORY_WORDS = 20


# ============================================================
# PRINT HEADER
# ============================================================

def print_header():

    print()
    print("=" * 60)
    print("DAILY RAMAYANA SHORT")
    print("=" * 60)
    print("Language : Marathi")
    print("Format   : YouTube Short")
    print("Duration : ~30 seconds")
    print("=" * 60)


# ============================================================
# VALIDATE GENERATED STORY
# ============================================================

def validate_story(episode):

    if not episode:

        raise RuntimeError(
            "Story generator returned no episode."
        )

    story = episode.get(
        "story",
        ""
    )

    if story is None:

        raise RuntimeError(
            "Story generator returned an empty story."
        )

    story = str(
        story
    ).strip()

    print()
    print("=" * 60)
    print("STORY BEING SENT TO TTS")
    print("=" * 60)

    print(story)

    print("=" * 60)

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if not story:

        raise RuntimeError(
            "STOPPING: Generated story is empty."
        )

    # --------------------------------------------------------
    # Remove whitespace and count words
    # --------------------------------------------------------

    words = story.split()

    word_count = len(
        words
    )

    print()
    print(
        f"Story word count: {word_count}"
    )

    # --------------------------------------------------------
    # Reject punctuation-only response
    # --------------------------------------------------------

    meaningful_characters = [
        character
        for character in story
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
            "STOPPING: Generated story does not "
            "contain enough meaningful text."
        )

    # --------------------------------------------------------
    # Minimum word check
    # --------------------------------------------------------

    if word_count < MIN_STORY_WORDS:

        raise RuntimeError(
            "STOPPING: Generated story is too short. "
            f"Only {word_count} words were generated. "
            f"Minimum required: {MIN_STORY_WORDS}."
        )

    # --------------------------------------------------------
    # Explicit punctuation check
    # --------------------------------------------------------

    if story in [
        ".",
        "।",
        "...",
        "....",
        "....."
    ]:

        raise RuntimeError(
            "STOPPING: Gemini returned only punctuation."
        )

    print()
    print(
        "Story validation: PASSED"
    )

    return story


# ============================================================
# PRINT EPISODE INFORMATION
# ============================================================

def print_episode_info(
    episode
):

    print()
    print("=" * 60)
    print("SELECTED RAMAYANA EPISODE")
    print("=" * 60)

    print(
        "Episode:",
        episode.get(
            "episode",
            "Unknown"
        )
    )

    print(
        "Title:",
        episode.get(
            "title",
            "Unknown"
        )
    )

    print(
        "Language:",
        "Marathi"
    )

    print("=" * 60)


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print_header()

    video_file = None

    try:

        # ====================================================
        # STEP 1
        # GET NEXT EPISODE + GENERATE STORY
        # ====================================================

        print()
        print("=" * 60)
        print("STEP 1: GENERATING STORY")
        print("=" * 60)

        episode = get_next_episode()

        if not episode:

            raise RuntimeError(
                "No episode was returned."
            )

        print_episode_info(
            episode
        )

        # ====================================================
        # STEP 2
        # VALIDATE STORY
        # ====================================================

        print()
        print("=" * 60)
        print("STEP 2: VALIDATING STORY")
        print("=" * 60)

        validate_story(
            episode
        )

        # ====================================================
        # STEP 3
        # CREATE VIDEO
        # ====================================================

        print()
        print("=" * 60)
        print("STEP 3: CREATING VIDEO")
        print("=" * 60)

        video_file = create_video(
            episode
        )

        if not video_file:

            raise RuntimeError(
                "Video creator returned no video file."
            )

        if not os.path.exists(
            video_file
        ):

            raise RuntimeError(
                f"Video file does not exist: "
                f"{video_file}"
            )

        video_size = os.path.getsize(
            video_file
        )

        if video_size < 10000:

            raise RuntimeError(
                "Generated video is too small "
                "or invalid."
            )

        print()
        print(
            "Video created successfully:"
        )

        print(
            video_file
        )

        print(
            f"Video size: "
            f"{video_size / 1024 / 1024:.2f} MB"
        )

        # ====================================================
        # STEP 4
        # UPLOAD TO YOUTUBE
        # ====================================================

        print()
        print("=" * 60)
        print("STEP 4: UPLOADING TO YOUTUBE")
        print("=" * 60)

        print(
            "Uploading:"
        )

        print(
            video_file
        )

        upload_result = upload_video(
            video_file,
            episode
        )

        # ====================================================
        # SUCCESS
        # ====================================================

        print()
        print("=" * 60)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)

        print(
            "Episode:",
            episode.get(
                "episode",
                "Unknown"
            )
        )

        print(
            "Title:",
            episode.get(
                "title",
                "Unknown"
            )
        )

        print(
            "Language:",
            "Marathi"
        )

        print(
            "Video:",
            video_file
        )

        if upload_result:

            print(
                "YouTube upload result:",
                upload_result
            )

        print("=" * 60)

        return 0

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as error:

        print()
        print("=" * 60)
        print("PIPELINE FAILED")
        print("=" * 60)

        print(
            "Error:"
        )

        print(
            str(error)
        )

        print()
        print(
            "Traceback:"
        )

        traceback.print_exc()

        print("=" * 60)

        # IMPORTANT:
        # Returning a non-zero exit code makes
        # GitHub Actions show the workflow as FAILED.

        return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    exit_code = main()

    sys.exit(
        exit_code
    )
