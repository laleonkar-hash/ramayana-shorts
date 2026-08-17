import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]


def get_youtube_service():

    refresh_token = os.environ.get(
        "YOUTUBE_REFRESH_TOKEN"
    )

    client_id = os.environ.get(
        "YOUTUBE_CLIENT_ID"
    )

    client_secret = os.environ.get(
        "YOUTUBE_CLIENT_SECRET"
    )

    if not refresh_token:
        raise RuntimeError(
            "YOUTUBE_REFRESH_TOKEN is missing"
        )

    if not client_id:
        raise RuntimeError(
            "YOUTUBE_CLIENT_ID is missing"
        )

    if not client_secret:
        raise RuntimeError(
            "YOUTUBE_CLIENT_SECRET is missing"
        )

    credentials = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials
    )

    return youtube


def upload_video(video_file, episode):

    youtube = get_youtube_service()

    title = (
        f"{episode['title']} | "
        f"Ramayana Episode {episode['episode']} #Shorts"
    )

    description = (
        f"Ramayana Episode {episode['episode']}\n\n"
        f"{episode['title']}\n\n"
        f"Discover the timeless story of the Ramayana "
        f"through a short daily episode.\n\n"
        f"Subscribe for the next episode.\n\n"
        f"#Ramayana #LordRama #Sita #HinduStories "
        f"#IndianMythology #Shorts"
    )

    tags = [
        "Ramayana",
        "Lord Rama",
        "Sita",
        "Hindu Stories",
        "Indian Mythology",
        "Ramayana Stories",
        "Indian Stories",
        "Shorts"
    ]

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "22"
        },

        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        video_file,
        mimetype="video/mp4",
        resumable=True
    )

    print("Starting YouTube upload...")

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None

    while response is None:

        status, response = request.next_chunk()

        if status:
            print(
                f"Upload progress: "
                f"{int(status.progress() * 100)}%"
            )

    video_id = response["id"]

    url = (
        f"https://www.youtube.com/shorts/{video_id}"
    )

    print()
    print("=" * 60)
    print("YOUTUBE UPLOAD SUCCESSFUL")
    print("=" * 60)
    print(url)
    print("=" * 60)

    return url
