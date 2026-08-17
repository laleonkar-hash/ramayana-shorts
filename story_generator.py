import json
import os
import re


EPISODES_FILE = "ramayana_episodes.json"
STATE_FILE = "episode_state.txt"


def load_episodes():
    with open(EPISODES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_current_episode_number():
    if not os.path.exists(STATE_FILE):
        return 1

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            number = int(f.read().strip())

        return number + 1

    except Exception:
        return 1


def create_narration(episode):
    number = episode["episode"]
    title = episode["title"]
    story = episode["story"]

    narration = (
        f"Ramayana, episode {number}. "
        f"{title}. "
        f"{story} "
        f"This was another important moment in the journey of Lord Rama."
    )

    # Clean extra spaces
    narration = re.sub(r"\s+", " ", narration).strip()

    return narration


def get_next_episode():

    episodes = load_episodes()

    episode_number = get_current_episode_number()

    # Restart from episode 1 after the final episode
    if episode_number > len(episodes):
        episode_number = 1

    episode = episodes[episode_number - 1]

    narration = create_narration(episode)

    return {
        "episode": episode["episode"],
        "title": episode["title"],
        "story": episode["story"],
        "narration": narration
    }


def save_episode_state(episode_number):

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(str(episode_number))


if __name__ == "__main__":

    episode = get_next_episode()

    print("=" * 60)
    print("RAMAYANA EPISODE")
    print("=" * 60)

    print("Episode:", episode["episode"])
    print("Title:", episode["title"])
    print()
    print(episode["narration"])
