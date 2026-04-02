from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
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
    """Return a (score, reasons) tuple rating how well a song matches the user's genre, mood, and energy preferences."""
    score = 0.0
    reasons = []

    # Genre match: +1.0 (halved — EXPERIMENT: weight shift)
    if song["genre"] == user_prefs["favorite_genre"]:
        score += 1.0
        reasons.append(f"genre match (+1.0)")

    # Mood match: +1.0
    if song["mood"] == user_prefs["favorite_mood"]:
        score += 1.0
        reasons.append(f"mood match (+1.0)")

    # Energy proximity: 0.0 – 2.0 based on closeness to target (doubled — EXPERIMENT: weight shift)
    energy_points = round(2.0 * (1.0 - abs(song["energy"] - user_prefs["target_energy"])), 2)
    score += energy_points
    reasons.append(f"energy {song['energy']} vs target {user_prefs['target_energy']} (+{energy_points})")

    return round(score, 2), reasons


def load_songs(csv_path: str) -> List[Dict]:
    """Read a CSV file of songs and return a list of dicts with numeric fields cast to float/int."""
    
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id":           int(row["id"]),
                "title":        row["title"],
                "artist":       row["artist"],
                "genre":        row["genre"],
                "mood":         row["mood"],
                "energy":       float(row["energy"]),
                "tempo_bpm":    float(row["tempo_bpm"]),
                "valence":      float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
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
