#!/usr/bin/env python3
"""Build compact offline Quran, Mushaf layout and hadith assets for Rafiq Al-Huda Lite."""
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


def arabic_number(value: int) -> str:
    return str(value).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))


def strip_diacritics_with_map(text: str) -> tuple[str, list[int]]:
    plain: list[str] = []
    positions: list[int] = []
    for index, char in enumerate(text):
        if ARABIC_DIACRITICS.fullmatch(char):
            continue
        plain.append(char)
        positions.append(index)
    return "".join(plain), positions


def original_index(mapping: list[int], plain_index: int, fallback: int) -> int:
    if not mapping:
        return fallback
    plain_index = max(0, min(plain_index, len(mapping) - 1))
    return mapping[plain_index]


def extract_hadith_parts(arabic: str) -> tuple[str, str]:
    """Return a concise companion attribution and a matn without the long isnad."""
    text = clean_text(arabic)
    plain, mapping = strip_diacritics_with_map(text)
    normalized_plain = normalize_arabic(plain)

    marker_phrases = [
        "قال رسول الله", "قالت قال رسول الله", "سمعت رسول الله",
        "ان رسول الله", "قال النبي", "عن النبي", "ان النبي",
    ]
    marker_pos = -1
    selected_marker = ""
    for marker in marker_phrases:
        pos = normalized_plain.find(marker)
        if pos >= 0 and (marker_pos < 0 or pos < marker_pos):
            marker_pos = pos
            selected_marker = marker

    prefix_plain = normalized_plain[:marker_pos] if marker_pos >= 0 else normalized_plain
    narrator_matches = re.findall(
        r"(?:^|\s)عن\s+(.{2,90}?)(?=\s+عن\s+|\s+قال(?:ت)?\s+|\s+ان\s+|$)",
        prefix_plain,
    )
    narrator_name = clean_text(narrator_matches[-1] if narrator_matches else "")
    narrator_name = re.sub(r"^(?:ان|انه|انها)\s+", "", narrator_name).strip(" ،.:")

    if marker_pos >= 0:
        display_plain_start = marker_pos
        nearby = normalized_plain[max(0, marker_pos - 18): marker_pos + 2]
        last_said = max(nearby.rfind("قال "), nearby.rfind("قالت "), nearby.rfind("سمعت "))
        if last_said >= 0:
            display_plain_start = max(0, marker_pos - 18) + last_said
        display_start = original_index(mapping, display_plain_start, 0)
        display = clean_text(text[display_start:])
    else:
        # Some reports have no explicit Prophet marker. Remove only the obvious leading chain.
        chain_markers = [m.start() for m in re.finditer(r"\s(?:قال|قالت)\s", normalized_plain)]
        if chain_markers:
            display_start = original_index(mapping, chain_markers[-1] + 1, 0)
            display = clean_text(text[display_start:])
        else:
            display = text

    if narrator_name:
        narrator = f"عن {narrator_name}، عن النبي ﷺ" if selected_marker else f"عن {narrator_name}"
    else:
        narrator = "عن الصحابي الراوي، عن النبي ﷺ" if selected_marker else "الراوي مذكور في المصدر"

    if len(display) < 18:
        display = text
    return narrator, display


def build_pages(page_dir: Path) -> list[dict[str, Any]]:
    """Store only chapter/verse pairs; the searchable text already exists in quran.json."""
    pages: list[dict[str, Any]] = []
    total_verses = 0
    for page_number in range(1, 605):
        source = page_dir / f"{page_number}.json"
        if not source.exists():
            raise FileNotFoundError(f"Missing Quran page: {source}")
        data = load_json(source)
        raw_verses = data.get("pages", data.get("verses", []))
        pairs = [[int(item["chapter"]), int(item["verse"])] for item in raw_verses]
        total_verses += len(pairs)
        pages.append({"v": pairs})
    if len(pages) != 604 or total_verses != 6236:
        raise ValueError(f"Invalid Quran pages: {len(pages)} pages, {total_verses} verses")
    return pages


def _api_verses(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("verses"), list):
            return payload["verses"]
        nested = payload.get("data")
        if isinstance(nested, dict) and isinstance(nested.get("verses"), list):
            return nested["verses"]
    raise ValueError("Quran page response does not contain a verses array")


def _word_line(word: dict[str, Any], fallback: int | None) -> int | None:
    raw = word.get("line_number", word.get("line"))
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
    """Keep the 15-line Madani page layout but use one Unicode Uthmanic font."""
    result: list[dict[str, Any]] = []
    total_words = 0
    verse_ends = 0

    for page_number in range(1, 605):
        source = qcf_dir / f"{page_number}.json"
        if not source.exists():
            raise FileNotFoundError(f"Missing Quran layout page: {source}")
        verses = _api_verses(load_json(source))
        line_words: dict[int, list[str]] = defaultdict(list)
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
                kind = clean_text(word.get("char_type_name") or word.get("char_type") or "word")
                text = clean_text(
                    word.get("text_qpc_hafs")
                    or word.get("text_uthmani")
                    or word.get("text")
                )
                if kind == "end":
                    verse_ends += 1
                    if not text:
                        text = f"﴿{arabic_number(verse_number)}﴾"
                if text:
                    line_words[line].append(text)
                    total_words += 1
            if verse_number == 1 and verse_line is not None:
                first_verse_lines[chapter] = verse_line

        special: dict[int, dict[str, Any]] = {}
        occupied = set(line_words)
        for chapter, first_line in sorted(first_verse_lines.items(), key=lambda item: item[1]):
            title_preferred = first_line - (1 if chapter in {1, 9} else 2)
            title_line = _choose_free_line(title_preferred, first_line, occupied | set(special))
            if title_line is not None:
                special[title_line] = {"n": title_line, "k": "s", "c": chapter}
            if chapter not in {1, 9}:
                basmala_line = _choose_free_line(first_line - 1, first_line, occupied | set(special))
                if basmala_line is not None:
                    special[basmala_line] = {"n": basmala_line, "k": "b", "c": chapter}

        lines: list[dict[str, Any]] = []
        for line_number in range(1, 16):
            if line_number in special:
                lines.append(special[line_number])
            elif line_words.get(line_number):
                lines.append({"n": line_number, "k": "q", "t": " ".join(line_words[line_number])})
            else:
                lines.append({"n": line_number, "k": "x"})

        if not any(line["k"] == "q" for line in lines):
            raise ValueError(f"Page {page_number} has no Quran lines")
        result.append({"j": juz, "s": surahs, "l": lines})

    if len(result) != 604:
        raise ValueError(f"Expected 604 Mushaf pages, got {len(result)}")
    if total_words < 70_000 or verse_ends < 6_200:
        raise ValueError(f"Unexpected Quran layout counts: {total_words} words, {verse_ends} endings")
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
        narrator, display = extract_hadith_parts(text)
        if title in {"صحيح البخاري", "صحيح مسلم"}:
            grade = "صحيح"
        elif title == "الأربعون النووية":
            grade = "بحسب التخريج المذكور في مصدر الأربعين النووية"
        elif title == "الأربعون القدسية":
            grade = "حديث قدسي — راجع التخريج المذكور في المصدر"
        else:
            grade = "راجع تخريج المصدر"
        record_id = int(raw.get("id") or len(output) + 1)
        number = int(raw.get("idInBook") or raw.get("id") or len(output) + 1)
        output.append({
            "id": record_id,
            "book": title,
            "number": number,
            "text": text,
            "display": display,
            "narrator": narrator,
            "grade": grade,
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--pages", type=Path, required=True)
    parser.add_argument("--qcf-pages", type=Path, required=True)
    parser.add_argument("--hadith", type=Path, required=True)
    args = parser.parse_args()

    validate_quran_index(args.assets / "quran.json")
    dump_json(args.assets / "quran_pages.json", build_pages(args.pages))
    dump_json(args.assets / "quran_mushaf.json", build_mushaf_layout(args.qcf_pages))
    hadiths = build_hadiths(args.hadith)
    dump_json(args.assets / "hadith.json", hadiths)
    concise = sum(1 for item in hadiths if item.get("display") and item["display"] != item["text"])
    print(f"Built 604 Quran pages and {len(hadiths)} hadiths; shortened {concise} chains")


if __name__ == "__main__":
    main()
