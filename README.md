# 🎬 Tam Otomatik YouTube Kanalı — "Marka Hikâyeleri"

Her gün kendiliğinden: **konu bulur → Wikipedia'dan araştırır → senaryo yazar → doğruluk denetler → sahnelere çevirir → görsel + seslendirme üretir → 1 uzun video + 2 Shorts hazırlar → en aktif saatlere zamanlar → Telegram'dan rapor atar.**

Aylık tahmini maliyet: yapay zekâ (Claude Haiku) birkaç dolar, gerisi ücretsiz (GitHub Actions, Pollinations görsel, Edge-TTS ses).

## Ekip (ajanlar)

| # | Ajan | Dosya | Görev |
|---|------|-------|-------|
| 0 | Orkestratör (beyin) | `main.py` | Herkese sırayla iş verir, hata yönetir |
| 1 | Konu Seçici | `agents.py` | Tekrar etmeyen, merak uyandıran konu |
| 2 | Araştırmacı | `agents.py` | Wikipedia'dan kaynak metin (TR, yoksa EN) |
| 3 | Senarist | `agents.py` | ~10 dk'lık hikâye anlatımı |
| 4 | Denetçi | `agents.py` | Bilgi doğruluğu + YouTube politikası (80 puan altı yayınlanmaz) |
| 5 | Sahne Tasarımcısı | `agents.py` | Her ~9 saniyeye bir görsel prompt'u |
| 6 | Shorts Üreticisi | `agents.py` | En çarpıcı anlardan 2 Shorts |
| 7 | Prodüksiyon | `media.py` | Görsel, ses, yakınlaşma efekti, müzik, kapak |
| 8 | Yayıncı | `youtube.py` | Zamanlanmış yükleme |
| 9 | Raporcu | `report.py` | Telegram günlük rapor |

## Kurulum (bir kez, ~1 saat)

### 1. GitHub
1. github.com'da hesap aç, **public** yeni repo oluştur (public repoda Actions dakikaları sınırsız ücretsiz; şifreler Secrets'ta gizli kalır).
2. Bu klasördeki tüm dosyaları repoya yükle (`.github` klasörü dahil).

### 2. Claude API anahtarı
console.anthropic.com → API Keys → anahtar oluştur → 5 $ kredi yükle.

### 3. YouTube izni
1. console.cloud.google.com → yeni proje → **YouTube Data API v3**'ü etkinleştir.
2. **OAuth consent screen** → External → kendi e-postanı test kullanıcısı ekle → sonra **"Publish app / Uygulamayı yayınla"** de. (Test modunda kalırsa izin 7 günde bir düşer!)
3. **Credentials → Create OAuth client ID → Desktop app** → JSON'u indir, adını `client_secret.json` yap.
4. Kendi bilgisayarında: `pip install -r requirements.txt` → `python get_token.py` → tarayıcıda kanal hesabınla izin ver. Ekrana 3 değer çıkar.
5. ⚠️ **Önemli:** Google, denetlenmemiş API projelerinden yüklenen videoları **gizli (private)** tutar. "YouTube API Services Audit and Quota Extension Form" ile denetime başvur. Onay gelene kadar videolar yüklenir ama herkese açılmaz.
6. YouTube Studio'da kanalını **telefonla doğrula** (özel kapak ve 15 dk üstü video için).

### 4. Telegram raporu
1. Telegram'da **@BotFather** → `/newbot` → token al.
2. Botuna bir mesaj at, sonra tarayıcıda aç: `https://api.telegram.org/bot<TOKEN>/getUpdates` → `"chat":{"id":...}` sayısı senin chat ID'n.

### 5. Şifreleri ekle
Repo → Settings → Secrets and variables → Actions → New secret:
`ANTHROPIC_API_KEY`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

### 6. Müzik (isteğe bağlı ama önerilir)
YouTube Studio → Ses Kitaplığı → "Atıf gerekmez" filtresi → 5-10 sakin belgesel müziği indir → `assets/music/` klasörüne `.mp3` olarak koy. **Başka yerden müzik koyma, telif yersin.**

### 7. Test
1. `config.yaml` içinde `dry_run: true` kalsın.
2. Repo → Actions → **gunluk-video** → **Run workflow**.
3. Bitince aynı sayfadaki **videolar** dosyasını indirip izle, Telegram raporuna bak.
4. Beğendiysen `dry_run: false` yap. Artık her sabah 06:00'da kendiliğinden çalışır.

## Ayarlar (`config.yaml`)
- Yayın saatleri: uzun video 20:00, Shorts ertesi gün 12:30 ve 18:00. Kanal oturunca YouTube Studio → Analiz → "İzleyicilerin YouTube'da olduğu zamanlar" kartına göre güncelle.
- **Başka dilde kanal:** `language`, `language_name`, `wikipedia_langs`, `voice` değerlerini değiştir (ör. `en`, `English`, `["en"]`, `en-US-GuyNeural`), ayrı bir repo ve ayrı YouTube izniyle kur.

## Sınırlar ve bilinen riskler
- Günlük API kotası 10.000 birim; bu kurulum ~5.000 kullanır (günde 3 video).
- Pollinations ücretsiz servistir. Çökerse o sahne koyu düz renk olur, video yine tamamlanır; rapora bak.
- YouTube'un "seri üretilmiş içerik" politikası nedeniyle birbirine benzeyen videolar para kazanamaz. Denetçi ve konu çeşitliliği bunu azaltır, ama arada videoları izlemen kanal sağlığı için iyi olur.
- GitHub, 60 gün hiç aktivite olmayan repolarda zamanlanmış görevleri durdurabilir; günlük kayıt commit'leri bunu genelde önler.
