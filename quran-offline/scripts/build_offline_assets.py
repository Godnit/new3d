#!/usr/bin/env python3
"""Build compact offline Quran, Madani Mushaf and hadith assets for Rafiq Al-Huda."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
WHITESPACE = re.compile(r"\s+")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, separators=(",", ":"))


def clean_text(value: Any) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    text = text.replace("\u202b", "").replace("\u202c", "")
    return WHITESPACE.sub(" ", text).strip()


def normalize_arabic(value: Any) -> str:
    text = ARABIC_DIACRITICS.sub("", clean_text(value))
    table = str.maketrans({
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه",
        "ؤ": "و", "ئ": "ي", "ـ": " ",
    })
    text = text.translate(table)
    text = re.sub(r"[^\u0621-\u064A0-9 ]", " ", text)
    return WHITESPACE.sub(" ", text).strip().lower()


def extract_narrator(arabic: str) -> str:
    text = clean_text(arabic)
    patterns = [
        r"^(عَنْ.{2,180}?)(?:قَالَ|قَالَتْ|يَقُولُ|:)\s*",
        r"^(حَدَّثَنَا.{2,180}?)(?:قَالَ|:)\s*",
        r"^(أَنَّ.{2,160}?)(?:قَالَ|:)\s*",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.DOTALL)
        if match:
            return clean_text(match.group(1)).rstrip("،.:")
    first = re.split(r"[.:\n]", text, maxsplit=1)[0]
    return clean_text(first[:150]).rstrip("،.:") or "غير مفصول في المصدر"


def build_pages(page_dir: Path) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    total_verses = 0
    for page_number in range(1, 605):
        source = page_dir / f"{page_number}.json"
        if not source.exists():
            raise FileNotFoundError(f"Missing Quran page: {source}")
        data = load_json(source)
        raw_verses = data.get("pages", data.get("verses", []))
        verses = []
        for item in raw_verses:
            verses.append({
                "chapter": int(item["chapter"]),
                "verse": int(item["verse"]),
                "text": clean_text(item["text"]),
            })
        total_verses += len(verses)
        pages.append({"page": page_number, "verses": verses})
    if len(pages) != 604:
        raise ValueError(f"Expected 604 Quran pages, got {len(pages)}")
    if total_verses != 6236:
        raise ValueError(f"Expected 6236 Quran verses across pages, got {total_verses}")
    return pages


def _api_verses(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("verses"), list):
            return payload["verses"]
        nested = payload.get("data")
        if isinstance(nested, dict) and isinstance(nested.get("verses"), list):
            return nested["verses"]
    raise ValueError("QCF page response does not contain a verses array")


def _word_line(word: dict[str, Any], fallback: int | None) -> int | None:
    raw = word.get("line_number")
    if raw is None:
        raw = word.get("line")
    try:
        line = int(raw)
    except (TypeError, ValueError):
        return fallback
    return line if 1 <= line <= 15 else fallback


def _choose_free_line(preferred: int, before: int, occupied: set[int]) -> int | None:
    candidates = [preferred]
    for distance in range(1, 16):
        candidates.extend((preferred - distance, preferred + distance))
    for line in candidates:
        if 1 <= line < before and line not in occupied:
            return line
    return None


def build_mushaf_layout(qcf_dir: Path) -> list[dict[str, Any]]:
    """Create the exact 15-line Madani page structure using QCF V2 glyph codes."""
    result: list[dict[str, Any]] = []
    total_words = 0
    verse_ends: set[str] = set()

    for page_number in range(1, 605):
        source = qcf_dir / f"{page_number}.json"
        if not source.exists():
            raise FileNotFoundError(f"Missing QCF page response: {source}")
        verses = _api_verses(load_json(source))
        line_words: dict[int, list[dict[str, str]]] = defaultdict(list)
        first_verse_lines: dict[int, int] = {}
        surahs: list[int] = []
        juz = 1

        for verse in verses:
            verse_key = clean_text(verse.get("verse_key"))
            chapter_raw = verse.get("chapter_id")
            verse_number_raw = verse.get("verse_number")
            if not chapter_raw and ":" in verse_key:
                chapter_raw = verse_key.split(":", 1)[0]
            if not verse_number_raw and ":" in verse_key:
                verse_number_raw = verse_key.split(":", 1)[1]
            chapter = int(chapter_raw or 1)
            verse_number = int(verse_number_raw or 1)
            juz = int(verse.get("juz_number") or juz)
            if chapter not in surahs:
                surahs.append(chapter)

            words = verse.get("words") or []
            known_lines = [_word_line(word, None) for word in words]
            verse_line = next((line for line in known_lines if line is not None), None)
            last_line = verse_line
            for word in words:
                line = _word_line(word, last_line or verse_line)
                if line is None:
                    continue
                last_line = line
                glyph = clean_text(word.get("code_v2") or word.get("code_v1"))
                text = clean_text(
                    word.get("text_qpc_hafs")
                    or word.get("text_uthmani")
                    or word.get("text")
                )
                if not glyph:
                    glyph = text
                kind = clean_text(word.get("char_type_name") or word.get("char_type") or "word")
                record = {"c": glyph, "t": text, "k": kind, "v": verse_key}
                line_words[line].append(record)
                total_words += 1
                if kind == "end":
                    verse_ends.add(verse_key)
            if verse_number == 1 and verse_line is not None:
                first_verse_lines[chapter] = verse_line

        special: dict[int, dict[str, Any]] = {}
        occupied = set(line_words)
        for chapter, first_line in sorted(first_verse_lines.items(), key=lambda item: item[1]):
            title_preferred = first_line - (1 if chapter in {1, 9} else 2)
            title_line = _choose_free_line(title_preferred, first_line, occupied | set(special))
            if title_line is not None:
                special[title_line] = {"line": title_line, "kind": "surah", "chapter": chapter}
            if chapter not in {1, 9}:
                basmala_line = _choose_free_line(first_line - 1, first_line, occupied | set(special))
                if basmala_line is not None:
                    special[basmala_line] = {"line": basmala_line, "kind": "basmala", "chapter": chapter}

        lines: list[dict[str, Any]] = []
        for line_number in range(1, 16):
            if line_number in special:
                lines.append(special[line_number])
            elif line_words.get(line_number):
                lines.append({"line": line_number, "kind": "quran", "words": line_words[line_number]})
            else:
                lines.append({"line": line_number, "kind": "blank"})

        if not any(line["kind"] == "quran" for line in lines):
            raise ValueError(f"Page {page_number} has no Quran lines")
        result.append({
            "page": page_number,
            "juz": juz,
            "surahs": surahs,
            "lines": lines,
        })

    if len(result) != 604:
        raise ValueError(f"Expected 604 Mushaf pages, got {len(result)}")
    if total_words < 70_000:
        raise ValueError(f"Unexpectedly low QCF word count: {total_words}")
    if len(verse_ends) < 6_200:
        raise ValueError(f"Expected at least 6200 verse endings, got {len(verse_ends)}")
    return result


def convert_hadith_file(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    data = load_json(path)
    title = clean_text(data.get("metadata", {}).get("arabic", {}).get("title") or path.stem)
    raw_hadiths = data.get("hadiths", [])
    if limit is not None:
        raw_hadiths = raw_hadiths[:limit]
    output: list[dict[str, Any]] = []
    for raw in raw_hadiths:
        text = clean_text(raw.get("arabic"))
        if not text:
            continue
        narrator = extract_narrator(text)
        if title in {"صحيح البخاري", "صحيح مسلم"}:
            grade = "صحيح"
        elif title == "الأربعون النووية":
            grade = "من مجموعة الأربعين النووية — راجع التخريج المذكور في النص"
        elif title == "الأربعون القدسية":
            grade = "حديث قدسي — راجع التخريج المذكور في النص"
        else:
            grade = "راجع تخريج المصدر"
        record_id = int(raw.get("id") or len(output) + 1)
        number = int(raw.get("idInBook") or raw.get("id") or len(output) + 1)
        search = normalize_arabic(f"{text} {narrator} {title} {number}")
        output.append({
            "id": record_id,
            "book": title,
            "number": number,
            "text": text,
            "narrator": narrator,
            "grade": grade,
            "search": search,
        })
    return output


def build_hadiths(hadith_dir: Path) -> list[dict[str, Any]]:
    sources = [
        (hadith_dir / "bukhari.json", 4000),
        (hadith_dir / "muslim.json", 3000),
        (hadith_dir / "nawawi40.json", None),
        (hadith_dir / "qudsi40.json", None),
    ]
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for path, limit in sources:
        if not path.exists():
            raise FileNotFoundError(f"Missing hadith source: {path}")
        for item in convert_hadith_file(path, limit):
            key = (item["book"], item["number"])
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
    if len(result) < 6000:
        raise ValueError(f"Expected at least 6000 hadiths, got {len(result)}")
    return result


def validate_quran_index(path: Path) -> None:
    quran = load_json(path)
    if not isinstance(quran, list) or len(quran) != 114:
        raise ValueError("Quran index must contain exactly 114 surahs")
    count = sum(len(surah.get("verses", [])) for surah in quran)
    if count != 6236:
        raise ValueError(f"Quran index must contain 6236 verses, got {count}")
    if quran[0].get("name") != "الفاتحة" or quran[-1].get("name") != "الناس":
        raise ValueError("Unexpected first or last surah")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--pages", type=Path, required=True)
    parser.add_argument("--qcf-pages", type=Path, required=True)
    parser.add_argument("--hadith", type=Path, required=True)
    args = parser.parse_args()

    validate_quran_index(args.assets / "quran.json")
    pages = build_pages(args.pages)
    mushaf = build_mushaf_layout(args.qcf_pages)
    hadiths = build_hadiths(args.hadith)
    dump_json(args.assets / "quran_pages.json", pages)
    dump_json(args.assets / "quran_mushaf.json", mushaf)
    dump_json(args.assets / "hadith.json", hadiths)
    print(
        f"Validated 114 surahs, {len(mushaf)} authentic Mushaf pages, "
        f"6236 verses and {len(hadiths)} hadiths"
    )


if __name__ == "__main__":
    main()
