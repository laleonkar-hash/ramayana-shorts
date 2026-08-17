import json
import os
from datetime import datetime

from google import genai


EPISODES_FILE = "ramayana_episodes.json"
STATE_FILE = "episode_state.json"

MODEL = "gemini-3.6-flash"


def load_episodes():

    with open(
        EPISODES_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        if "episodes" in data:
            return data["episodes"]

    raise RuntimeError(
        "ramayana_episodes.json must contain a list "
        "or an object with an 'episodes' list."
    )


def get_episode_number(item):

    for key in [
        "episode",
        "episode_number",
        "number",
        "id"
    ]:

        if key in item:
            return int(item[key])

    raise RuntimeError(
        "Episode number missing from ramayana_episodes.json"
    )


def get_episode_title(item):

    for key in [
        "title",
        "name",
        "episode_title"
    ]:

        if key in item:
            return str(item[key])

    return "Ramayana Story"


def get_episode_source(item):

    for key in [
        "story",
        "description",
        "summary",
        "content"
    ]:

        if key in item:
            return str(item[key])

    raise RuntimeError(
        "Story/description missing from ramayana_episodes.json"
    )


def load_state():

    if not os.path.exists(STATE_FILE):

        return 1

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            state = json.load(f)

        return int(
            state.get("next_episode", 1)
        )

    except Exception:

        return 1


def save_state(next_episode):

    state = {
        "next_episode": next_episode
    }

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            state,
            f,
            indent=2
        )


def find_episode(episodes, episode_number):

    for item in episodes:

        number = get_episode_number(item)

        if number == episode_number:
            return item

    return None


def generate_story(episode):

    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "GEMINI_API_KEY GitHub Secret is missing."
        )

    client = genai.Client(
        api_key=api_key
    )

    episode_number = get_episode_number(
        episode
    )

    episode_title = get_episode_title(
        episode
    )

    source_story = get_episode_source(
        episode
    )

    today = datetime.utcnow().strftime(
        "%Y-%m-%d"
    )

    prompt = f"""
You are an expert Ramayana storyteller creating
a daily YouTube Shorts series.

TODAY:
{today}

EPISODE NUMBER:
{episode_number}

EPISODE TITLE:
{episode_title}

SOURCE INFORMATION:
{source_story}

Create a UNIQUE narration for a 25–30 second
YouTube Short.

STRICT RULES:

1. Stay faithful to the supplied Ramayana source.
2. Do not invent major events.
3. Do not invent characters.
4. Do not change relationships between characters.
5. Do not mix events from another episode.
6. Use simple, natural English.
7. Make it interesting from the first sentence.
8. Target approximately 70–80 spoken words.
9. The narration should sound natural when spoken aloud.
10. Do not use emojis.
11. Do not use bullet points.
12. Do not use headings inside the narration.
13. Do not mention that AI created the story.
14. End with a small curiosity/continuation line.
15. Keep the story suitable for a general YouTube audience.

Return EXACTLY in this format:

TITLE:
<short engaging title>

STORY:
<the complete 25–30 second narration>
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    text = response.text.strip()

    if not text:

        raise RuntimeError(
            "Gemini returned an empty response."
        )

    title = ""
    story = ""

    lines = text.splitlines()

    collecting_story = False

    for line in lines:

        clean = line.strip()

        if clean.upper().startswith("TITLE:"):

            title = clean.split(
                ":", 1
            )[1].strip()

            collecting_story = False

        elif clean.upper().startswith("STORY:"):

            story = clean.split(
                ":", 1
            )[1].strip()

            collecting_story = True

        elif collecting_story:

            story += " " + clean

    title = title.strip()
    story = story.strip()

    if not title:
        title = episode_title

    if not story:

        raise RuntimeError(
            "Gemini response did not contain STORY."
        )

    # Remove accidental quotes.
    story = story.strip('"').strip()

    return {
        "episode": episode_number,
        "source_title": episode_title,
        "title": title,
        "story": story
    }


def get_next_episode():

    episodes = load_episodes()

    next_number = load_state()

    episode = find_episode(
        episodes,
        next_number
    )

    # If we reached the end, restart at episode 1.
    if episode is None:

        next_number = 1

        episode = find_episode(
            episodes,
            next_number
        )

    if episode is None:

        raise RuntimeError(
            "No matching episode found."
        )

    print()
    print("=" * 60)
    print("SELECTED RAMAYANA EPISODE")
    print("=" * 60)

    print(
        "Episode:",
        get_episode_number(episode)
    )

    print(
        "Source title:",
        get_episode_title(episode)
    )

    print("=" * 60)

    generated = generate_story(
        episode
    )

    print()
    print("=" * 60)
    print("GEMINI GENERATED STORY")
    print("=" * 60)

    print(
        "Title:",
        generated["title"]
    )

    print()
    print(
        generated["story"]
    )

    print("=" * 60)

    return generated


if __name__ == "__main__":

    result = get_next_episode()

    print(result)
