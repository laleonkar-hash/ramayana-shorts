import json
import os
from datetime import datetime

from google import genai


# ============================================================
# FILE SETTINGS
# ============================================================

EPISODES_FILE = "ramayana_episodes.json"
STATE_FILE = "episode_state.json"

# Gemini model
MODEL = "gemini-3.6-flash"


# ============================================================
# LOAD RAMAYANA EPISODES
# ============================================================

def load_episodes():

    if not os.path.exists(EPISODES_FILE):

        raise RuntimeError(
            f"{EPISODES_FILE} was not found."
        )

    with open(
        EPISODES_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    # Format:
    #
    # [
    #   {...},
    #   {...}
    # ]

    if isinstance(data, list):

        return data

    # Format:
    #
    # {
    #   "episodes": [
    #       {...},
    #       {...}
    #   ]
    # }

    if isinstance(data, dict):

        if "episodes" in data:

            episodes = data["episodes"]

            if isinstance(episodes, list):

                return episodes

    raise RuntimeError(
        "ramayana_episodes.json must contain either "
        "a list of episodes or an object containing "
        "an 'episodes' list."
    )


# ============================================================
# GET EPISODE NUMBER
# ============================================================

def get_episode_number(item):

    possible_keys = [
        "episode",
        "episode_number",
        "number",
        "id"
    ]

    for key in possible_keys:

        if key in item:

            try:

                return int(item[key])

            except (
                ValueError,
                TypeError
            ):

                pass

    raise RuntimeError(
        "Could not find a valid episode number "
        "in ramayana_episodes.json."
    )


# ============================================================
# GET EPISODE TITLE
# ============================================================

def get_episode_title(item):

    possible_keys = [
        "title",
        "name",
        "episode_title"
    ]

    for key in possible_keys:

        if key in item:

            value = str(
                item[key]
            ).strip()

            if value:

                return value

    return "Ramayana Story"


# ============================================================
# GET SOURCE STORY
# ============================================================

def get_episode_source(item):

    possible_keys = [
        "story",
        "description",
        "summary",
        "content"
    ]

    for key in possible_keys:

        if key in item:

            value = str(
                item[key]
            ).strip()

            if value:

                return value

    raise RuntimeError(
        "Could not find story/description/summary/content "
        "for the selected Ramayana episode."
    )


# ============================================================
# LOAD CURRENT EPISODE STATE
# ============================================================

def load_state():

    # If state file doesn't exist,
    # start with Episode 1.

    if not os.path.exists(STATE_FILE):

        return 1

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            state = json.load(f)

        next_episode = int(
            state.get(
                "next_episode",
                1
            )
        )

        if next_episode < 1:

            return 1

        return next_episode

    except Exception:

        print(
            "WARNING: Could not read episode_state.json."
        )

        print(
            "Starting from Episode 1."
        )

        return 1


# ============================================================
# SAVE NEXT EPISODE
# ============================================================

def save_state(next_episode):

    state = {
        "next_episode": int(
            next_episode
        )
    }

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            state,
            f,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# FIND EPISODE
# ============================================================

def find_episode(
    episodes,
    episode_number
):

    for item in episodes:

        try:

            number = get_episode_number(
                item
            )

            if number == episode_number:

                return item

        except Exception:

            continue

    return None


# ============================================================
# CREATE GEMINI CLIENT
# ============================================================

def create_gemini_client():

    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Add GEMINI_API_KEY to GitHub Actions Secrets."
        )

    return genai.Client(
        api_key=api_key
    )


# ============================================================
# GENERATE UNIQUE RAMAYANA STORY
# ============================================================

def generate_story(episode):

    client = create_gemini_client()

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
You are an expert storyteller specializing
in the Ramayana.

You are creating ONE daily YouTube Short
for a Ramayana storytelling channel.

TODAY'S DATE:
{today}

EPISODE NUMBER:
{episode_number}

EPISODE TITLE:
{episode_title}

SOURCE INFORMATION FOR THIS EPISODE:
{source_story}


YOUR TASK:

Create a unique and engaging narration for
a YouTube Short based ONLY on the supplied
episode information.


VERY IMPORTANT STORY RULES:

1. Stay faithful to the supplied Ramayana source.

2. Do NOT invent major events.

3. Do NOT invent characters.

4. Do NOT change relationships between characters.

5. Do NOT combine this episode with another
   Ramayana episode.

6. Do NOT introduce events that happen later
   in the Ramayana.

7. Do NOT contradict the supplied source.

8. Use simple, natural English.

9. Make the first sentence interesting enough
   to catch attention immediately.

10. The narration MUST contain approximately
    55–65 words.

11. The narration should normally fit into
    approximately 25–30 seconds when spoken.

12. Write it as natural spoken narration,
    not as an article.

13. Do NOT use bullet points.

14. Do NOT use numbered points.

15. Do NOT use emojis.

16. Do NOT use quotation marks around the
    entire narration.

17. Do NOT use headings inside the story.

18. Do NOT mention AI, Gemini, prompts,
    scripts, or automation.

19. Do NOT say "according to the source".

20. End with a short curiosity or continuation
    feeling that encourages viewers to watch
    the next episode.

21. Keep the story respectful and suitable
    for a general YouTube audience.

22. The story must be different in wording
    from a simple copy of the source text.

23. Do not add a moral lesson unless it is
    naturally part of the supplied episode.


OUTPUT FORMAT:

Return EXACTLY these two sections:

TITLE:
A short engaging YouTube Shorts title

STORY:
The complete 55–65 word narration


Do not return anything before TITLE.
Do not return anything after the STORY.
"""

    print()
    print("=" * 60)
    print("ASKING GEMINI TO CREATE UNIQUE RAMAYANA STORY")
    print("=" * 60)

    print(
        "Model:",
        MODEL
    )

    print(
        "Episode:",
        episode_number
    )

    print(
        "Episode title:",
        episode_title
    )

    print("=" * 60)

    try:

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

    except Exception as error:

        raise RuntimeError(
            f"Gemini API request failed: {error}"
        ) from error

    if response is None:

        raise RuntimeError(
            "Gemini returned no response."
        )

    text = getattr(
        response,
        "text",
        None
    )

    if not text:

        raise RuntimeError(
            "Gemini returned an empty response."
        )

    text = text.strip()

    print()
    print("=" * 60)
    print("RAW GEMINI RESPONSE")
    print("=" * 60)

    print(text)

    print("=" * 60)


    # ========================================================
    # PARSE TITLE AND STORY
    # ========================================================

    title = ""
    story = ""

    lines = text.splitlines()

    collecting_story = False

    story_lines = []

    for line in lines:

        clean = line.strip()

        if not clean:

            if collecting_story:

                story_lines.append(" ")

            continue

        upper = clean.upper()

        if upper.startswith("TITLE:"):

            title = clean.split(
                ":",
                1
            )[1].strip()

            collecting_story = False

            continue

        if upper.startswith("STORY:"):

            first_story_part = clean.split(
                ":",
                1
            )[1].strip()

            if first_story_part:

                story_lines.append(
                    first_story_part
                )

            collecting_story = True

            continue

        if collecting_story:

            story_lines.append(
                clean
            )


    story = " ".join(
        story_lines
    )

    # Clean multiple spaces.

    story = " ".join(
        story.split()
    )

    title = " ".join(
        title.split()
    )


    # ========================================================
    # FALLBACK PARSING
    # ========================================================

    # If Gemini didn't follow the format perfectly,
    # try to recover the content.

    if not title:

        title = episode_title

    if not story:

        # Try finding STORY in the raw response.

        upper_text = text.upper()

        story_position = upper_text.find(
            "STORY:"
        )

        if story_position != -1:

            story = text[
                story_position + len("STORY:")
            :].strip()

            story = " ".join(
                story.split()
            )


    if not story:

        raise RuntimeError(
            "Could not extract STORY from Gemini response."
        )


    # ========================================================
    # CLEAN GEMINI OUTPUT
    # ========================================================

    story = story.strip()

    # Remove accidental wrapping quotes.

    if (
        story.startswith('"')
        and story.endswith('"')
    ):

        story = story[1:-1].strip()

    if (
        story.startswith("'")
        and story.endswith("'")
    ):

        story = story[1:-1].strip()


    # Remove accidental "STORY:" if Gemini
    # repeated it.

    if story.upper().startswith(
        "STORY:"
    ):

        story = story.split(
            ":",
            1
        )[1].strip()


    # ========================================================
    # WORD COUNT
    # ========================================================

    word_count = len(
        story.split()
    )

    print()
    print("=" * 60)
    print("GEMINI STORY GENERATED")
    print("=" * 60)

    print(
        "Title:",
        title
    )

    print(
        "Word count:",
        word_count
    )

    print()
    print(story)

    print("=" * 60)


    # We don't hard-fail if Gemini returns
    # slightly outside the requested range.
    #
    # video_creator.py will still control
    # the final audio/video duration.

    if word_count < 45:

        print(
            "WARNING: Gemini generated a very short story."
        )

    if word_count > 75:

        print(
            "WARNING: Gemini generated a longer story."
        )


    return {
        "episode": episode_number,
        "source_title": episode_title,
        "title": title,
        "story": story
    }


# ============================================================
# GET NEXT EPISODE AND GENERATE STORY
# ============================================================

def get_next_episode():

    episodes = load_episodes()

    if not episodes:

        raise RuntimeError(
            "ramayana_episodes.json contains no episodes."
        )

    next_number = load_state()

    print()
    print("=" * 60)
    print("SELECTING NEXT RAMAYANA EPISODE")
    print("=" * 60)

    print(
        "Next episode from state:",
        next_number
    )

    episode = find_episode(
        episodes,
        next_number
    )

    # If the requested episode doesn't exist,
    # restart from the first available episode.

    if episode is None:

        print(
            f"Episode {next_number} was not found."
        )

        print(
            "Restarting from the first episode."
        )

        valid_numbers = []

        for item in episodes:

            try:

                valid_numbers.append(
                    get_episode_number(item)
                )

            except Exception:

                pass

        if not valid_numbers:

            raise RuntimeError(
                "No valid episode numbers found "
                "in ramayana_episodes.json."
            )

        first_episode_number = min(
            valid_numbers
        )

        episode = find_episode(
            episodes,
            first_episode_number
        )

    if episode is None:

        raise RuntimeError(
            "Could not select a Ramayana episode."
        )


    selected_number = get_episode_number(
        episode
    )

    selected_title = get_episode_title(
        episode
    )

    print()
    print(
        "Selected episode:"
    )

    print(
        selected_number,
        "-",
        selected_title
    )

    print("=" * 60)


    # Generate the unique Gemini narration.

    generated_story = generate_story(
        episode
    )

    return generated_story


# ============================================================
# TEST MODE
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("RAMAYANA STORY GENERATOR TEST")
    print("=" * 60)

    result = get_next_episode()

    print()
    print("=" * 60)
    print("FINAL STORY OBJECT")
    print("=" * 60)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )

    print("=" * 60)
