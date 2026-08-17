import os
import sys
import traceback

from story_generator import (
    get_next_episode,
    load_state,
    save_state
)

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
    print("Duration : Full narration")
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
    # Empty story
    # --------------------------------------------------------

    if not story:

        raise RuntimeError(
            "STOPPING: Generated story is empty."
        )

    # --------------------------------------------------------
    # Count words
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
    # Meaningful characters
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
    # Minimum words
    # --------------------------------------------------------

    if word_count < MIN_STORY_WORDS:

        raise RuntimeError(
            "STOPPING: Generated story is too short. "
            f"Only {word_count} words were generated. "
            f"Minimum required: {MIN_STORY_WORDS}."
        )

    # --------------------------------------------------------
    # Punctuation-only response
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
# ADVANCE EPISODE
# ============================================================

def advance_episode(
    current_episode
):

    try:

        current_episode = int(
            current_episode
        )

    except (
        ValueError,
        TypeError
    ):

        raise RuntimeError(
            "Invalid current episode number: "
            f"{current_episode}"
        )

    next_episode = (
        current_episode + 1
    )

    save_state(
        next_episode
    )

    print()
    print("=" * 60)
    print("EPISODE STATE UPDATED")
    print("=" * 60)

    print(
        "Completed episode:",
        current_episode
    )

    print(
        "Next episode:",
        next_episode
    )

    print(
        "State file:",
        "episode_state.json"
    )

    print("=" * 60)

    return next_episode


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

        # ----------------------------------------------------
        # Remember the state BEFORE this run.
        # ----------------------------------------------------

        state_before = load_state()

        print(
            "Episode state before run:",
            state_before
        )

        # ----------------------------------------------------
        # Generate the episode.
        # ----------------------------------------------------

        episode = get_next_episode()

        if not episode:

            raise RuntimeError(
                "No episode was returned."
            )

        print_episode_info(
            episode
        )

        # ----------------------------------------------------
        # Verify selected episode.
        # ----------------------------------------------------

        current_episode = episode.get(
            "episode"
        )

        if current_episode is None:

            raise RuntimeError(
                "Selected episode has no episode number."
            )

        try:

            current_episode = int(
                current_episode
            )

        except (
            ValueError,
            TypeError
        ):

            raise RuntimeError(
                "Invalid episode number: "
                f"{current_episode}"
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

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # This function must finish successfully before
        # we advance the episode.
        # ----------------------------------------------------

        upload_result = upload_video(
            video_file,
            episode
        )

        print()
        print(
            "YouTube upload completed successfully."
        )

        # ====================================================
        # STEP 5
        # ADVANCE EPISODE
        # ====================================================

        print()
        print("=" * 60)
        print("STEP 5: ADVANCING EPISODE")
        print("=" * 60)

        next_episode = advance_episode(
            current_episode
        )

        # ====================================================
        # SUCCESS
        # ====================================================

        print()
        print("=" * 60)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)

        print(
            "Completed episode:",
            current_episode
        )

        print(
            "Next episode:",
            next_episode
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

        print()
        print(
            "IMPORTANT:"
        )

        print(
            "episode_state.json now contains:"
        )

        print(
            f'{{"next_episode": {next_episode}}}'
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

        print()
        print(
            "IMPORTANT:"
        )

        print(
            "Episode state was NOT advanced."
        )

        print(
            "The same episode can be retried."
        )

        print("=" * 60)

        return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    exit_code = main()

    sys.exit(
        exit_code
    )
