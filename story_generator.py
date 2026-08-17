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
# EPISODE STATE
# ============================================================

def load_state():

    if not os.path.exists(
        STATE_FILE
    ):

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


def save_state(
    next_episode
):

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
# GEMINI WITH RETRY + FALLBACK
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

        for attempt in range(
            1,
            4
        ):

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
                        f"Waiting "
                        f"{wait_seconds} seconds..."
                    )

                    time.sleep(
                        wait_seconds
                    )

                    continue

                raise RuntimeError(
                    f"Gemini API request failed: "
                    f"{error}"
                ) from error

        print()
        print(
            f"All retries failed for {model}."
        )

        print(
            "Trying fallback model..."
        )

    raise RuntimeError(
        "All Gemini models failed. "
        f"Last error: {last_error}"
    )


# ============================================================
# GENERATE FULL MARATHI STORY
# ============================================================

def generate_story(
    episode
):

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
तुम्ही रामायणातील कथा सांगणारे
एक उत्कृष्ट मराठी कथाकार आहात.

दररोज एका रामायणाच्या भागावर आधारित
YouTube Short तयार करायचा आहे.

आजची तारीख:
{today}

भाग क्रमांक:
{episode_number}

भागाचे शीर्षक:
{episode_title}

या भागाची संपूर्ण माहिती:
{source_story}


तुमचे काम:

वरील माहितीच्या आधारावर या भागाची
एक पूर्ण, सुंदर आणि भावनिक कथा तयार करा.


अत्यंत महत्त्वाचे नियम:

1. संपूर्ण कथा फक्त मराठी भाषेत लिहा.

2. कथा नैसर्गिक, शुद्ध आणि बोलण्यासाठी
   योग्य मराठीत असावी.

3. कथा केवळ सारांशासारखी वाटता कामा नये.

4. प्रेक्षकांना असे वाटले पाहिजे की त्यांनी
   त्या प्रसंगाची पूर्ण कथा ऐकली आहे.

5. कथेमध्ये स्पष्ट सुरुवात असावी.

6. त्यानंतर मुख्य घटना क्रमाने सांगावी.

7. कथेमध्ये मुख्य पात्रे आणि त्यांची भूमिका
   स्पष्ट असावी.

8. मुख्य घटना घडल्यानंतर त्याचा परिणाम
   किंवा भावनिक शेवट सांगावा.

9. कथा अचानक थांबवू नका.

10. या भागातील महत्त्वाची घटना वगळू नका.

11. दुसऱ्या रामायणाच्या भागातील घटना
    या कथेमध्ये मिसळू नका.

12. पुढील भागातील घटना आधीच सांगू नका.

13. रामायणातील पात्रांची नावे आणि
    नातेसंबंध चुकीचे लिहू नका.

14. स्वतःहून मोठ्या किंवा महत्त्वाच्या
    घटना निर्माण करू नका.

15. दिलेल्या स्रोताच्या विरोधात कोणतीही
    माहिती लिहू नका.

16. इंग्रजी शब्दांचा अनावश्यक वापर करू नका.

17. "AI", "Gemini", "script", "prompt",
    "source" किंवा automation यांचा
    उल्लेख करू नका.

18. कथा YouTube Shorts साठी आकर्षक असावी.

19. पहिल्या वाक्यात आकर्षक सुरुवात करा.

20. कथा ऐकताना भावनिक आणि चित्रमय
    अनुभव मिळाला पाहिजे.

21. शेवट नैसर्गिक असावा.

22. शेवटी पुढील भागाबद्दल उत्सुकता
    निर्माण करणारे एक छोटे वाक्य असू शकते,
    पण पुढील भागाची घटना सांगू नका.

23. कथा साधारण 75 ते 90 मराठी शब्दांची असावी.

24. केवळ शब्दसंख्या पूर्ण करण्यासाठी
    महत्त्वहीन वाक्ये जोडू नका.

25. कथा लहान करण्यासाठी मुख्य घटना
    घाईघाईने एकत्र करू नका.

26. शक्य तितकी पूर्ण आणि सलग कथा सांगा.

27. कथा फक्त दिलेल्या रामायणाच्या
    भागावर आधारित असावी.


कथेची रचना:

सुरुवात:
प्रसंग आणि परिस्थिती स्पष्ट करा.

मध्य:
मुख्य घटना नैसर्गिक क्रमाने सांगा.

शेवट:
मुख्य घटनेचा परिणाम आणि भावनिक
समारोप सांगा.


OUTPUT EXACTLY:

TITLE:
<मराठी YouTube Shorts शीर्षक>

STORY:
<पूर्ण मराठी कथा>


TITLE आणि STORY व्यतिरिक्त काहीही लिहू नका.
"""


    print()
    print("=" * 60)
    print("GEMINI MARATHI STORY GENERATION")
    print("=" * 60)

    print(
        "Episode:",
        episode_number
    )

    print(
        "Episode:",
        episode_title
    )

    print(
        "Language: Marathi"
    )

    print(
        "Story type: Full mini-story"
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
    # PARSE TITLE + STORY
    # ========================================================

    title = ""

    story_lines = []

    collecting_story = False

    for line in text.splitlines():

        clean = line.strip()

        if not clean:

            continue

        upper = clean.upper()

        if (
            upper.startswith("TITLE:")
            or
            upper.startswith("TITLE :")
        ):

            title = clean.split(
                ":",
                1
            )[1].strip()

            collecting_story = False

            continue


        if (
            upper.startswith("STORY:")
            or
            upper.startswith("STORY :")
        ):

            first_part = clean.split(
                ":",
                1
            )[1].strip()

            if first_part:

                story_lines.append(
                    first_part
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

    story = " ".join(
        story.split()
    )

    title = " ".join(
        title.split()
    )


    # ========================================================
    # FALLBACK
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
            "Could not extract story "
            "from Gemini response."
        )


    # ========================================================
    # CLEAN STORY
    # ========================================================

    if (
        story.startswith('"')
        and
        story.endswith('"')
    ):

        story = story[
            1:-1
        ].strip()


    if (
        story.startswith("'")
        and
        story.endswith("'")
    ):

        story = story[
            1:-1
        ].strip()


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
    print("MARATHI STORY GENERATED")
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

    print(
        story
    )

    print("=" * 60)


    if word_count < 60:

        print(
            "WARNING: Story may be too short."
        )


    if word_count > 110:

        print(
            "WARNING: Story may be too long "
            "for a 30-second narration."
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
            "No episodes found."
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
    # restart from first episode.

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
                "No valid episode numbers found."
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
    print("FINAL MARATHI STORY")
    print("=" * 60)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )

    print("=" * 60)
