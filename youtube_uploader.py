import os
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

import config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _service():
    for name in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"):
        if not getattr(config, name):
            raise RuntimeError(f"{name} is missing.")
    creds = Credentials(None, refresh_token=config.YOUTUBE_REFRESH_TOKEN,
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=config.YOUTUBE_CLIENT_ID, client_secret=config.YOUTUBE_CLIENT_SECRET, scopes=SCOPES)
    return build("youtube", "v3", credentials=creds)


def make_metadata(script, episode_number):
    suffix = f" | रामायण भाग {episode_number} #Shorts"
    title = script["title"][: 100 - len(suffix)].rstrip() + suffix
    parts = []
    if script.get("comment_question"):
        parts.append(script["comment_question"])
    parts.append(script["description"])
    if script.get("teaser"):
        parts.append(f"पुढील भाग: {script['teaser']}")
    parts.append("रोज दोन नवीन रामायण कथा शॉर्ट्स. चॅनेल सबस्क्राईब करा आणि जय श्री राम लिहा! 🙏")
    parts.append(config.CHANNEL_HASHTAGS)
    parts.append("या व्हिडिओमधील चित्रे आणि आवाज AI च्या मदतीने तयार केले आहेत.")
    tags, total = [], 0
    for t in script.get("tags", []) + ["Ramayana", "रामायण", "Marathi", "मराठी", "Shorts", "Lord Rama"]:
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
                    "defaultLanguage": "mr", "defaultAudioLanguage": "mr"},
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
