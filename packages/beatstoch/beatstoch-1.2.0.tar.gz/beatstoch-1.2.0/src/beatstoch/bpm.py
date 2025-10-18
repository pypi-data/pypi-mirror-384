# filename: src/beatstoch/bpm.py
import re
import sys
import unicodedata
from typing import Optional, List
import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (compatible; beatstoch/1.0; +https://pypi.org/project/beatstoch/)"
)
REQUEST_TIMEOUT = 12  # seconds


def _sanitize_query(s: str) -> str:
    # Convert smart punctuation to ASCII so the request path is clean
    return (
        (s or "")
        .replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .replace("–", "-")
        .replace("—", "-")
        .strip()
    )


def _normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("’", "'")
    return s


def _parse_rows(html: str) -> List[List[str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: List[List[str]] = []
    for tr in soup.select("table tr"):
        cols = tr.find_all(["td", "th"])
        if len(cols) < 4:
            continue
        # Each column contains concatenated text - combine all columns for this row
        full_row_text = " ".join([col.get_text(strip=True) for col in cols])
        rows.append([full_row_text])
    return rows


def _pick_best_bpm(
    rows: List[List[str]], q_title: str, q_artist: Optional[str]
) -> Optional[float]:
    best_bpm = None
    best_score = -1.0

    def numerize(s: str) -> str:
        return re.sub(r"[^\w]", "", s or "")

    for row_data in rows:
        if not row_data or len(row_data) == 0:
            continue

        full_text = row_data[0]  # Each row is now just one column with all text
        text_norm = _normalize_text(full_text)

        # Extract BPM values from the text
        bpm_candidates = []
        for match in re.finditer(r'\b(\d{2,3})\b', text_norm):
            bpm_val = int(match.group(1))
            if 40 <= bpm_val <= 220:
                bpm_candidates.append(float(bpm_val))

        if not bpm_candidates:
            continue

        # Use the first valid BPM found
        bpm_candidate = bpm_candidates[0]

        # Calculate match score for this row
        score = 0.0

        # Check if title matches
        if q_title in text_norm or text_norm in q_title:
            score += 3.0
        elif numerize(q_title) in numerize(text_norm):
            score += 2.0

        # Check if artist matches (if provided)
        if q_artist:
            if q_artist in text_norm or text_norm in q_artist:
                score += 3.0
            elif numerize(q_artist) in numerize(text_norm):
                score += 2.0

        # Prefer rows without remix/edit/mix/dub/extended
        if not re.search(r'\b(remix|edit|mix|dub|extended)\b', text_norm):
            score += 0.5

        if score > best_score:
            best_score = score
            best_bpm = bpm_candidate

    return best_bpm


def fetch_bpm_from_bpmdatabase(
    song_title: str, artist: Optional[str] = None, verbose: bool = False
) -> Optional[float]:
    if not song_title:
        return None
    song_title = _sanitize_query(song_title)
    artist = _sanitize_query(artist) if artist else None

    headers = {"User-Agent": USER_AGENT}

    # Prefer the explicit music/search endpoint if artist is provided
    if artist:
        try:
            if verbose:
                print(f"beatstoch: querying BPMDatabase for '{song_title}' by '{artist}'", file=sys.stderr)
            resp = requests.get(
                "https://www.bpmdatabase.com/music/search/",
                params={"artist": artist, "title": song_title, "bpm": "", "genre": ""},
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            rows = _parse_rows(resp.text)
            bpm = _pick_best_bpm(
                rows, _normalize_text(song_title), _normalize_text(artist)
            )
            if bpm is not None:
                if verbose:
                    print(f"beatstoch: found BPM {bpm} for '{song_title}' by '{artist}'", file=sys.stderr)
                return bpm
        except requests.RequestException as e:
            print(
                f"beatstoch: network error querying BPMDatabase (music/search): {e}",
                file=sys.stderr,
            )

    # Fallback: title-only search via search.asp (NO trailing slash)
    try:
        if verbose:
            print(f"beatstoch: falling back to title-only search for '{song_title}'", file=sys.stderr)
        resp2 = requests.get(
            "https://www.bpmdatabase.com/search.asp",
            params={"title": song_title},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        resp2.raise_for_status()
        rows2 = _parse_rows(resp2.text)
        bpm = _pick_best_bpm(
            rows2, _normalize_text(song_title), _normalize_text(artist) if artist else None
        )
        if bpm is not None and verbose:
            print(f"beatstoch: found BPM {bpm} from fallback search for '{song_title}'", file=sys.stderr)
        return bpm
    except requests.RequestException as e:
        print(
            f"beatstoch: network error querying BPMDatabase (search.asp): {e}",
            file=sys.stderr,
        )
        return None
