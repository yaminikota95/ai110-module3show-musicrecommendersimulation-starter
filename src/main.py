"""
Command line runner for the Music Recommender Simulation.

Run with:  python -m src.main
"""

import re
from tabulate import tabulate

from .recommender import load_songs, recommend_songs, STRATEGIES


# ---------------------------------------------------------------------------
# Shared user profiles
# ---------------------------------------------------------------------------

PROFILES = {
    # Wants mainstream pop right now, summery and upbeat, 2020s sound, very vocal
    "High-Energy Pop": {
        "favorite_genre":             "pop",
        "favorite_mood":              "happy",
        "target_energy":              0.85,
        "likes_acoustic":             False,
        "preferred_popularity":       80,
        "preferred_decade":           2020,
        "preferred_mood_tags":        ["upbeat", "carefree", "summery"],
        "preferred_instrumentalness": 0.10,
        "preferred_liveness":         0.10,
    },
    # Underground lofi listener, ambient+focused tags, instrumental, studio recordings
    "Chill Lofi": {
        "favorite_genre":             "lofi",
        "favorite_mood":              "chill",
        "target_energy":              0.40,
        "likes_acoustic":             True,
        "preferred_popularity":       55,
        "preferred_decade":           2020,
        "preferred_mood_tags":        ["calm", "focused", "ambient"],
        "preferred_instrumentalness": 0.85,
        "preferred_liveness":         0.05,
    },
    # Wants intense rock, 2010s era, live feel, driving/anthemic tags
    "Deep Intense Rock": {
        "favorite_genre":             "rock",
        "favorite_mood":              "intense",
        "target_energy":              0.90,
        "likes_acoustic":             False,
        "preferred_popularity":       70,
        "preferred_decade":           2010,
        "preferred_mood_tags":        ["aggressive", "anthemic", "driving"],
        "preferred_instrumentalness": 0.20,
        "preferred_liveness":         0.40,
    },
}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _section(title: str, width: int = 72) -> None:
    """Print a bold section header."""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def _subsection(title: str, width: int = 72) -> None:
    print("\n" + "-" * width)
    print(f"  {title}")
    print("-" * width)


def _profile_summary(label: str, prefs: dict) -> str:
    tags = ", ".join(prefs.get("preferred_mood_tags") or []) or "—"
    return (
        f"  Profile : {label}\n"
        f"  Genre   : {prefs['favorite_genre']}   "
        f"Mood: {prefs['favorite_mood']}   "
        f"Energy: {prefs['target_energy']}\n"
        f"  Tags    : {tags}   "
        f"Popularity: {prefs.get('preferred_popularity', 50)}   "
        f"Decade: {prefs.get('preferred_decade', 2020)}"
    )


def _format_reasons(explanation: str) -> str:
    """
    Convert the flat comma-joined reason string into one line per signal.

    Strategy
    --------
    Every scoring reason ends with a score in parentheses, e.g. (+1.96) or
    (-0.75).  We split on the pattern  "),  " followed by a lowercase letter
    so we don't accidentally split on commas *inside* a tag list like
    "['calm', 'focused']".

    Diversity penalty notes (appended after "  ||  ") are separated out and
    prefixed with "! " so they stand out visually.
    """
    # Separate score block from optional diversity penalty block
    blocks = explanation.split("  ||  ")
    score_block = blocks[0]
    diversity_block = blocks[1] if len(blocks) > 1 else None

    # Split score reasons: match "), " only when the next char is a-z
    raw_parts = re.split(r"\), (?=[a-z])", score_block)

    # Re-attach the closing paren that the split consumed (last part keeps its own)
    reasons = [
        p + ")" if not p.endswith(")") else p
        for p in raw_parts
    ]

    lines = list(reasons)

    if diversity_block:
        # e.g. "diversity penalty: artist 'LoRoom' already seen x1 (-1.50); ..."
        notes_raw = diversity_block.replace("diversity penalty: ", "")
        for note in notes_raw.split("; "):
            lines.append(f"! {note}")

    return "\n".join(lines)


def _results_table(results: list) -> str:
    """
    Build a tabulate table string from a recommend_songs() result list.

    Columns
    -------
    #   Title   Artist   Genre   Mood   Score   Scoring Reasons
    """
    rows = []
    for rank, (song, score, explanation) in enumerate(results, start=1):
        rows.append([
            rank,
            song["title"],
            song["artist"],
            song["genre"],
            song["mood"],
            f"{score:.2f}",
            _format_reasons(explanation),
        ])

    headers = ["#", "Title", "Artist", "Genre", "Mood", "Score", "Scoring Reasons"]
    return tabulate(rows, headers=headers, tablefmt="outline")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"\nLoaded {len(songs)} songs from catalog.\n")

    # ------------------------------------------------------------------
    # Section 1 — Standard profiles, default VibeMatch strategy
    # ------------------------------------------------------------------
    _section("SECTION 1 — STANDARD PROFILES  (strategy: vibe_match)")

    for label, user_prefs in PROFILES.items():
        _subsection(label)
        print(_profile_summary(label, user_prefs))
        print()

        results = recommend_songs(
            user_prefs, songs, k=5,
            strategy=STRATEGIES["vibe_match"],
        )
        print(_results_table(results))

    # ------------------------------------------------------------------
    # Section 2 — Same profile, every strategy
    # ------------------------------------------------------------------
    _section("SECTION 2 — STRATEGY COMPARISON  (profile: Chill Lofi)")
    print(
        "\n  Same user. Five different scoring modes.\n"
        "  Watch how the top-5 shifts as priorities change.\n"
    )

    demo_profile = PROFILES["Chill Lofi"]
    print(_profile_summary("Chill Lofi", demo_profile))

    for _, strategy in STRATEGIES.items():
        print(f"\n  Strategy: [{strategy.name}]  {strategy.description}\n")
        results = recommend_songs(
            demo_profile, songs, k=5,
            strategy=strategy,
        )
        print(_results_table(results))

    # ------------------------------------------------------------------
    # Section 3 — Diversity penalty: before vs. after
    # ------------------------------------------------------------------
    _section("SECTION 3 — DIVERSITY PENALTY  (profile: Chill Lofi)")
    print(
        "\n  Without penalty: LoRoom appears twice, lofi fills 3/5 slots.\n"
        "  With penalty   : artist_penalty=1.5 pts/repeat, "
        "genre_penalty=0.75 pts/repeat.\n"
        "  Rows marked '!' show diversity deductions applied.\n"
    )
    print(_profile_summary("Chill Lofi", demo_profile))

    for label, diversity_on in [
        ("WITHOUT diversity penalty", False),
        ("WITH    diversity penalty  (artist_penalty=1.5 | genre_penalty=0.75)", True),
    ]:
        print(f"\n  --- {label} ---\n")
        results = recommend_songs(
            demo_profile, songs, k=5,
            strategy=STRATEGIES["vibe_match"],
            diversity=diversity_on,
            artist_penalty=1.5,
            genre_penalty=0.75,
        )
        print(_results_table(results))


if __name__ == "__main__":
    main()
