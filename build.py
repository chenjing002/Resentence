#!/usr/bin/env python3
"""Build sentences.json (English sentences + highlight words) from a Rewords export."""
import hashlib
import json
import re
import sys
from pathlib import Path

DEFAULT_SRC = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Rewords/rewords-vocabulary.json"
OUT = Path(__file__).resolve().parent / "sentences.json"

# CJK ideographs, CJK punctuation, full-width forms
CJK = re.compile(r"[⺀-⿿　-〿぀-ヿ㐀-䶿一-鿿豈-﫿＀-￯]+")
ELLIPSIS = ("…", "...")


def strip_ellipsis(text):
    cut_start = cut_end = False
    text = text.strip()
    for e in ELLIPSIS:
        if text.startswith(e):
            text, cut_start = text[len(e):].lstrip(), True
        if text.endswith(e):
            text, cut_end = text[: -len(e)].rstrip(), True
    return text, cut_start, cut_end


def english_part(raw, words):
    """Return (text, cut_start, cut_end) holding only the English part of a saved sentence."""
    text, cut_start, cut_end = strip_ellipsis(raw)
    segments = CJK.split(text)
    candidates = [i for i, s in enumerate(segments) if re.search(r"[A-Za-z]", s)]
    if not candidates:
        return "", False, False
    # Prefer the segment that contains a saved word, then the longest one.
    def score(i):
        s = segments[i].lower()
        return (any(re.search(rf"\b{re.escape(w)}\b", s) for w in words), len(s))
    idx = max(candidates, key=score)
    seg = segments[idx].strip()
    cut_start = cut_start and idx == 0
    cut_end = cut_end and idx == len(segments) - 1
    lowered = {w.lower() for w in words}

    # Drop a half-word left over from truncation, unless it is the saved word.
    if cut_start:
        first, _, rest = seg.partition(" ")
        if rest and first.isalpha() and first.islower() and first.lower() not in lowered:
            seg = rest
    if cut_end:
        rest, _, last = seg.rpartition(" ")
        if rest and last.isalpha() and last.lower() not in lowered:
            seg = rest
    return seg.strip(), cut_start, cut_end


def english_title(title):
    parts = [p.strip(" ·-—|:") for p in CJK.split(title or "")]
    parts = [p for p in parts if re.search(r"[A-Za-z]", p)]
    return max(parts, key=len) if parts else ""


def definitions(entry):
    if not entry:
        return None
    meanings = []
    for m in entry.get("meanings", [])[:3]:
        defs = [d.get("def", "") for d in m.get("definitions", []) if d.get("def")]
        if defs:
            meanings.append({"pos": m.get("pos", ""), "def": defs[0]})
    return {"phonetic": entry.get("phonetic", ""), "meanings": meanings}


def position(text, word):
    m = re.search(rf"\b{re.escape(word)}\b", text, re.I)
    return m.start() if m else len(text)


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def build(src):
    data = json.loads(Path(src).read_text(encoding="utf-8"))
    items = []
    for w in data.get("words", []):
        word = (w.get("word") or "").strip()
        if not word:
            continue
        forms = [f for f in (w.get("forms") or []) if isinstance(f, str)]
        for c in w.get("contexts", []):
            text, cs, ce = english_part(c.get("sentence", ""), [word, *forms])
            if not text:
                continue
            items.append({
                "text": text, "cutStart": cs, "cutEnd": ce,
                "word": word, "forms": forms, "def": definitions(w.get("entry")),
                "source": english_title(c.get("title", "")), "url": c.get("url", ""),
                "addedAt": c.get("savedAt") or w.get("addedAt") or 0,
            })

    # Merge identical / truncated copies of the same sentence: longest version wins.
    cards = []
    for it in sorted(items, key=lambda x: (-len(x["text"]), x["addedAt"])):
        key = norm(it["text"])
        home = next((c for c in cards if key in c["_key"]), None)
        if home is None:
            home = {
                "_key": key, "text": it["text"], "cutStart": it["cutStart"], "cutEnd": it["cutEnd"],
                "words": [], "source": it["source"], "url": it["url"], "addedAt": it["addedAt"],
            }
            cards.append(home)
        home["addedAt"] = max(home["addedAt"], it["addedAt"])
        if all(x["word"].lower() != it["word"].lower() for x in home["words"]):
            home["words"].append({"word": it["word"], "forms": it["forms"], "def": it["def"]})

    for c in cards:
        c["id"] = hashlib.sha1(c.pop("_key").encode()).hexdigest()[:10]
        c["words"].sort(key=lambda w: position(c["text"], w["word"]))
    cards.sort(key=lambda c: -c["addedAt"])
    return cards


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    cards = build(src)
    out = json.dumps(cards, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if not OUT.exists() or OUT.read_text(encoding="utf-8") != out:
        OUT.write_text(out, encoding="utf-8")
    print(f"{len(cards)} cards")


if __name__ == "__main__":
    main()
