from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError


def get_gmail_service(access_token: str):
    creds = Credentials(
        token=access_token,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"]
    )
    return build("gmail", "v1", credentials=creds)


def fetch_latest_emails(access_token: str, max_results: int = 5):
    try:
        service = get_gmail_service(access_token)

        results = service.users().messages().list(
            userId="me",
            maxResults=max_results
        ).execute()

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            msg_data = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["From", "Subject"]
            ).execute()

            headers = msg_data.get("payload", {}).get("headers", [])
            email = {h["name"]: h["value"] for h in headers}
            emails.append(email)

        return emails

    except HttpError as e:
        # Google API error (most likely)
        raise RuntimeError(f"Gmail API error: {e}")

    except Exception as e:
        # Anything else
        raise RuntimeError(f"Unexpected Gmail error: {e}")
