from story_generator import (
    get_next_episode,
    load_episodes,
    save_state,
    get_episode_number
)

from video_creator import create_video

from youtube_uploader import upload_video


def main():

    print()
    print("=" * 70)
    print("        DAILY RAMAYANA SHORT GENERATOR")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Select next episode and generate Gemini story
    # --------------------------------------------------------

    episode = get_next_episode()

    print()
    print(
        "Selected episode:"
    )

    print(
        episode["episode"],
        "-",
        episode["title"]
    )

    # --------------------------------------------------------
    # 2. Create video
    # --------------------------------------------------------

    video_file = create_video(
        episode
    )

    # --------------------------------------------------------
    # 3. Upload to YouTube
    # --------------------------------------------------------

    youtube_url = upload_video(
        video_file,
        episode
    )

    # --------------------------------------------------------
    # 4. Update episode state ONLY after
    #    successful YouTube upload
    # --------------------------------------------------------

    episodes = load_episodes()

    episode_numbers = []

    for item in episodes:

        try:

            episode_numbers.append(
                get_episode_number(item)
            )

        except Exception:

            continue

    current_episode = episode[
        "episode"
    ]

    future_episodes = [
        number
        for number in episode_numbers
        if number > current_episode
    ]

    if future_episodes:

        next_episode = min(
            future_episodes
        )

    else:

        # Restart from first episode
        # after reaching the end.

        next_episode = min(
            episode_numbers
        )

    save_state(
        next_episode
    )

    print()
    print("=" * 70)
    print("       DAILY RAMAYANA SHORT COMPLETE")
    print("=" * 70)

    print(
        "Episode:",
        current_episode
    )

    print(
        "Title:",
        episode["title"]
    )

    print(
        "YouTube:",
        youtube_url
    )

    print(
        "Next episode:",
        next_episode
    )

    print("=" * 70)


if __name__ == "__main__":

    main()
