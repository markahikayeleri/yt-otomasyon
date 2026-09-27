"""SADECE BİR KEZ, KENDİ BİLGİSAYARINDA çalıştır. YouTube izni verip refresh token alırsın.
Kullanım: client_secret.json dosyasını bu klasöre koy, sonra:  python get_token.py"""
from google_auth_oauthlib.flow import InstalledAppFlow

from youtube import SCOPES

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
print("\nYT_CLIENT_ID     =", creds.client_id)
print("YT_CLIENT_SECRET =", creds.client_secret)
print("YT_REFRESH_TOKEN =", creds.refresh_token)
print("\nBu 3 değeri GitHub > Settings > Secrets > Actions kısmına ekle. Kimseyle paylaşma!")
