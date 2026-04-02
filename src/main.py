"""
Command line runner for the Music Recommender Simulation.

Run with:  python -m src.main
"""

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
# Helpers
# ---------------------------------------------------------------------------

def _divider(char: str = "-", width: int = 62) -> str:
    return char * width


def _print_results(
    user_prefs: dict,
    songs: list,
    strategy_key: str = "vibe_match",
) -> None:
    strategy = STRATEGIES[strategy_key]
    results = recommend_songs(user_prefs, songs, k=5, strategy=strategy)

    print(f"\n  [{strategy.name}]  {strategy.description}")
    print(f"  {'#':<3} {'Title':<25} {'Artist':<20} {'Score':>6}")
    print(f"  {_divider()}")
    for rank, (song, score, explanation) in enumerate(results, start=1):
        print(f"  {rank:<3} {song['title']:<25} {song['artist']:<20} {score:>6.2f}")
        print(f"      Why: {explanation}")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded {len(songs)} songs.\n")

    # ------------------------------------------------------------------
    # Section 1 — Standard profiles, default VibeMatch strategy
    # ------------------------------------------------------------------
    print(_divider("="))
    print("SECTION 1 — STANDARD PROFILES  (strategy: vibe_match)")
    print(_divider("="))

    for label, user_prefs in PROFILES.items():
        print(f"\n>>> {label}")
        print(
            f"    genre={user_prefs['favorite_genre']}  "
            f"mood={user_prefs['favorite_mood']}  "
            f"energy={user_prefs['target_energy']}"
        )
        _print_results(user_prefs, songs, strategy_key="vibe_match")

    # ------------------------------------------------------------------
    # Section 2 — Strategy comparison on one profile
    #
    # We run the same "Chill Lofi" user through every strategy so you can
    # see exactly how the ranking shifts when the priorities change.
    # ------------------------------------------------------------------
    print("\n" + _divider("="))
    print("SECTION 2 — STRATEGY COMPARISON  (profile: Chill Lofi)")
    print(_divider("="))
    print(
        "\nSame user, five different scoring modes.\n"
        "Watch how the top-5 list changes as priorities shift.\n"
    )

    demo_profile = PROFILES["Chill Lofi"]
    print(
        f"Profile: genre={demo_profile['favorite_genre']}  "
        f"mood={demo_profile['favorite_mood']}  "
        f"energy={demo_profile['target_energy']}  "
        f"tags={demo_profile['preferred_mood_tags']}\n"
    )

    for strategy_key in STRATEGIES:
        _print_results(demo_profile, songs, strategy_key=strategy_key)
        print(_divider("-"))

    # ------------------------------------------------------------------
    # Section 3 — Diversity Penalty: before vs. after
    #
    # The Chill Lofi profile exposes the problem clearly:
    #   - LoRoom appears twice (Midnight Coding + Focus Flow)
    #   - The lofi genre fills three of five slots
    # With diversity ON, repeated artists and genres are penalised so the
    # list opens up to songs from other genres that still fit the mood.
    #
    # Penalty values (tunable):
    #   artist_penalty = 1.5 pts per prior occurrence of the same artist
    #   genre_penalty  = 0.75 pts per prior occurrence of the same genre
    # ------------------------------------------------------------------
    print("\n" + _divider("="))
    print("SECTION 3 — DIVERSITY PENALTY  (profile: Chill Lofi)")
    print(_divider("="))
    print(
        "\nartist_penalty=1.5 pts per repeat  |  genre_penalty=0.75 pts per repeat\n"
    )

    for label, diversity_on in [("WITHOUT diversity penalty", False),
                                 ("WITH diversity penalty", True)]:
        results = recommend_songs(
            demo_profile, songs, k=5,
            strategy=STRATEGIES["vibe_match"],
            diversity=diversity_on,
            artist_penalty=1.5,
            genre_penalty=0.75,
        )
        print(f"  --- {label} ---")
        print(f"  {'#':<3} {'Title':<25} {'Artist':<20} {'Genre':<12} {'Score':>6}")
        print(f"  {_divider()}")
        for rank, (song, score, explanation) in enumerate(results, start=1):
            print(
                f"  {rank:<3} {song['title']:<25} {song['artist']:<20}"
                f" {song['genre']:<12} {score:>6.2f}"
            )
            if diversity_on and "diversity penalty" in explanation:
                penalty_note = explanation.split("||")[1].strip()
                print(f"      {penalty_note}")
        print()


if __name__ == "__main__":
    main()
