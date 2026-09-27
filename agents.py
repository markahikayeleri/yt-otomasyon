"""Ekipteki ajanlar. Her biri tek bir işten sorumlu, orkestratör (main.py) onları sırayla yönetir."""
import json
import math

import requests

from llm import ask

UA = {"User-Agent": "yt-otomasyon/1.0 (egitim amacli kanal)"}


# ---------- AJAN 1: Trend / Konu Seçici ----------
def pick_topic(cfg, history):
    done = [h["topic"] for h in history][-300:]
    system = (
        "You are a YouTube content strategist for a faceless educational channel. "
        f"Channel niche: {cfg['niche']} Audience language: {cfg['language_name']}."
    )
    user = f"""Pick ONE video topic with strong curiosity and high watch-time potential for this audience.
Rules:
- It must be a real, well documented story (a Wikipedia article must exist about it).
- Do NOT repeat or closely resemble these already produced topics: {json.dumps(done, ensure_ascii=False)}
- Vary the type: founding stories, collapses, rivalries, famous mistakes, economic concepts.
Return ONLY JSON:
{{"topic": "short topic in {cfg['language_name']}",
  "wiki_queries": ["best Wikipedia search term", "alternative term"],
  "angle": "the hook / surprising angle of the story in one sentence"}}"""
    return ask(cfg["model"], system, user, 600, as_json=True)


# ---------- AJAN 2: Araştırmacı (Wikipedia, ücretsiz) ----------
def research(cfg, queries):
    for lang in cfg["wikipedia_langs"]:
        api = f"https://{lang}.wikipedia.org/w/api.php"
        for q in queries:
            try:
                s = requests.get(api, headers=UA, timeout=30, params={
                    "action": "query", "list": "search", "srsearch": q, "format": "json", "srlimit": 1}).json()
                hits = s["query"]["search"]
                if not hits:
                    continue
                title = hits[0]["title"]
                p = requests.get(api, headers=UA, timeout=30, params={
                    "action": "query", "prop": "extracts", "explaintext": 1, "titles": title,
                    "format": "json", "redirects": 1}).json()
                text = next(iter(p["query"]["pages"].values())).get("extract", "")
                if len(text) > 3000:
                    url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
                    return {"title": title, "url": url, "text": text[:18000]}
            except Exception:
                continue
    return None


# ---------- AJAN 3: Senarist ----------
def write_script(cfg, topic, source):
    system = (
        f"You are an award-winning documentary scriptwriter writing in {cfg['language_name']}. "
        "You write gripping, accurate narration for YouTube. You only use facts from the given source."
    )
    user = f"""Topic: {topic['topic']}
Angle: {topic['angle']}
SOURCE (only use facts from here, never invent numbers, dates or quotes):
\"\"\"{source['text']}\"\"\"

Write a ~{cfg['long_video_words']} word narration in {cfg['language_name']}.
- First 2 sentences = a strong hook that creates curiosity (no "hello, welcome").
- Tell it as a story with tension, turning points and a clear lesson at the end.
- Short spoken sentences. No investment advice. Do not insult real people.
- End with a one-sentence call to subscribe that feels natural.
- Split into 8-12 sections.
Return ONLY JSON:
{{"title": "clickable but honest title, max 70 chars",
  "description": "3-4 sentence video description",
  "tags": ["10-15 tags"],
  "thumbnail_text": "2-4 punchy words",
  "sections": [{{"narration": "..."}}]}}"""
    return ask(cfg["model"], system, user, 8000, as_json=True)


# ---------- AJAN 4: Doğruluk ve Politika Denetçisi ----------
def review(cfg, script, source):
    system = "You are a strict fact-checker and YouTube policy reviewer."
    narration = "\n".join(s["narration"] for s in script["sections"])
    user = f"""SOURCE:
\"\"\"{source['text']}\"\"\"

SCRIPT TITLE: {script['title']}
SCRIPT:
\"\"\"{narration}\"\"\"

Check: 1) every number, date, name and claim is supported by the source,
2) no investment advice, no defamation, no hate, no misleading clickbait title,
3) the script is original storytelling (not copied sentences from the source).
Return ONLY JSON: {{"approved": true/false, "score": 0-100, "issues": ["specific issue", ...]}}
Approve only if score >= 80 and there are no factual errors."""
    return ask(cfg["model"], system, user, 1500, as_json=True)


def revise(cfg, script, source, issues):
    system = f"You fix documentary scripts in {cfg['language_name']} using only the given source."
    user = f"""SOURCE:
\"\"\"{source['text']}\"\"\"
SCRIPT JSON:
{json.dumps(script, ensure_ascii=False)}
Fix these issues and keep the same JSON structure and length: {json.dumps(issues, ensure_ascii=False)}
Return ONLY the corrected JSON."""
    return ask(cfg["model"], system, user, 8000, as_json=True)


# ---------- AJAN 5: Sahne / Prompt Tasarımcısı ----------
def design_scenes(cfg, sections, words_per_image):
    counts = [max(1, math.ceil(len(s["narration"].split()) / words_per_image)) for s in sections]
    system = "You are an art director turning narration into image-generation prompts."
    user = f"""For each section, write exactly the given number of English image prompts that visually
tell that part of the story. Keep characters and era visually consistent across prompts.
Never include real logos, trademarks, text or the faces of real, identifiable people
(show them from behind, in silhouette, or as generic figures).
Sections: {json.dumps([{"narration": s["narration"], "count": c} for s, c in zip(sections, counts)], ensure_ascii=False)}
Return ONLY JSON: {{"scenes": [["prompt", ...], ...]}}  (one inner list per section)"""
    res = ask(cfg["model"], system, user, 8000, as_json=True)
    scenes = res["scenes"]
    for i, s in enumerate(sections):  # eksik prompt olursa güvenli doldur
        p = scenes[i] if i < len(scenes) and scenes[i] else [s["narration"][:200]]
        s["images"] = [f"{x}, {cfg['image_style']}" for x in p]
    return sections


# ---------- AJAN 6: Shorts Üreticisi ----------
def make_shorts(cfg, script, source):
    n = cfg["shorts_per_day"]
    system = f"You create viral YouTube Shorts scripts in {cfg['language_name']} from longer documentaries."
    user = f"""Long video title: {script['title']}
Long script: {json.dumps([s['narration'] for s in script['sections']], ensure_ascii=False)}
Create {n} different Shorts (each 110-140 words, 45-55 seconds), each focused on one surprising moment.
- Line 1 is a scroll-stopping hook. Facts must come from the long script only.
- Last sentence invites viewers to watch the full story on the channel.
Return ONLY JSON: {{"shorts": [{{"title": "max 60 chars", "narration": "...", "images": ["6 English image prompts"]}}]}}"""
    res = ask(cfg["model"], system, user, 4000, as_json=True)
    for sh in res["shorts"]:
        sh["images"] = [f"{x}, vertical composition, {cfg['image_style']}" for x in sh["images"]]
    return res["shorts"][:n]
