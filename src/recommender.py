from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import csv

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # --- Advanced attributes (default so existing tests keep passing) ---
    popularity: int = 50            # 0–100: mainstream appeal
    release_decade: int = 2020      # e.g. 1980, 1990, 2000, 2010, 2020
    mood_tags: str = ""             # pipe-separated detail tags e.g. "calm|focused|ambient"
    instrumentalness: float = 0.5   # 0 = very vocal, 1 = fully instrumental
    liveness: float = 0.1           # 0 = studio polished, 1 = live recording feel

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # --- Advanced preferences (default so existing tests keep passing) ---
    preferred_popularity: int = 50          # 0 = underground, 100 = mainstream
    preferred_decade: int = 2020            # preferred era of music
    preferred_mood_tags: List[str] = field(default_factory=list)  # e.g. ["calm", "focused"]
    preferred_instrumentalness: float = 0.5 # 0 = lots of vocals, 1 = fully instrumental
    preferred_liveness: float = 0.1         # 0 = studio, 1 = live feel

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects ranked by score against the given user profile."""
        from dataclasses import asdict
        user_prefs = asdict(user)
        return sorted(
            self.songs,
            key=lambda song: score_song(user_prefs, asdict(song))[0],
            reverse=True
        )[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable string explaining why a song was recommended."""
        from dataclasses import asdict
        _, reasons = score_song(asdict(user), asdict(song))
        return ", ".join(reasons)

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Return a (score, reasons) tuple rating how well a song matches the user profile.

    Scoring breakdown (max 10.5):
      Genre match         +1.0   exact label match
      Mood match          +1.0   exact label match
      Energy proximity    0–2.0  2 × (1 − |song − target|)
      Popularity proximity 0–1.0  1 − |song − user| / 100
      Decade proximity    0–1.0  loses 0.25 per decade away, floor 0
      Mood tag overlap    0–1.5  +0.5 per shared tag, capped at 1.5
      Instrumentalness    0–1.0  1 − |song − user|
      Liveness            0–1.0  1 − |song − user|
    """
    score = 0.0
    reasons = []

    # --- Original signals ---

    # Genre match: +1.0
    if song["genre"] == user_prefs["favorite_genre"]:
        score += 1.0
        reasons.append("genre match (+1.0)")

    # Mood match: +1.0
    if song["mood"] == user_prefs["favorite_mood"]:
        score += 1.0
        reasons.append("mood match (+1.0)")

    # Energy proximity: 0.0–2.0
    energy_points = round(2.0 * (1.0 - abs(song["energy"] - user_prefs["target_energy"])), 2)
    score += energy_points
    reasons.append(f"energy {song['energy']} vs target {user_prefs['target_energy']} (+{energy_points})")

    # --- Advanced signals ---

    # Popularity proximity: 0.0–1.0
    # Underground fans (low preferred_popularity) are penalised by mainstream songs and vice versa.
    pop_points = round(1.0 - abs(song.get("popularity", 50) - user_prefs.get("preferred_popularity", 50)) / 100, 2)
    score += pop_points
    reasons.append(f"popularity {song.get('popularity', 50)} vs preferred {user_prefs.get('preferred_popularity', 50)} (+{pop_points})")

    # Decade proximity: 0.0–1.0
    # Each decade of distance costs 0.25 points; 4+ decades away scores 0.
    decade_gap = abs(song.get("release_decade", 2020) - user_prefs.get("preferred_decade", 2020))
    decade_points = round(max(0.0, 1.0 - (decade_gap / 10) * 0.25), 2)
    score += decade_points
    reasons.append(f"decade {song.get('release_decade', 2020)} vs preferred {user_prefs.get('preferred_decade', 2020)} (+{decade_points})")

    # Mood tag overlap: 0.0–1.5
    # Each shared tag between the song and user adds +0.5, capped at 1.5 (3 matches).
    song_tags = set(song.get("mood_tags", "").split("|")) if song.get("mood_tags") else set()
    user_tags = set(user_prefs.get("preferred_mood_tags") or [])
    tag_matches = len(song_tags & user_tags)
    tag_points = round(min(1.5, tag_matches * 0.5), 2)
    if tag_points > 0:
        score += tag_points
        reasons.append(f"mood tags {sorted(song_tags & user_tags)} matched (+{tag_points})")
    else:
        reasons.append("mood tags no match (+0.0)")

    # Instrumentalness proximity: 0.0–1.0
    # Vocal-preferring users are penalised by instrumental tracks and vice versa.
    inst_points = round(1.0 - abs(song.get("instrumentalness", 0.5) - user_prefs.get("preferred_instrumentalness", 0.5)), 2)
    score += inst_points
    reasons.append(f"instrumentalness {song.get('instrumentalness', 0.5)} vs preferred {user_prefs.get('preferred_instrumentalness', 0.5)} (+{inst_points})")

    # Liveness proximity: 0.0–1.0
    # Live-show fans are penalised by polished studio recordings and vice versa.
    live_points = round(1.0 - abs(song.get("liveness", 0.1) - user_prefs.get("preferred_liveness", 0.1)), 2)
    score += live_points
    reasons.append(f"liveness {song.get('liveness', 0.1)} vs preferred {user_prefs.get('preferred_liveness', 0.1)} (+{live_points})")

    return round(score, 2), reasons


def load_songs(csv_path: str) -> List[Dict]:
    """Read a CSV file of songs and return a list of dicts with numeric fields cast to float/int."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id":                 int(row["id"]),
                "title":              row["title"],
                "artist":             row["artist"],
                "genre":              row["genre"],
                "mood":               row["mood"],
                "energy":             float(row["energy"]),
                "tempo_bpm":          float(row["tempo_bpm"]),
                "valence":            float(row["valence"]),
                "danceability":       float(row["danceability"]),
                "acousticness":       float(row["acousticness"]),
                "popularity":         int(row["popularity"]),
                "release_decade":     int(row["release_decade"]),
                "mood_tags":          row["mood_tags"],
                "instrumentalness":   float(row["instrumentalness"]),
                "liveness":           float(row["liveness"]),
            })
    return songs

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song in the catalog and return the top k as (song, score, explanation) tuples."""
    scored = [
        (song, *score_song(user_prefs, song))
        for song in songs
    ]
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    return [
        (song, score, ", ".join(reasons))
        for song, score, reasons in ranked[:k]
    ]
