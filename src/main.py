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

    profiles = {
        # Wants mainstream pop right now, summery and upbeat, 2020s sound, very vocal
        "High-Energy Pop": {
            "favorite_genre":           "pop",
            "favorite_mood":            "happy",
            "target_energy":            0.85,
            "likes_acoustic":           False,
            "preferred_popularity":     80,
            "preferred_decade":         2020,
            "preferred_mood_tags":      ["upbeat", "carefree", "summery"],
            "preferred_instrumentalness": 0.10,
            "preferred_liveness":       0.10,
        },
        # Underground lofi listener, ambient+focused tags, instrumental, studio recordings
        "Chill Lofi": {
            "favorite_genre":           "lofi",
            "favorite_mood":            "chill",
            "target_energy":            0.40,
            "likes_acoustic":           True,
            "preferred_popularity":     55,
            "preferred_decade":         2020,
            "preferred_mood_tags":      ["calm", "focused", "ambient"],
            "preferred_instrumentalness": 0.85,
            "preferred_liveness":       0.05,
        },
        # Wants intense rock, likes older decades (2010s), live feel, driving/anthemic tags
        "Deep Intense Rock": {
            "favorite_genre":           "rock",
            "favorite_mood":            "intense",
            "target_energy":            0.90,
            "likes_acoustic":           False,
            "preferred_popularity":     70,
            "preferred_decade":         2010,
            "preferred_mood_tags":      ["aggressive", "anthemic", "driving"],
            "preferred_instrumentalness": 0.20,
            "preferred_liveness":       0.40,
        },
    }

    # --- Adversarial / Edge-Case Profiles ---
    # Each profile is designed to stress-test a specific weakness in the scoring logic.
    adversarial_profiles = {
        # 1. Conflicted Emotion: sad mood but wants high energy.
        #    Does genre+mood override the glaring energy mismatch?
        #    "3AM Rain" (blues/sad/0.33) gets genre+mood but terrible energy proximity.
        "Sad but Pumped (conflicted mood/energy)": {
            "favorite_genre": "blues",
            "favorite_mood":  "sad",
            "target_energy":  0.9,
            "likes_acoustic": False,
        },
        # 2. Ghost Genre: "metal" doesn't exist in the catalog.
        #    With zero genre matches, everything competes on mood+energy alone — max score is 2.0.
        #    Reveals the genre-bonus dominance when it's entirely absent.
        "Ghost Genre (no catalog match for 'metal')": {
            "favorite_genre": "metal",
            "favorite_mood":  "intense",
            "target_energy":  0.92,
            "likes_acoustic": False,
        },
        # 3. Out-of-Bounds Energy: target_energy=1.5 is outside [0, 1].
        #    energy_points = 1.0 - abs(song_energy - 1.5) goes NEGATIVE for low-energy songs.
        #    Low-energy songs are actively penalized; scores can drop below their mood/genre bonuses.
        "Out-of-Bounds Energy (target=1.5)": {
            "favorite_genre": "edm",
            "favorite_mood":  "euphoric",
            "target_energy":  1.5,
            "likes_acoustic": False,
        },
        # 4. Acoustic Blindspot: likes_acoustic=True but the field is never read by score_song().
        #    Highly electronic songs may rank above acoustic ones even though the user said otherwise.
        "Acoustic Blindspot (likes_acoustic=True, but ignored)": {
            "favorite_genre": "classical",
            "favorite_mood":  "peaceful",
            "target_energy":  0.1,
            "likes_acoustic": True,
        },
        # 5. Mood-Genre Mismatch: the only hip-hop song ("Golden Hour Drive") has mood "energetic",
        #    not "chill". Genre bonus fires, but mood bonus never will — can mood+energy on non-hip-hop
        #    songs beat a genre-only match?
        "Mood-Genre Mismatch (no hip-hop/chill song exists)": {
            "favorite_genre": "hip-hop",
            "favorite_mood":  "chill",
            "target_energy":  0.5,
            "likes_acoustic": False,
        },
    }

  
    for label, user_prefs in adversarial_profiles.items():
        recommendations = recommend_songs(user_prefs, songs, k=5)
        
        print(f"Profile: genre={user_prefs['favorite_genre']}  mood={user_prefs['favorite_mood']}  energy={user_prefs['target_energy']}\n")
        print(f"{'#':<3} {'Title':<25} {'Artist':<20} {'Score':>5}")
        print("-" * 57)
        for rank, (song, score, explanation) in enumerate(recommendations, start=1):
            print(f"{rank:<3} {song['title']:<25} {song['artist']:<20} {score:>5.2f}")
            print(f"    Why: {explanation}")
            print()

    for label, user_prefs in profiles.items():
        recommendations = recommend_songs(user_prefs, songs, k=5)
        
        print(f"Profile: genre={user_prefs['favorite_genre']}  mood={user_prefs['favorite_mood']}  energy={user_prefs['target_energy']}\n")
        print(f"{'#':<3} {'Title':<25} {'Artist':<20} {'Score':>5}")
        print("-" * 57)
        for rank, (song, score, explanation) in enumerate(recommendations, start=1):
            print(f"{rank:<3} {song['title']:<25} {song['artist']:<20} {score:>5.2f}")
            print(f"    Why: {explanation}")
            print()


if __name__ == "__main__":
    main()
