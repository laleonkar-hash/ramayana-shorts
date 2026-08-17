import os
import shutil

from story_generator import (
    get_next_episode,
    save_episode_state
)

from video_creator import create_video

from youtube_uploader import upload_video


def main():

    print()
    print("=" * 60)
    print("DAILY RAMAYANA SHORT")
    print("=" * 60)

    episode = get_next_episode()

    print()
    print("Episode:", episode["episode"])
    print("Title:", episode["title"])
    print()

    print("Narration:")
    print(episode["narration"])
    print()

    try:

        video_file = create_video(
            episode
        )

        print()
        print("Video generation complete.")
        print(video_file)
        print()

        youtube_url = upload_video(
            video_file,
            episode
        )

        # Save state ONLY after successful YouTube upload.
        save_episode_state(
            episode["episode"]
        )

        print()
        print("=" * 60)
        print("DAILY RAMAYANA SHORT COMPLETE")
        print("=" * 60)
        print()
        print("Episode:", episode["episode"])
        print("YouTube:", youtube_url)
        print()

    except Exception as error:

        print()
        print("=" * 60)
        print("PIPELINE FAILED")
        print("=" * 60)
        print()
        print(type(error).__name__)
        print(str(error))
        print()

        raise


if __name__ == "__main__":
    main()
