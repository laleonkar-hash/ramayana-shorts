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

    # 1. Select episode + generate unique Gemini story.
    episode = get_next_episode()

    print()
    print("Selected episode:")
    print(
        episode["episode"],
        "-",
        episode["title"]
    )

    # 2. Create video.
    video_file = create_video(
        episode
    )

    # 3. Upload to YouTube.
    youtube_url = upload_video(
        video_file,
        episode
    )

    # 4. Only after successful upload,
    #    advance to the next episode.
    episodes = load_episodes()

    episode_numbers = [
        get_episode_number(item)
        for item in episodes
    ]

    current = episode["episode"]

    larger = [
        number
        for number in episode_numbers
        if number > current
    ]

    if larger:

        next_episode = min(
            larger
        )

    else:

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
        episode["episode"]
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
