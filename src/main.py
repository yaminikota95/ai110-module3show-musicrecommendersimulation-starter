"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Taste profile: target values used to score each song
    # favorite_genre   — preferred style; songs matching this get a genre bonus
    # favorite_mood    — emotional tone the user wants right now; highest-weighted signal
    # target_energy    — desired intensity on a 0.0 (calm) to 1.0 (intense) scale
    # likes_acoustic   — True rewards acoustic tracks; False rewards electronic ones
    user_prefs = {
        "favorite_genre": "pop",
        "favorite_mood":  "happy",
        "target_energy":  0.80,
        "likes_acoustic": False,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print(f"\nProfile: genre={user_prefs['favorite_genre']}  mood={user_prefs['favorite_mood']}  energy={user_prefs['target_energy']}\n")
    print(f"{'#':<3} {'Title':<25} {'Artist':<20} {'Score':>5}")
    print("-" * 57)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank:<3} {song['title']:<25} {song['artist']:<20} {score:>5.2f}")
        print(f"    Why: {explanation}")
        print()


if __name__ == "__main__":
    main()
