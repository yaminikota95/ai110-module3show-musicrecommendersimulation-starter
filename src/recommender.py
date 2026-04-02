from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import csv

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

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
    # Advanced attributes — defaulted so existing tests keep passing
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
    # Advanced preferences — defaulted so existing tests keep passing
    preferred_popularity: int = 50
    preferred_decade: int = 2020
    preferred_mood_tags: List[str] = field(default_factory=list)
    preferred_instrumentalness: float = 0.5
    preferred_liveness: float = 0.1


# ---------------------------------------------------------------------------
# Strategy pattern
# ---------------------------------------------------------------------------

def _weighted_score(user_prefs: Dict, song: Dict, w: Dict) -> Tuple[float, List[str]]:
    """
    Core scoring math, fully parameterised by a weight dict `w`.

    Weight keys and what they control
    ----------------------------------
    genre          float  Added to score when genre label matches exactly.
                          Can be negative (DiscoveryMode) to penalise comfort-zone picks.
    mood           float  Added to score when mood label matches exactly.
    energy         float  Multiplier on (1 − |song_energy − target_energy|), so the
                          raw 0–1 proximity becomes 0–energy_weight points.
    popularity     float  Multiplier on popularity proximity (0–1 range).
    decade         float  Multiplier on decade proximity (0–1 range, −0.25 per decade away).
    tag_per_match  float  Points awarded per shared mood tag.
    tag_cap        float  Maximum total points from mood-tag overlap.
    inst           float  Multiplier on instrumentalness proximity (0–1 range).
    live           float  Multiplier on liveness proximity (0–1 range).
    """
    score = 0.0
    reasons = []

    # Genre — can be a bonus (positive) or a penalty (negative, used by DiscoveryMode)
    if song["genre"] == user_prefs["favorite_genre"]:
        g = w.get("genre", 1.0)
        score += g
        label = "penalty" if g < 0 else "match"
        reasons.append(f"genre {label} ({g:+.1f})")

    # Mood
    if song["mood"] == user_prefs["favorite_mood"]:
        m = w.get("mood", 1.0)
        score += m
        reasons.append(f"mood match ({m:+.1f})")

    # Energy proximity — scaled by weight
    energy_proximity = 1.0 - abs(song["energy"] - user_prefs["target_energy"])
    energy_points = round(w.get("energy", 2.0) * energy_proximity, 2)
    score += energy_points
    reasons.append(
        f"energy {song['energy']} vs {user_prefs['target_energy']} ({energy_points:+.2f})"
    )

    # Popularity proximity
    pop_weight = w.get("popularity", 1.0)
    if pop_weight != 0:
        pop_proximity = 1.0 - abs(
            song.get("popularity", 50) - user_prefs.get("preferred_popularity", 50)
        ) / 100
        pop_points = round(pop_weight * pop_proximity, 2)
        score += pop_points
        reasons.append(
            f"popularity {song.get('popularity', 50)} vs "
            f"{user_prefs.get('preferred_popularity', 50)} ({pop_points:+.2f})"
        )

    # Decade proximity — loses 0.25 per decade of distance
    decade_weight = w.get("decade", 1.0)
    if decade_weight != 0:
        decade_gap = abs(
            song.get("release_decade", 2020) - user_prefs.get("preferred_decade", 2020)
        )
        decade_proximity = max(0.0, 1.0 - (decade_gap / 10) * 0.25)
        decade_points = round(decade_weight * decade_proximity, 2)
        score += decade_points
        reasons.append(
            f"decade {song.get('release_decade', 2020)} vs "
            f"{user_prefs.get('preferred_decade', 2020)} ({decade_points:+.2f})"
        )

    # Mood tag overlap — +tag_per_match per shared tag, capped at tag_cap
    tag_bonus = w.get("tag_per_match", 0.5)
    tag_cap = w.get("tag_cap", 1.5)
    if tag_bonus > 0:
        song_tags = (
            set(song.get("mood_tags", "").split("|"))
            if song.get("mood_tags")
            else set()
        )
        user_tags = set(user_prefs.get("preferred_mood_tags") or [])
        shared = song_tags & user_tags
        tag_points = round(min(tag_cap, len(shared) * tag_bonus), 2)
        if tag_points > 0:
            score += tag_points
            reasons.append(f"tags {sorted(shared)} ({tag_points:+.2f})")
        else:
            reasons.append("tags no match (+0.00)")

    # Instrumentalness proximity
    inst_weight = w.get("inst", 1.0)
    if inst_weight != 0:
        inst_proximity = 1.0 - abs(
            song.get("instrumentalness", 0.5)
            - user_prefs.get("preferred_instrumentalness", 0.5)
        )
        inst_points = round(inst_weight * inst_proximity, 2)
        score += inst_points
        reasons.append(
            f"instrumentalness {song.get('instrumentalness', 0.5)} vs "
            f"{user_prefs.get('preferred_instrumentalness', 0.5)} ({inst_points:+.2f})"
        )

    # Liveness proximity
    live_weight = w.get("live", 1.0)
    if live_weight != 0:
        live_proximity = 1.0 - abs(
            song.get("liveness", 0.1) - user_prefs.get("preferred_liveness", 0.1)
        )
        live_points = round(live_weight * live_proximity, 2)
        score += live_points
        reasons.append(
            f"liveness {song.get('liveness', 0.1)} vs "
            f"{user_prefs.get('preferred_liveness', 0.1)} ({live_points:+.2f})"
        )

    return round(score, 2), reasons


class ScoringStrategy:
    """
    Base class for all scoring strategies.

    Each subclass defines a WEIGHTS dict and a name/description.
    Calling score() delegates to _weighted_score() with those weights.
    To create a new strategy, subclass this, set WEIGHTS, name, and description.
    """
    name: str = "base"
    description: str = ""
    WEIGHTS: Dict = {}

    def score(self, user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
        return _weighted_score(user_prefs, song, self.WEIGHTS)


class VibeMatchStrategy(ScoringStrategy):
    """
    Balanced mode — all signals contribute equally.
    Genre and mood are modest bonuses; energy is doubled; all advanced
    features (popularity, decade, tags, instrumentalness, liveness) count.
    Max score ≈ 10.5
    """
    name = "vibe_match"
    description = "Balanced: all signals matter equally."
    WEIGHTS = {
        "genre":        1.0,
        "mood":         1.0,
        "energy":       2.0,   # 0–2.0
        "popularity":   1.0,
        "decade":       1.0,
        "tag_per_match": 0.5,
        "tag_cap":      1.5,
        "inst":         1.0,
        "live":         1.0,
    }


class GenreFirstStrategy(ScoringStrategy):
    """
    Genre is the primary filter — everything else is a tiebreaker.
    Songs outside the user's genre almost never surface.
    Max score ≈ 8.25
    """
    name = "genre_first"
    description = "Genre dominates. Mood and energy are tiebreakers."
    WEIGHTS = {
        "genre":        4.0,   # dominant
        "mood":         0.5,
        "energy":       1.0,   # 0–1.0
        "popularity":   0.5,
        "decade":       0.5,
        "tag_per_match": 0.25,
        "tag_cap":      0.75,
        "inst":         0.5,
        "live":         0.5,
    }


class MoodFirstStrategy(ScoringStrategy):
    """
    Emotional fit comes first — genre is almost irrelevant.
    Mood tags are boosted so detailed emotional descriptors matter more.
    Great for "I just need something that feels a certain way."
    Max score ≈ 9.5
    """
    name = "mood_first"
    description = "Mood and tags dominate. Genre is nearly irrelevant."
    WEIGHTS = {
        "genre":        0.5,
        "mood":         3.0,   # dominant
        "energy":       1.0,   # 0–1.0
        "popularity":   0.5,
        "decade":       0.5,
        "tag_per_match": 1.0,  # each shared tag = +1.0
        "tag_cap":      3.0,
        "inst":         0.5,
        "live":         0.5,
    }


class EnergyFocusedStrategy(ScoringStrategy):
    """
    Pure intensity matching — genre and mood labels are ignored entirely.
    Instrumentalness and liveness are boosted because they shape the "feel"
    of intensity (a live rock song feels different from a studio EDM track
    even at the same energy level).
    Good for workouts, studying, or any context where pacing matters most.
    Max score ≈ 10.0
    """
    name = "energy_focused"
    description = "Ignores genre and mood. Only energy, instrumentalness, and liveness count."
    WEIGHTS = {
        "genre":        0.0,   # ignored
        "mood":         0.0,   # ignored
        "energy":       6.0,   # 0–6.0, dominant
        "popularity":   1.0,
        "decade":       0.0,   # ignored
        "tag_per_match": 0.0,  # ignored
        "tag_cap":      0.0,
        "inst":         1.5,
        "live":         1.5,
    }


class DiscoveryModeStrategy(ScoringStrategy):
    """
    Actively breaks filter bubbles.
    A genre match COSTS 2 points — the system pushes you out of your comfort zone.
    Mood tags are heavily rewarded so cross-genre songs that share your emotional
    vocabulary still surface. Popularity is doubled to help you find hidden gems
    (set preferred_popularity low to favour underground tracks).
    Max score ≈ 11.0 (excluding genre penalty)
    """
    name = "discovery"
    description = "Genre match is penalised. Cross-genre emotional and energy fits win."
    WEIGHTS = {
        "genre":        -2.0,  # penalty for staying in comfort zone
        "mood":          2.0,
        "energy":        1.5,  # 0–1.5
        "popularity":    2.0,  # doubled — set preferred_popularity low for hidden gems
        "decade":        0.0,  # era doesn't matter in discovery mode
        "tag_per_match": 1.5,  # strong tag bonus to surface cross-genre emotional matches
        "tag_cap":       4.5,
        "inst":          0.5,
        "live":          0.5,
    }


# Registry — import this in main.py to switch modes by name
STRATEGIES: Dict[str, ScoringStrategy] = {
    s.name: s
    for s in [
        VibeMatchStrategy(),
        GenreFirstStrategy(),
        MoodFirstStrategy(),
        EnergyFocusedStrategy(),
        DiscoveryModeStrategy(),
    ]
}


# ---------------------------------------------------------------------------
# Recommender class
# ---------------------------------------------------------------------------

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py

    Pass a ScoringStrategy instance (or a name from STRATEGIES) to switch modes:
        Recommender(songs, strategy=STRATEGIES["mood_first"])
        Recommender(songs, strategy=MoodFirstStrategy())
    Defaults to VibeMatchStrategy when no strategy is given.
    """
    def __init__(self, songs: List[Song], strategy: Optional[ScoringStrategy] = None):
        self.songs = songs
        self.strategy: ScoringStrategy = strategy or VibeMatchStrategy()

    def set_strategy(self, strategy: ScoringStrategy) -> None:
        """Swap the scoring strategy without rebuilding the Recommender."""
        self.strategy = strategy

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects ranked by the current strategy."""
        from dataclasses import asdict
        user_prefs = asdict(user)
        return sorted(
            self.songs,
            key=lambda song: self.strategy.score(user_prefs, asdict(song))[0],
            reverse=True,
        )[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation using the current strategy."""
        from dataclasses import asdict
        _, reasons = self.strategy.score(asdict(user), asdict(song))
        return ", ".join(reasons)


# ---------------------------------------------------------------------------
# Module-level helpers (backward-compatible, used by recommend_songs & tests)
# ---------------------------------------------------------------------------

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Score one song against a user profile using VibeMatch (balanced) weights.
    Preserved for backward compatibility — Recommender and tests call this via
    the default strategy path.
    """
    return _weighted_score(user_prefs, song, VibeMatchStrategy.WEIGHTS)


def load_songs(csv_path: str) -> List[Dict]:
    """Read a CSV file of songs and return a list of dicts with numeric fields cast."""
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


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    strategy: Optional[ScoringStrategy] = None,
) -> List[Tuple[Dict, float, str]]:
    """
    Score every song and return the top k as (song, score, explanation) tuples.
    Pass a strategy= to override the default VibeMatchStrategy.
    """
    active = strategy or VibeMatchStrategy()
    scored = [(song, *active.score(user_prefs, song)) for song in songs]
    ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    return [
        (song, score, ", ".join(reasons))
        for song, score, reasons in ranked[:k]
    ]
