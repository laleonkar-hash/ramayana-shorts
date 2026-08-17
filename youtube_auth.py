import json
import os

from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]


def main():

    client_secret_file = "client_secret.json"

    if not os.path.exists(client_secret_file):

        print()
        print(
            "ERROR: client_secret.json was not found."
        )

        print(
            "Download your OAuth client JSON "
            "from Google Cloud and rename it "
            "to client_secret.json."
        )

        return

    flow = InstalledAppFlow.from_client_secrets_file(
        client_secret_file,
        SCOPES
    )

    credentials = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent"
    )

    print()
    print("=" * 60)
    print("AUTHENTICATION SUCCESSFUL")
    print("=" * 60)
    print()

    print("CLIENT ID:")
    print(credentials.client_id)

    print()
    print("CLIENT SECRET:")
    print(credentials.client_secret)

    print()
    print("REFRESH TOKEN:")
    print(credentials.refresh_token)

    print()
    print("=" * 60)
    print(
        "SAVE THESE THREE VALUES AS GITHUB SECRETS."
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
