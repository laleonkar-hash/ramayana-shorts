import json
import os
import time
from datetime import datetime

from google import genai


# ============================================================
# CONFIGURATION
# ============================================================

EPISODES_FILE = "ramayana_episodes.json"
STATE_FILE = "episode_state.json"

# Primary + fallback models.
#
# If one model temporarily returns 503,
# the program retries and then moves to the next model.

MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
]


# ============================================================
# LOAD EPISODES
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

    if isinstance(data, list):

        return data

    if isinstance(data, dict):

        if "episodes" in data:

            if isinstance(
                data["episodes"],
                list
            ):

                return data["episodes"]

    raise RuntimeError(
        "ramayana_episodes.json must contain "
        "a list or an 'episodes' list."
    )


# ============================================================
# EPISODE HELPERS
# ============================================================

def get_episode_number(item):

    for key in [
        "episode",
        "episode_number",
        "number",
        "id"
    ]:

        if key in item:

            try:

                return int(
                    item[key]
                )

            except (
                ValueError,
                TypeError
            ):

                continue

    raise RuntimeError(
        "No valid episode number found."
    )


def get_episode_title(item):

    for key in [
        "title",
        "name",
        "episode_title"
    ]:

        if key in item:

            value = str(
                item[key]
            ).strip()

            if value:

                return value

    return "Ramayana Story"


def get_episode_source(item):

    for key in [
        "story",
        "description",
        "summary",
        "content"
    ]:

        if key in item:

            value = str(
                item[key]
            ).strip()

            if value:

                return value

    raise RuntimeError(
        "No story/description/summary/content "
        "found for episode."
    )


# ============================================================
# STATE
# ============================================================

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

        return max(
            1,
            int(
                state.get(
                    "next_episode",
                    1
                )
            )
        )

    except Exception:

        print(
            "WARNING: episode_state.json "
            "could not be read."
        )

        return 1


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

            if (
                get_episode_number(item)
                ==
                episode_number
            ):

                return item

        except Exception:

            continue

    return None


# ============================================================
# GEMINI CLIENT
# ============================================================

def create_gemini_client():

    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "GEMINI_API_KEY is missing."
        )

    return genai.Client(
        api_key=api_key
    )


# ============================================================
# GEMINI REQUEST WITH RETRIES + FALLBACKS
# ============================================================

def generate_with_fallback(
    client,
    prompt
):

    last_error = None

    for model in MODELS:

        print()
        print("=" * 60)
        print(
            f"TRYING GEMINI MODEL: {model}"
        )
        print("=" * 60)

        # Three attempts per model.
        for attempt in range(1, 4):

            try:

                print(
                    f"Attempt {attempt}/3"
                )

                response = (
                    client.models.generate_content(
                        model=model,
                        contents=prompt
                    )
                )

                if response is None:

                    raise RuntimeError(
                        "Gemini returned no response."
                    )

                text = getattr(
                    response,
                    "text",
                    None
                )

                if text and text.strip():

                    print()
                    print(
                        f"SUCCESS: {model}"
                    )

                    return response

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            except Exception as error:

                last_error = error

                error_text = str(
                    error
                )

                print()
                print(
                    f"{model} attempt "
                    f"{attempt} failed:"
                )

                print(
                    error_text
                )

                temporary_error = (
                    "503" in error_text
                    or
                    "UNAVAILABLE" in error_text
                    or
                    "429" in error_text
                    or
                    "RESOURCE_EXHAUSTED" in error_text
                    or
                    "500" in error_text
                    or
                    "502" in error_text
                    or
                    "504" in error_text
                )

                if temporary_error:

                    wait_seconds = (
                        5 * attempt
                    )

                    print(
                        f"Temporary error."
                    )

                    print(
                        f"Waiting "
                        f"{wait_seconds} seconds..."
                    )

                    time.sleep(
                        wait_seconds
                    )

                    continue

                # Authentication, invalid API key,
                # invalid model, etc.
                #
                # These should not be endlessly retried.
                raise RuntimeError(
                    f"Gemini API request failed: "
                    f"{error}"
                ) from error

        print()
        print(
            f"All retries failed for {model}."
        )

        print(
            "Moving to fallback model..."
        )

    raise RuntimeError(
        "All Gemini models failed. "
        f"Last error: {last_error}"
    )


# ============================================================
# GENERATE STORY
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

You are creating one daily YouTube Short.

TODAY:
{today}

EPISODE NUMBER:
{episode_number}

EPISODE TITLE:
{episode_title}

SOURCE INFORMATION:
{source_story}


TASK:

Create a UNIQUE narration for a
25–30 second YouTube Short.


STRICT RULES:

1. Stay faithful to the supplied Ramayana source.

2. Do not invent major events.

3. Do not invent characters.

4. Do not change character relationships.

5. Do not combine this episode with another episode.

6. Do not introduce events that belong to later episodes.

7. Do not contradict the supplied source.

8. Use simple natural English.

9. Make the first sentence an interesting hook.

10. The STORY should contain approximately
    55–65 words.

11. Make it sound natural when spoken aloud.

12. Do not use bullet points.

13. Do not use numbered points.

14. Do not use emojis.

15. Do not mention AI, Gemini, automation,
    scripts or prompts.

16. Do not write "according to the source".

17. Do not put headings inside STORY.

18. Keep the story respectful.

19. Make the wording fresh and engaging.
    Do not simply copy the source text.

20. End with a small curiosity or continuation
    feeling.

21. The story must remain focused on THIS episode.

22. Do not add unrelated mythology.


RETURN EXACTLY:

TITLE:
<short engaging title>

STORY:
<55–65 word narration>
"""

    print()
    print("=" * 60)
    print("ASKING GEMINI TO CREATE STORY")
    print("=" * 60)

    print(
        "Episode:",
        episode_number
    )

    print(
        "Title:",
        episode_title
    )

    print("=" * 60)

    response = generate_with_fallback(
        client,
        prompt
    )

    text = response.text.strip()

    if not text:

        raise RuntimeError(
            "Gemini returned an empty story."
        )

    print()
    print("=" * 60)
    print("RAW GEMINI RESPONSE")
    print("=" * 60)

    print(text)

    print("=" * 60)

    # ========================================================
    # PARSE RESPONSE
    # ========================================================

    title = ""
    story_lines = []

    collecting_story = False

    for line in text.splitlines():

        clean = line.strip()

        if not clean:

            continue

        upper = clean.upper()

        if upper.startswith("TITLE:"):

            title = clean.split(
                ":",
                1
            )[1].strip()

            collecting_story = False

        elif upper.startswith("STORY:"):

            first_part = clean.split(
                ":",
                1
            )[1].strip()

            if first_part:

                story_lines.append(
                    first_part
                )

            collecting_story = True

        elif collecting_story:

            story_lines.append(
                clean
            )

    story = " ".join(
        story_lines
    )

    story = " ".join(
        story.split()
    )

    title = " ".join(
        title.split()
    )

    # ========================================================
    # FALLBACK PARSING
    # ========================================================

    if not title:

        title = episode_title

    if not story:

        upper_text = text.upper()

        position = upper_text.find(
            "STORY:"
        )

        if position != -1:

            story = text[
                position + len("STORY:")
            :].strip()

            story = " ".join(
                story.split()
            )

    if not story:

        raise RuntimeError(
            "Could not extract story from Gemini."
        )

    # Remove accidental wrapping quotes.

    if (
        story.startswith('"')
        and
        story.endswith('"')
    ):

        story = story[1:-1].strip()

    if (
        story.startswith("'")
        and
        story.endswith("'")
    ):

        story = story[1:-1].strip()

    # Remove accidental repeated STORY prefix.

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

    if word_count < 45:

        print(
            "WARNING: Story is shorter than expected."
        )

    if word_count > 75:

        print(
            "WARNING: Story is longer than expected."
        )

    return {
        "episode": episode_number,
        "source_title": episode_title,
        "title": title,
        "story": story
    }


# ============================================================
# SELECT NEXT EPISODE
# ============================================================

def get_next_episode():

    episodes = load_episodes()

    if not episodes:

        raise RuntimeError(
            "No episodes found in "
            "ramayana_episodes.json."
        )

    next_number = load_state()

    print()
    print("=" * 60)
    print("SELECTING NEXT RAMAYANA EPISODE")
    print("=" * 60)

    print(
        "Next episode:",
        next_number
    )

    episode = find_episode(
        episodes,
        next_number
    )

    # If episode doesn't exist,
    # restart from the first episode.

    if episode is None:

        print(
            f"Episode {next_number} "
            "was not found."
        )

        valid_numbers = []

        for item in episodes:

            try:

                valid_numbers.append(
                    get_episode_number(item)
                )

            except Exception:

                continue

        if not valid_numbers:

            raise RuntimeError(
                "No valid episode numbers "
                "found."
            )

        first_number = min(
            valid_numbers
        )

        episode = find_episode(
            episodes,
            first_number
        )

    if episode is None:

        raise RuntimeError(
            "Could not select episode."
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

    # Generate unique Gemini story.

    return generate_story(
        episode
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    result = get_next_episode()

    print()
    print("=" * 60)
    print("FINAL STORY")
    print("=" * 60)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )

    print("=" * 60)
