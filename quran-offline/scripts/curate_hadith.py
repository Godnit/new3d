#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
SPACE = re.compile(r"\s+")
IMPORTANT = [
    "الايمان", "الاسلام", "الاحسان", "النيه", "الاخلاص", "القران", "الصلاه", "الزكاه", "الصيام", "الحج",
    "الصدق", "الكذب", "الامانه", "الرحمه", "التوبه", "الاستغفار", "الدعاء", "الذكر", "التسبيح", "الجنه",
    "النار", "الوالدين", "الجار", "الاخلاق", "العلم", "العمل", "الصدقه", "الربا", "البيع", "النكاح",
    "الظلم", "الصبر", "الشكر", "التوكل", "الحلال", "الحرام", "المسلم", "المومن", "رسول الله", "النبي",
    "قيام الليل", "الوتر", "الجمعه", "الاذان", "الوضوء", "الطهاره", "الفتنه", "القيامه", "القبر", "الموت",
]


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    text = DIACRITICS.sub("", text)
    text = text.translate(str.maketrans({"أ":"ا","إ":"ا","آ":"ا","ٱ":"ا","ى":"ي","ة":"ه","ؤ":"و","ئ":"ي","ـ":" "}))
    text = re.sub(r"[^\u0621-\u064A0-9 ]", " ", text)
    return SPACE.sub(" ", text).strip().lower()


def score(item: dict) -> tuple[int, int]:
    text = normalize((item.get("text") or "") + " " + (item.get("display") or ""))
    points = sum(35 for word in IMPORTANT if word in text)
    length = len(text)
    if 100 <= length <= 950:
        points += 32
    elif length > 1800:
        points -= 45
    if "قال رسول الله" in text or "عن النبي" in text:
        points += 24
    number = int(item.get("number") or 99999)
    points += max(0, 34 - min(34, number // 100))
    return points, -length


def unique(items: list[dict]) -> list[dict]:
    result = []
    seen = set()
    for item in items:
        key = normalize(item.get("display") or item.get("text") or "")[:220]
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def main() -> None:
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    groups: dict[str, list[dict]] = {}
    for item in data:
        groups.setdefault(item.get("book") or "", []).append(item)

    selected: list[dict] = []
    # Keep the compact foundational collections complete.
    for name in ("الأربعون النووية", "الأربعون القدسية"):
        selected.extend(groups.get(name, []))
    # Add only the most useful, famous and searchable records from the two Sahihs.
    for name, limit in (("صحيح البخاري", 150), ("صحيح مسلم", 150)):
        ranked = sorted(groups.get(name, []), key=score, reverse=True)
        selected.extend(ranked[:limit])

    if not any("يتحري الصدق" in normalize(item.get("text") or "") for item in selected):
        selected.insert(0, {
            "id": 9906094,
            "book": "صحيح البخاري",
            "number": 6094,
            "text": "عَنْ عَبْدِ اللَّهِ بْنِ مَسْعُودٍ رضي الله عنه، عَنِ النَّبِيِّ ﷺ قَالَ: عَلَيْكُمْ بِالصِّدْقِ، فَإِنَّ الصِّدْقَ يَهْدِي إِلَى الْبِرِّ، وَإِنَّ الْبِرَّ يَهْدِي إِلَى الْجَنَّةِ، وَمَا يَزَالُ الرَّجُلُ يَصْدُقُ وَيَتَحَرَّى الصِّدْقَ حَتَّى يُكْتَبَ عِنْدَ اللَّهِ صِدِّيقًا، وَإِيَّاكُمْ وَالْكَذِبَ، فَإِنَّ الْكَذِبَ يَهْدِي إِلَى الْفُجُورِ، وَإِنَّ الْفُجُورَ يَهْدِي إِلَى النَّارِ، وَمَا يَزَالُ الرَّجُلُ يَكْذِبُ وَيَتَحَرَّى الْكَذِبَ حَتَّى يُكْتَبَ عِنْدَ اللَّهِ كَذَّابًا.",
            "display": "قال النبي ﷺ: عليكم بالصدق، فإن الصدق يهدي إلى البر، وإن البر يهدي إلى الجنة، وما يزال الرجل يصدق ويتحرى الصدق حتى يكتب عند الله صديقًا، وإياكم والكذب، فإن الكذب يهدي إلى الفجور، وإن الفجور يهدي إلى النار.",
            "narrator": "عن عبد الله بن مسعود رضي الله عنه، عن النبي ﷺ",
            "grade": "صحيح"
        })

    selected = unique(selected)
    selected.sort(key=lambda item: (0 if int(item.get("id") or 0) == 9906094 else 1, -(score(item)[0])))
    if not 320 <= len(selected) <= 430:
        raise SystemExit(f"Unexpected curated hadith count: {len(selected)}")
    if not any("يتحري الصدق" in normalize(item.get("text") or "") for item in selected):
        raise SystemExit("Requested truthfulness hadith is missing")
    path.write_text(json.dumps(selected, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Curated {len(data)} hadiths down to {len(selected)} important records")


if __name__ == "__main__":
    main()
