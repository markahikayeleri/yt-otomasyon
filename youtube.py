"""AJAN 8: Yayıncı. Videoyu en aktif saate zamanlanmış şekilde yükler."""
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly"]


def _service():
    creds = Credentials(
        None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload(path, title, description, tags, publish_at, cfg, thumb=None):
    yt = _service()
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:4900],
            "tags": tags[:15],
            "categoryId": cfg["category_id"],
            "defaultLanguage": cfg["language"],
            "defaultAudioLanguage": cfg["language"],
        },
        "status": {
            "privacyStatus": "private",          # publishAt için zorunlu
            "publishAt": publish_at,             # ISO 8601, UTC
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": cfg["ai_disclosure"],
        },
    }
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(path, chunksize=-1, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    vid = resp["id"]
    if thumb:
        try:  # özel kapak için kanalın telefonla doğrulanmış olması gerekir
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(thumb)).execute()
        except Exception as e:
            print("Kapak yüklenemedi:", e)
    return vid


def stats(video_ids):
    if not video_ids:
        return {}
    yt = _service()
    res = yt.videos().list(part="statistics,snippet", id=",".join(video_ids[:50])).execute()
    return {i["id"]: {"title": i["snippet"]["title"], **i["statistics"]} for i in res.get("items", [])}
