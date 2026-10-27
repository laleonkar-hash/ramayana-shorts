import os
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

import config
import lang
from collections import Counter

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _service(scopes=None):
    for name in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"):
        if not getattr(config, name):
            raise RuntimeError(f"{name} is missing.")
    creds = Credentials(None, refresh_token=config.YOUTUBE_REFRESH_TOKEN,
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=config.YOUTUBE_CLIENT_ID, client_secret=config.YOUTUBE_CLIENT_SECRET,
                        scopes=scopes or SCOPES)
    return build("youtube", "v3", credentials=creds)


CHAR_TAGS = {   # characters that appear in the episode -> the hashtags people actually search
    "sita": "#MataSita", "lakshmana": "#Laxman", "hanuman": "#Hanuman #BajrangBali", "ravana": "#Ravan",
    "bharata": "#Bharat", "dasharatha": "#Dashrath", "vishwamitra": "#Vishwamitra", "sugriva": "#Sugriv",
    "vali": "#Vali", "jatayu": "#Jatayu", "vibhishana": "#Vibhishan", "kumbhakarna": "#Kumbhkaran",
    "indrajit": "#Meghnad", "mandodari": "#Mandodari", "kaikeyi": "#Kaikeyi", "kaushalya": "#Kaushalya",
    "shabari": "#Shabari", "angad": "#Angad", "jambavan": "#Jambavan", "janaka": "#Janak",
    "surpanakha": "#Surpanakha", "maricha": "#Maricha", "guha": "#Nishadraj", "tara": "#Tara",
}


def build_hashtags(script):
    """Channel hashtags + up to 3 character hashtags of THIS episode. Max 13 (YouTube ignores ALL hashtags above 15).
    The first three are shown above the title, so they are the strongest ones."""
    tags = list(lang.pack()["hashtags"])
    counts = Counter()
    for sc in script.get("scenes", []):
        for c in sc.get("characters", []) or []:
            counts[c] += 1
        if sc.get("speaker") not in (None, "", "narrator"):
            counts[sc["speaker"]] += 1
    extra = []
    for key, _ in counts.most_common():
        if key in CHAR_TAGS:
            extra += CHAR_TAGS[key].split()
        if len(extra) >= 3:
            break
    for t in extra:
        if t not in tags:
            tags.append(t)
    return tags[:13]


def make_metadata(script, episode_number):
    pk = lang.pack()
    suffix = pk["title_suffix"].format(n=episode_number)
    title = script["title"][: 100 - len(suffix)].rstrip() + suffix
    parts = []
    if script.get("comment_question"):
        parts.append(script["comment_question"])
    parts.append(script["description"])
    parts.append(pk["seo_line"].format(n=episode_number))
    if script.get("teaser"):
        parts.append(pk["next_label"] + " " + script["teaser"])
    parts.append(pk["cta"])
    parts.append(" ".join(build_hashtags(script)))
    parts.append(pk["ai_note"])
    wanted = list(script.get("tags", [])) + pk["tags"] + [f"Ramayan episode {episode_number}", f"रामायण भाग {episode_number}"]
    tags, total = [], 0
    for t in wanted:
        if t not in tags and total + len(t) + 1 < 450:
            tags.append(t)
            total += len(t) + 1
    return title, "\n\n".join(parts)[:4900], tags


def upload_video(video_path, script, episode_number, thumb_path=None):
    if not os.path.exists(video_path):
        raise RuntimeError(f"Video file not found: {video_path}")
    yt = _service()
    title, description, tags = make_metadata(script, episode_number)
    body = {
        "snippet": {"title": title, "description": description, "tags": tags, "categoryId": config.CATEGORY_ID,
                    "defaultLanguage": lang.pack()["code"], "defaultAudioLanguage": lang.pack()["code"]},
        "status": {"privacyStatus": config.PRIVACY, "selfDeclaredMadeForKids": config.MADE_FOR_KIDS,
                   "containsSyntheticMedia": True, "embeddable": True, "publicStatsViewable": True},
    }
    media = MediaFileUpload(video_path, mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    print("Uploading:", title)
    resp, fails = None, 0
    while resp is None:
        try:
            status, resp = req.next_chunk()
            if status:
                print(f"   upload {int(status.progress() * 100)}%")
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and fails < 5:
                fails += 1
                time.sleep(5 * fails)
                continue
            raise
    vid = resp["id"]
    applied = resp.get("status", {}).get("privacyStatus", "unknown")
    print(f"Uploaded: https://www.youtube.com/shorts/{vid}  (privacy applied: {applied})")
    if applied != config.PRIVACY:
        print("WARNING: YouTube did not apply the requested privacy. API projects that have not passed Google's audit "
              "are forced to private. Make the video public in YouTube Studio or request the audit.")
    if thumb_path and os.path.exists(thumb_path):
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(thumb_path)).execute()
        except Exception as e:  # noqa: BLE001
            print("Thumbnail not set (not required for Shorts):", str(e)[:120])
    return vid


def post_first_comment(video_id, script):
    """The channel's own first comment (the episode question) to start a real conversation.
    Needs the extra 'youtube.force-ssl' permission; if your token does not have it this just prints a note and
    the upload is NOT affected."""
    q = (script.get("comment_question") or "").strip()
    if not q:
        return
    text = f"{q} 👇\nजय श्री राम 🙏"
    try:
        yt = _service(["https://www.googleapis.com/auth/youtube.force-ssl"])
        yt.commentThreads().insert(part="snippet", body={"snippet": {"videoId": video_id, "topLevelComment": {
            "snippet": {"textOriginal": text}}}}).execute()
        print("First comment posted.")
    except Exception as e:  # noqa: BLE001
        print("First comment skipped (token lacks comment permission - see README, optional):", str(e)[:140])
