"""ORKESTRATÖR (beyin): Her gün bir kez çalışır, ajanlara sırayla görev verir ve raporlar."""
import json
import os
import traceback
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import yaml

import agents
import media
from llm import USAGE
from report import Report

HIST = "data/history.json"


def publish_time(hhmm, tz, day_offset=0):
    now = datetime.now(ZoneInfo(tz))
    h, m = map(int, hhmm.split(":"))
    t = now.replace(hour=h, minute=m, second=0, microsecond=0) + timedelta(days=day_offset)
    if t < now + timedelta(minutes=30):
        t += timedelta(days=1)
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"), t.strftime("%d.%m %H:%M")


def main():
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    history = json.load(open(HIST, encoding="utf-8"))
    rep = Report()
    today = datetime.now(ZoneInfo(cfg["timezone"])).strftime("%d.%m.%Y")
    rep.add(f"📊 {cfg['channel_name']} — Günlük Rapor ({today})")
    if cfg["dry_run"]:
        rep.add("🧪 TEST MODU: videolar üretildi, YouTube'a yüklenmedi.")
    os.makedirs("output", exist_ok=True)

    try:
        # 1) Konu + kaynak (kaynak bulunamazsa 3 kez yeni konu dener)
        source = None
        for _ in range(3):
            topic = agents.pick_topic(cfg, history)
            source = agents.research(cfg, topic["wiki_queries"])
            if source:
                break
        if not source:
            raise RuntimeError("3 denemede de güvenilir kaynak bulunamadı.")
        rep.add(f"🧭 Konu: {topic['topic']}\n📚 Kaynak: {source['url']}")

        # 2) Senaryo + denetim (1 düzeltme hakkı)
        script = agents.write_script(cfg, topic, source)
        check = agents.review(cfg, script, source)
        if not check.get("approved"):
            script = agents.revise(cfg, script, source, check.get("issues", []))
            check = agents.review(cfg, script, source)
        rep.add(f"✅ Denetim puanı: {check.get('score')}")
        if not check.get("approved"):
            rep.add("⛔ Video denetimden geçemedi, yayınlanmadı. Sorunlar:\n- " + "\n- ".join(check.get("issues", [])))
            return

        # 3) Sahneler + uzun video + kapak
        words_per_image = max(10, int(cfg["seconds_per_image"] * 2.3))
        sections = agents.design_scenes(cfg, script["sections"], words_per_image)
        long_path = media.render(sections, cfg, cfg["long_size"], "output/long", "output/long.mp4")
        thumb = media.thumbnail(sections[0]["images"][0], script["thumbnail_text"], "output/thumb.jpg")
        rep.add(f"🎬 Uzun video hazır: {media.duration(long_path) / 60:.1f} dk")

        # 4) Shorts
        shorts = agents.make_shorts(cfg, script, source)
        short_paths = []
        for i, sh in enumerate(shorts):
            p = media.render([sh], cfg, cfg["short_size"], f"output/short{i}", f"output/short{i}.mp4")
            short_paths.append(p)
        rep.add(f"📱 {len(short_paths)} Shorts hazır")

        # 5) Yayın
        entry = {"date": today, "topic": topic["topic"], "long_id": None, "short_ids": []}
        credit = f"\n\nKaynak: {source['url']} (CC BY-SA)\nGörseller ve seslendirme yapay zekâ ile üretilmiştir."
        if not cfg["dry_run"]:
            import youtube
            iso, human = publish_time(cfg["long_publish_time"], cfg["timezone"])
            desc = script["description"] + credit
            vid = youtube.upload(long_path, script["title"], desc, script["tags"], iso, cfg, thumb)
            entry["long_id"] = vid
            rep.add(f"🚀 Uzun video → {human}\nhttps://youtu.be/{vid}")
            for sh, p, t in zip(shorts, short_paths, cfg["short_publish_times"]):
                iso, human = publish_time(t, cfg["timezone"], day_offset=1)  # uzun video yayındayken
                d = f"Hikâyenin tamamı: https://youtu.be/{vid}\n#shorts" + credit
                sid = youtube.upload(p, sh["title"] + " #shorts", d, script["tags"][:5], iso, cfg)
                entry["short_ids"].append(sid)
                rep.add(f"🚀 Short → {human}\nhttps://youtu.be/{sid}")
        history.append(entry)

        # 6) Son videoların performansı
        if not cfg["dry_run"]:
            ids = [h["long_id"] for h in history[-8:-1] if h.get("long_id")]
            for s in youtube.stats(ids).values():
                rep.add(f"📈 {s['title'][:40]} → 👁 {s.get('viewCount', 0)} 👍 {s.get('likeCount', 0)}")

    except Exception as e:
        rep.add(f"❌ Hata: {e}\n{traceback.format_exc()[-1500:]}")
    finally:
        cost = USAGE["input"] / 1e6 * cfg["price_input_per_mtok"] + USAGE["output"] / 1e6 * cfg["price_output_per_mtok"]
        rep.add(f"💰 Yapay zekâ: {USAGE['calls']} çağrı, tahmini ${cost:.3f}")
        json.dump(history, open(HIST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        rep.send()


if __name__ == "__main__":
    main()
