"""Episode selection + Gemini script writing.

Output of generate_script() is a dict:
  title, description, tags, comment_question, attire, location, teaser,
  scenes: [{speaker, text, characters, image_prompt, motion, sfx}]   (last scene = closing card)
"""
import json
import os
import re
import time

import characters as cast
import config

MOTIONS = ["zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down", "shake", "punch"]
SFX = ["whoosh", "bell", "drum", "crash", "sparkle", "none"]

HOOKS = [
    "open with a startling QUESTION that makes people need the answer (a mystery about this moment)",
    "open with the MOST DRAMATIC moment of the episode first (in the middle of the crisis), then tell how it came to that",
    "open with a bold, surprising FACT or contrast that most people do not know about this moment",
    "open with an EMOTIONAL line spoken by a character at the peak of the crisis",
]
ENDINGS = [
    "ask viewers one simple question about the episode so they comment, then say the next episode is coming",
    "ask viewers to comment 'जय श्री राम' if they felt this moment in their heart, then tease the next episode",
    "give a one-line lesson (dharma) from the episode, then tease the next episode and ask viewers to follow",
]


# ============================================================ files / state
def load_episodes():
    if not os.path.exists(config.EPISODES_FILE):
        raise RuntimeError(f"{config.EPISODES_FILE} was not found.")
    with open(config.EPISODES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("episodes", [])
    if not isinstance(data, list) or not data:
        raise RuntimeError(f"{config.EPISODES_FILE} must contain a non-empty list.")
    return data


def _atomic_write(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def save_episodes(episodes):
    _atomic_write(config.EPISODES_FILE, episodes)


def load_state():
    try:
        with open(config.STATE_FILE, encoding="utf-8") as f:
            return max(1, int(json.load(f).get("next_episode", 1)))
    except Exception:
        print("WARNING: episode_state.json missing/unreadable -> starting at episode 1")
        return 1


def save_state(next_episode):
    _atomic_write(config.STATE_FILE, {"next_episode": int(next_episode)})


def find_episode(episodes, number):
    for e in episodes:
        try:
            if int(e.get("episode")) == int(number):
                return e
        except (TypeError, ValueError):
            continue
    return None


# ============================================================ Gemini
def _client():
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing.")
    from google import genai
    return genai.Client(api_key=config.GEMINI_API_KEY)


_DEAD = set()          # models that are out of quota / retired during THIS run: never asked again
_STATE = {"fallback": False}


class GeminiUnavailable(RuntimeError):
    """Every writer (all Gemini models + the Cloudflare fallback) failed. Retrying the whole script would only waste quota."""


def _retry_seconds(msg, default=30):
    m = re.search(r"retry in ([\d.]+)\s*s", msg, re.I) or re.search(r"retryDelay\W+(\d+)", msg)
    return min(float(m.group(1)) + 2, 60) if m else default


def _extract_json(text):
    text = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except Exception:  # noqa: BLE001
        m = re.search(r"\{.*\}", text, re.S)           # model wrapped the JSON in chatter
        if not m:
            raise
        return json.loads(m.group(0))


def _ask_cloudflare(prompt, temperature):
    """Fallback writer: Cloudflare Workers AI text model (same token as the pictures)."""
    import requests
    if not (config.CF_ACCOUNT_ID and config.CF_API_TOKEN):
        raise RuntimeError("no Cloudflare credentials")
    print(f"   Fallback writer: Cloudflare {config.CF_TEXT_MODEL}")
    r = requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{config.CF_ACCOUNT_ID}/ai/run/{config.CF_TEXT_MODEL}",
        headers={"Authorization": f"Bearer {config.CF_API_TOKEN}"},
        json={"messages": [{"role": "system", "content": "You are a careful writer. Reply with ONE valid JSON object only, no other text."},
                           {"role": "user", "content": prompt}],
              "max_tokens": 4096, "temperature": min(temperature, 0.8)}, timeout=240)
    if r.status_code != 200:
        raise RuntimeError(f"Cloudflare text HTTP {r.status_code}: {r.text[:200]}")
    res = r.json().get("result") or {}
    text = res.get("response")
    if not text and res.get("choices"):
        text = res["choices"][0].get("message", {}).get("content")
    if not text:
        raise RuntimeError(f"Cloudflare text: empty result {str(res)[:150]}")
    return _extract_json(text)


def _ask_json(prompt, temperature=0.9):
    """Gemini with sensible quota handling:
       - daily quota used up (429 PerDay)      -> skip that model at once (no pointless retries)
       - per-minute limit (429)                -> wait the time Google asks, retry once
       - 503/500 overload                      -> short back-off, up to 3 tries
       - 404 / retired model                   -> next model
       then Cloudflare text model, then GeminiUnavailable."""
    from google.genai import types
    client = _client()
    last = None
    for model in config.GEMINI_MODELS:
        if model in _DEAD:
            continue
        tries = 0
        while tries < 3:
            tries += 1
            try:
                print(f"   Gemini {model} (try {tries}/3)")
                resp = client.models.generate_content(
                    model=model, contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json", temperature=temperature))
                text = (getattr(resp, "text", None) or "").strip()
                if not text:
                    raise ValueError("empty response")
                return _extract_json(text)
            except Exception as e:  # noqa: BLE001
                last, msg = e, str(e)
                print(f"   -> {type(e).__name__}: {msg[:260]}")
                low = msg.lower()
                if "429" in msg or "resource_exhausted" in low:
                    if "perday" in low.replace(" ", "").replace("_", "") or "per day" in low or "daily" in low:
                        print("   -> daily quota of this model is used up, trying the next model")
                        _DEAD.add(model)
                        break
                    if tries >= 2:
                        break
                    wait = _retry_seconds(msg)
                    print(f"   -> per-minute limit, waiting {wait:.0f}s")
                    time.sleep(wait)
                elif any(k in msg for k in ("503", "500", "502", "504", "UNAVAILABLE", "INTERNAL", "DEADLINE")) or "timed out" in low:
                    time.sleep(5 * 2 ** (tries - 1))
                elif isinstance(e, (ValueError, json.JSONDecodeError)):
                    time.sleep(2)                        # bad/empty JSON: one more go, same model
                else:
                    _DEAD.add(model)
                    break                                # 404 retired model, 400, 403 ... -> next model
    print("   All Gemini models unavailable -> trying the Cloudflare text model")
    try:
        out = _ask_cloudflare(prompt, temperature)
        _STATE["fallback"] = True
        return out
    except Exception as e:  # noqa: BLE001
        raise GeminiUnavailable(
            "No writer is available right now. Gemini: quota used up or overloaded (daily quota resets at about 12:30 PM IST); "
            f"Cloudflare fallback: {str(e)[:160]}. Last Gemini error: {str(last)[:200]}") from e


# ============================================================ prompts
def _script_prompt(ep, prev_title, next_title, notes=""):
    n = config.NUM_SCENES
    hook = HOOKS[int(ep["episode"]) % len(HOOKS)]
    ending = ENDINGS[int(ep["episode"]) % len(ENDINGS)]
    keys = ", ".join(cast.CAST_KEYS)
    teaser = f'Next episode: "{next_title}".' if next_title else "This is the latest episode; just say the story continues soon."
    return f"""You are the head writer of a hugely popular MARATHI YouTube Shorts channel that retells the Valmiki Ramayana as a gripping, emotional, cinematic daily series. Viewers swipe away in 2 seconds unless the first line grabs them, so every second must earn attention.

EPISODE {ep['episode']}: {ep['title']}
FACTS (source of truth, do not contradict): {ep['story']}
Previous episode: {prev_title or 'none (this is the start of the series)'}
{teaser}

Write ONE script of EXACTLY {n} scenes (about 45 seconds when spoken).

STRUCTURE
- Scene 1 = HOOK, 6-12 words, speaker "narrator" or a lively character (never a king or sage). {hook}. Never start with a greeting, a title or "आजच्या भागात".
- Scenes 2 to {n-1}: the story as a chain of vivid moments. Each scene = one new picture and ONE idea. Escalate emotion and curiosity; hold a surprise for the second half.
- At least 4 scenes must be DIRECT SPEECH in a character's own words (first person, short and powerful), spoken by at least 2 DIFFERENT characters, and by a woman wherever the story has one (Sita, Kaikeyi, Kaushalya, Mandodari ...). Every line must really be said by the character in the "speaker" field, so the right man or woman voice is used. The rest are the narrator.
- Scene {n} = CLOSING CARD, 14-20 words: {ending}. It must mention the next episode. Its speaker is "narrator". Do not describe any picture for it.

LANGUAGE RULES for the spoken "text"
- Only Marathi in Devanagari. Natural, simple, spoken Marathi that an ordinary Maharashtrian viewer loves, warm and dramatic, not stiff or bookish.
- No English words, no digits (write numbers in words), no emoji, no brackets, no quotation marks. Use only these punctuation marks: , . ? ! (they create natural pauses for the voice).
- Spell names exactly: राम, सीता, लक्ष्मण, हनुमान, रावण, दशरथ, कैकेयी, कौसल्या, भरत, सुग्रीव, वाली, जटायू, विभीषण, कुंभकर्ण, इंद्रजित, मंदोदरी, शूर्पणखा, मारीच, शबरी, जनक, विश्वामित्र, अयोध्या, लंका.
- Each normal scene: 8-16 words. Total for all scenes: 90-130 words.

CONTENT RULES
- ACCURACY IS CRITICAL. Use the FACTS above. Add a detail from your own memory ONLY if you are 100% sure it is in the Valmiki Ramayana; otherwise leave it out. Never invent who appears, who says what, numbers, places or names. Never make a god appear personally unless the FACTS say so. Do not insult any person, community or religion. Tone: reverent, emotional, heroic.
- Never mention AI, Gemini, prompts, scripts or "episode summary".

PICTURES: for every scene except the last, give "image_prompt" in ENGLISH: ONE clear visual moment (action, emotion, camera angle such as close-up or wide shot, lighting). Do NOT describe faces or clothes of known characters, the computer adds that. No blood, gore, nudity or cruelty: show battles with glowing arrows, dust, fire and light. No text in the picture. Keep "location" the same visual world through the episode.
"characters": list of 1-2 keys from this list that are visible in that picture (the first one is the main subject): {keys}.
"speaker": "narrator" or exactly one key from the same list (the one who speaks the line).
"attire": for Rama, Sita and Lakshmana choose the outfit that fits THIS episode: "palace" (Ayodhya / Mithila / coronation), "forest" (exile, Panchavati, Kishkindha, Lanka captivity) or "war" (battle of Lanka).
"motion": one of {', '.join(MOTIONS)} (shake for crashes and fights, punch for shocks and the hook, pans for journeys, zoom_in for emotion).
"sfx": one of {', '.join(SFX)} (use none on about half of the scenes; bell for divine moments, drum for tension, crash for fights, whoosh for flying, sparkle for miracles).

TITLE: Marathi, 30-55 characters, curiosity hook first, ends with exactly one fitting emoji. Do not put the words episode or भाग in it.
{notes}
Return ONLY valid JSON of exactly this shape:
{{
  "title": "...",
  "description": "2-3 Marathi sentences for the YouTube description",
  "tags": ["10 to 12 short search tags, mixing Marathi and English, e.g. Ramayana, रामायण, Lord Rama"],
  "comment_question": "one simple Marathi question for viewers, max 12 words",
  "attire": "palace | forest | war",
  "location": "ENGLISH: one concrete visual setting that stays consistent through the episode",
  "scenes": [{{"speaker": "...", "text": "...", "characters": ["..."], "image_prompt": "...", "motion": "...", "sfx": "..."}}]
}}"""


def _director_prompt(ep, script):
    return f"""You are the director and final editor of a Marathi YouTube Shorts series on the Valmiki Ramayana. Improve the script below WITHOUT changing the number or order of scenes.

FACTS (source of truth): {ep['story']}

SCRIPT:
{json.dumps(script, ensure_ascii=False)}

Do all of this:
1. Scene 1 must be an irresistible hook within 2 seconds of speech. If it is weak, rewrite it.
2. Fix any factual mistake against the FACTS and the Valmiki Ramayana (remove any detail you are not sure about; no god may appear personally unless the FACTS say so); fix contradictions; make every scene follow from the previous one.
3. Make the Marathi natural, spoken, emotional and grammatically perfect. Keep speech lines short and punchy. Only Marathi Devanagari, no digits, no English, no emoji, only , . ? ! punctuation.
4. Each "image_prompt" (ENGLISH) must show EXACTLY what that line says at that moment, with the right "characters" visible. Keep it non-violent (no blood or gore). Do not describe faces or clothes of known characters.
5. Keep "speaker", "characters", "motion", "sfx" valid and unchanged unless a fix needs it. Title: 30-55 characters, hook first, one emoji at the end.
6. The last scene stays the closing card (14-20 words, mentions the next episode).

Return ONLY valid JSON with the same shape as the SCRIPT (title, description, tags, comment_question, attire, location, scenes)."""


# ============================================================ validation / cleanup
_DEV = re.compile(r"[\u0900-\u097F]")
_LAT = re.compile(r"[A-Za-z]")
_BAD = re.compile(r"\b(AI|Gemini|prompt|script)\b", re.I)


def _clean_text(text):
    text = str(text or "")
    text = re.sub(r"[\"“”‘’'`()\[\]{}*_#<>]", "", text)
    text = re.sub(r"[\U00010000-\U0010FFFF\u2600-\u27BF]", "", text)        # emoji
    text = text.replace("…", ".").replace("।", ".").replace("॥", ".")
    text = re.sub(r"\.{2,}", ".", text)
    return " ".join(text.split())


def normalize_script(script):
    """Fix small things instead of failing: aliases, invalid motion/sfx, speaker always visible."""
    attire = str(script.get("attire", "forest")).lower().strip()
    script["attire"] = attire if attire in ("palace", "forest", "war") else "forest"
    for i, sc in enumerate(script["scenes"]):
        sc["text"] = _clean_text(sc.get("text"))
        speaker = cast.normalize(sc.get("speaker"))
        sc["speaker"] = speaker or "narrator"
        chars = []
        for c in sc.get("characters") or []:
            k = cast.normalize(c)
            if k and k != "narrator" and k not in chars:
                chars.append(k)
        if sc["speaker"] != "narrator" and sc["speaker"] not in chars:
            chars.insert(0, sc["speaker"])
        sc["characters"] = chars[:2]
        sc["image_prompt"] = " ".join(str(sc.get("image_prompt") or "").split())
        sc["motion"] = sc.get("motion") if sc.get("motion") in MOTIONS else ["zoom_in", "pan_right", "zoom_out", "pan_left"][i % 4]
        sc["sfx"] = sc.get("sfx") if sc.get("sfx") in SFX else "none"
    first = script["scenes"][0]
    if cast.voice_profile(first["speaker"])[0] in ("elder", "villain"):
        first["speaker"] = "narrator"                      # slow/growly voices make a weak opening
    first["sfx"] = "none"                                  # clean start: voice only, no effect over the first word
    last = script["scenes"][-1]
    last["speaker"], last["characters"], last["motion"] = "narrator", [], "zoom_in"
    script["tags"] = [str(t).strip().lstrip("#") for t in (script.get("tags") or []) if str(t).strip()][:15]
    script["title"] = " ".join(str(script.get("title", "")).split())
    script["description"] = " ".join(str(script.get("description", "")).split())
    script["comment_question"] = " ".join(str(script.get("comment_question", "")).split())
    script["location"] = " ".join(str(script.get("location", "")).split())
    return script


def validate_script(script):
    """Returns a list of problems (empty = good)."""
    problems = []
    scenes = script.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != config.NUM_SCENES:
        return [f"need exactly {config.NUM_SCENES} scenes, got {len(scenes) if isinstance(scenes, list) else 'none'}"]
    if not _DEV.search(script.get("title", "")):
        problems.append("title must be Marathi (Devanagari)")
    total = 0
    for i, sc in enumerate(scenes, 1):
        t = sc.get("text", "")
        words = len(t.split())
        total += words
        letters_dev, letters_lat = len(_DEV.findall(t)), len(_LAT.findall(t))
        if words < 3:
            problems.append(f"scene {i}: text too short")
        if words > 24:
            problems.append(f"scene {i}: text too long ({words} words)")
        if letters_dev < 5 or letters_lat > 0.05 * max(letters_dev, 1):
            problems.append(f"scene {i}: must be Marathi Devanagari only")
        if _BAD.search(t):
            problems.append(f"scene {i}: mentions AI/prompt/script")
        if i < len(scenes) and len(sc.get("image_prompt", "")) < 15:
            problems.append(f"scene {i}: image_prompt missing")
    if not 70 <= total <= 150:
        problems.append(f"total spoken words {total} (need 90-130)")
    return problems


# ============================================================ public API
def generate_script(episode, previous, following):
    """Write + polish the script for one episode. Retries until it passes validation."""
    prev_title = previous.get("title") if previous else ""
    next_title = following.get("title") if following else ""
    notes, best, best_problems = "", None, None
    for attempt in range(1, 4):
        print(f"\nWriting script (attempt {attempt}/3) ...")
        try:
            script = _ask_json(_script_prompt(episode, prev_title, next_title, notes), 0.9)
            if not isinstance(script, dict) or "scenes" not in script:
                raise RuntimeError("Gemini JSON has no scenes")
            script = normalize_script(script)
            problems = validate_script(script)
            if not problems:
                try:
                    if not config.DIRECTOR_PASS:
                        raise RuntimeError("DIRECTOR_PASS=false")
                    if _STATE["fallback"]:
                        raise RuntimeError("fallback writer was used; not spending more requests")
                    print("Director pass (hook, facts, Marathi, picture match) ...")
                    fixed = normalize_script(_ask_json(_director_prompt(episode, script), 0.6))
                    if not validate_script(fixed):
                        script = fixed
                    else:
                        print("   director output failed validation -> keeping first draft")
                except Exception as e:  # noqa: BLE001
                    print("   director pass skipped:", str(e)[:150])   # the first draft is already valid
                script["teaser"] = next_title
                return script
            print("   problems:", "; ".join(problems))
            if best is None or len(problems) < len(best_problems):
                best, best_problems = script, problems
            notes = "\nFIX THESE PROBLEMS FROM YOUR LAST ATTEMPT: " + "; ".join(problems) + "\n"
        except GeminiUnavailable:
            raise                                          # quota/outage: retrying only burns more requests
        except Exception as e:  # noqa: BLE001
            print("   attempt failed:", str(e)[:200])
    # accept a near-miss only if the structure is sound (right scene count, Marathi title)
    if best is not None and not any(("exactly" in p or "title" in p or "Devanagari" in p or "AI/prompt" in p)
                                    for p in best_problems):
        print("Using best near-miss script. Remaining issues:", best_problems)
        best["teaser"] = next_title
        return best
    raise RuntimeError("Could not produce a valid script after 3 attempts.")


def _generate_new_episode(number, episodes):
    """Called only if the JSON runs out (after the coronation): continue with the next chronological event."""
    context = "\n".join(f"Episode {e['episode']}: {e['title']} - {e['story']}" for e in episodes[-5:])
    prompt = f"""You are an expert on the Valmiki Ramayana. We are making a chronological daily series.
Previous episodes:
{context}

Give Episode {number}: the NEXT event in the Ramayana (continue into the Uttara Kanda if the main story has ended). It must be a real event from the epic, not an invented one.
Return ONLY JSON: {{"title": "English title", "story": "English summary, 2-3 sentences"}}"""
    data = _ask_json(prompt, 0.4)
    ep = {"episode": number, "title": str(data["title"]).strip(), "story": str(data["story"]).strip()}
    episodes.append(ep)
    save_episodes(episodes)
    print(f"New episode {number} added to {config.EPISODES_FILE}: {ep['title']}")
    return ep


def get_next_episode():
    """Returns (episode, previous, following, number). Does NOT change the saved state."""
    episodes = load_episodes()
    if config.EPISODE_OVERRIDE:
        number = int(config.EPISODE_OVERRIDE)
        print(f"EPISODE_OVERRIDE -> episode {number} (state will not change)")
    else:
        number = load_state()
        if number > config.MAX_EPISODES:
            print(f"Series finished ({config.MAX_EPISODES} episodes) -> starting again from episode 1")
            number = 1
    episode = find_episode(episodes, number)
    if episode is None:
        if config.EPISODE_OVERRIDE:
            raise RuntimeError(f"Episode {number} does not exist.")
        print(f"Episode {number} not in {config.EPISODES_FILE} -> asking Gemini for the next event")
        episode = _generate_new_episode(number, episodes)
    return episode, find_episode(episodes, number - 1), find_episode(episodes, number + 1), number
