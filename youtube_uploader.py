import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]


def get_youtube():

    client_id = os.environ.get(
        "YOUTUBE_CLIENT_ID"
    )

    client_secret = os.environ.get(
        "YOUTUBE_CLIENT_SECRET"
    )

    refresh_token = os.environ.get(
        "YOUTUBE_REFRESH_TOKEN"
    )

    if not client_id:
        raise RuntimeError(
            "YOUTUBE_CLIENT_ID is missing."
        )

    if not client_secret:
        raise RuntimeError(
            "YOUTUBE_CLIENT_SECRET is missing."
        )

    if not refresh_token:
        raise RuntimeError(
            "YOUTUBE_REFRESH_TOKEN is missing."
        )

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )

    return build(
        "youtube",
        "v3",
        credentials=credentials
    )


def upload_video(
    video_file,
    episode
):

    youtube = get_youtube()

    title = (
        f"{episode['title']} | "
        f"Ramayana Episode "
        f"{episode['episode']} #Shorts"
    )

    description = (
        f"Ramayana Episode "
        f"{episode['episode']}\n\n"

        f"{episode['title']}\n\n"

        f"{episode['story']}\n\n"

        "Follow the Ramayana journey "
        "through a new short story every day.\n\n"

        "#Ramayana #LordRama #Sita "
        "#RamayanaStories #IndianMythology #Shorts"
    )

    body = {

        "snippet": {

            "title": title[:100],

            "description": description,

            "tags": [
                "Ramayana",
                "Lord Rama",
                "Sita",
                "Ramayana Stories",
                "Indian Mythology",
                "Hindu Stories",
                "Lord Ram",
                "Indian Stories",
                "Shorts"
            ],

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

    print()
    print("=" * 60)
    print("STARTING YOUTUBE UPLOAD")
    print("=" * 60)

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
                "Upload:",
                int(status.progress() * 100),
                "%"
            )

    video_id = response["id"]

    url = (
        f"https://www.youtube.com/shorts/{video_id}"
    )

    print()
    print("=" * 60)
    print("YOUTUBE UPLOAD SUCCESSFUL")
    print("=" * 60)
    print("Video ID:", video_id)
    print("URL:", url)
    print("=" * 60)

    return url
