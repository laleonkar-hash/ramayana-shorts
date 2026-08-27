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
# LOAD & SAVE EPISODES
# ============================================================

def load_episodes():
    if not os.path.exists(EPISODES_FILE):
        raise RuntimeError(f"{EPISODES_FILE} was not found.")

    with open(EPISODES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict) and "episodes" in data and isinstance(data["episodes"], list):
        return data["episodes"]

    raise RuntimeError("ramayana_episodes.json must contain a list or an 'episodes' list.")


def save_episodes(episodes):
    """Saves updated episode list back to ramayana_episodes.json"""
    with open(EPISODES_FILE, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)


# ============================================================
# EPISODE HELPERS
# ============================================================

def get_episode_number(item):
    for key in ["episode", "episode_number", "number", "id"]:
        if key in item:
            try:
                return int(item[key])
            except (ValueError, TypeError):
                continue
    raise RuntimeError("No valid episode number found.")


def get_episode_title(item):
    for key in ["title", "name", "episode_title"]:
        if key in item:
            value = str(item[key]).strip()
            if value:
                return value
    return "Ramayana Story"


def get_episode_source(item):
    for key in ["story", "description", "summary", "content"]:
        if key in item:
            value = str(item[key]).strip()
            if value:
                return value
    raise RuntimeError("No story/description/summary/content found for episode.")


# ============================================================
# EPISODE STATE
# ============================================================

def load_state():
    if not os.path.exists(STATE_FILE):
        return 1

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        return max(1, int(state.get("next_episode", 1)))
    except Exception:
        print("WARNING: episode_state.json could not be read. Defaulting to 1.")
        return 1


def save_state(next_episode):
    state = {"next_episode": int(next_episode)}
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# ============================================================
# FIND EPISODE
# ============================================================

def find_episode(episodes, episode_number):
    for item in episodes:
        try:
            if get_episode_number(item) == episode_number:
                return item
        except Exception:
            continue
    return None


# ============================================================
# GEMINI CLIENT & API CALL
# ============================================================

def create_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")
    return genai.Client(api_key=api_key)


def generate_with_fallback(client, prompt):
    last_error = None

    for model in MODELS:
        print("\n" + "=" * 60)
        print(f"TRYING GEMINI MODEL: {model}")
        print("=" * 60)

        for attempt in range(1, 4):
            try:
                print(f"Attempt {attempt}/3")
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                if response is None:
                    raise RuntimeError("Gemini returned no response.")

                text = getattr(response, "text", None)
                if text and text.strip():
                    print(f"SUCCESS: {model}")
                    return response

                raise RuntimeError("Gemini returned an empty response.")

            except Exception as error:
                last_error = error
                error_text = str(error)
                print(f"\n{model} attempt {attempt} failed: {error_text}")

                temporary_error = any(err in error_text for err in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "500", "502", "504"])

                if temporary_error:
                    wait_seconds = 5 * attempt
                    print(f"Waiting {wait_seconds} seconds...")
                    time.sleep(wait_seconds)
                    continue

                raise RuntimeError(f"Gemini API request failed: {error}") from error

        print(f"\nAll retries failed for {model}. Trying fallback model...")

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")


# ============================================================
# AUTO-GENERATE NEW EPISODE OUTLINE WHEN FILE RUNS OUT
# ============================================================

def generate_new_episode_data(episode_number, previous_episodes):
    """Generates next Ramayana episode title and summary when JSON runs out."""
    client = create_gemini_client()
    
    last_5_episodes = previous_episodes[-5:]
    summary_context = "\n".join([f"Episode {get_episode_number(e)}: {get_episode_title(e)} - {get_episode_source(e)}" for e in last_5_episodes])

    prompt = f"""
You are an expert on the epic Ramayana.
We are creating a daily chronological episode series.

Previous Episodes Context:
{summary_context}

Generate Episode Number: {episode_number}

What is the NEXT logical chronological event/story in the Ramayana directly following the context above?

Respond strictly in JSON format with two keys:
"title": "<English title for Episode {episode_number}>",
"story": "<English brief summary of this episode's event (2-3 sentences)>"

Do NOT output Markdown formatting or backticks, return raw JSON string only.
"""
    print(f"\nGenerating new Ramayana episode outline for Episode {episode_number}...")
    response = generate_with_fallback(client, prompt)
    clean_json = response.text.strip().replace("```json", "").replace("```", "").strip()
    
    parsed = json.loads(clean_json)
    
    new_episode = {
        "episode": episode_number,
        "title": parsed["title"],
        "story": parsed["story"]
    }
    
    # Append and save to file
    previous_episodes.append(new_episode)
    save_episodes(previous_episodes)
    print(f"New Episode {episode_number} added and saved to {EPISODES_FILE}!")
    
    return new_episode


# ============================================================
# GENERATE FULL MARATHI STORY
# ============================================================

def generate_story(episode):
    client = create_gemini_client()
    episode_number = get_episode_number(episode)
    episode_title = get_episode_title(episode)
    source_story = get_episode_source(episode)

    today = datetime.utcnow().strftime("%Y-%m-%d")

    prompt = f"""
तुम्ही रामायणातील कथा सांगणारे एक उत्कृष्ट मराठी कथाकार आहात.
दररोज एका रामायणाच्या भागावर आधारित YouTube Short तयार करायचा आहे.

आजची तारीख: {today}
भाग क्रमांक: {episode_number}
भागाचे शीर्षक: {episode_title}
या भागाची संपूर्ण माहिती: {source_story}

तुमचे काम: वरील माहितीच्या आधारावर या भागाची एक पूर्ण, सुंदर आणि भावनिक कथा तयार करा.

अत्यंत महत्त्वाचे नियम:
1. संपूर्ण कथा फक्त मराठी भाषेत लिहा.
2. कथा नैसर्गिक, शुद्ध आणि बोलण्यासाठी योग्य मराठीत असावी.
3. कथा केवळ सारांशासारखी वाटता कामा नये.
4. कथा साधारण 75 ते 90 मराठी शब्दांची असावी.
5. "AI", "Gemini", "script", "prompt", "source" यांचा उल्लेख करू नका.

OUTPUT EXACTLY:
TITLE:
<मराठी YouTube Shorts शीर्षक>

STORY:
<पूर्ण मराठी कथा>
"""

    print("\n" + "=" * 60)
    print("GEMINI MARATHI STORY GENERATION")
    print(f"Episode: {episode_number} - {episode_title}")
    print("=" * 60)

    response = generate_with_fallback(client, prompt)
    text = response.text.strip()

    title = ""
    story_lines = []
    collecting_story = False

    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        upper = clean.upper()

        if upper.startswith("TITLE:") or upper.startswith("TITLE :"):
            title = clean.split(":", 1)[1].strip()
            collecting_story = False
            continue

        if upper.startswith("STORY:") or upper.startswith("STORY :"):
            first_part = clean.split(":", 1)[1].strip()
            if first_part:
                story_lines.append(first_part)
            collecting_story = True
            continue

        if collecting_story:
            story_lines.append(clean)

    story = " ".join(" ".join(story_lines).split())
    title = " ".join(title.split()) or episode_title

    if not story:
        raise RuntimeError("Could not extract story from Gemini response.")

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
        raise RuntimeError("No episodes found.")

    next_number = load_state()

    print("\n" + "=" * 60)
    print(f"SELECTING NEXT RAMAYANA EPISODE: {next_number}")
    print("=" * 60)

    episode = find_episode(episodes, next_number)

    # Automatically generate episode if missing from JSON
    if episode is None:
        print(f"Episode {next_number} not found in {EPISODES_FILE}. Generating automatically...")
        episode = generate_new_episode_data(next_number, episodes)

    selected_number = get_episode_number(episode)

    # Save state for the NEXT run
    save_state(selected_number + 1)

    return generate_story(episode)


# ============================================================
# MAIN EXECUTION
# ============================================================

if __name__ == "__main__":
    result = get_next_episode()

    print("\n" + "=" * 60)
    print("FINAL MARATHI STORY")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 60)
