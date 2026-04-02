# 🎧 Model Card: Music Recommender Simulation

---

## 1. Model Name

**VibeMatch 1.0**

---

## 2. Goal / Task

VibeMatch suggests songs based on what kind of music you are in the mood for right now.

You tell it your favorite genre, your current mood, and how energetic you want the music to feel. It scores every song in the catalog and returns the top 5 that fit your preferences best.

This is a classroom simulation. It is not connected to any real music service and is not designed for real users.

---

## 3. Algorithm Summary

Every song starts at zero points. Then three questions get asked:

**Does the genre match?** If the song's genre matches your favorite genre, it earns 1 point. Genre is a basic filter — it is the system's first guess at whether a song even belongs in your world.

**Does the mood match?** If the song's mood matches the mood you told the system you are in, it earns 1 more point. Mood matters, but it is softer than genre — the same emotional feel shows up across many styles.

**How close is the energy?** Energy is a number from 0 (very calm) to 1 (very intense). The system measures how far the song's energy is from your target, and gives up to 2 points for a close match. A perfect match earns the full 2 points. A song that is 0.5 away earns 1 point. A song that is 1.0 away earns 0.

Add those three numbers together and you get the song's score. The highest possible score is 4.0, which means genre, mood, and energy all matched perfectly. The top 5 scores win.

---

## 4. Data Used

The catalog has 18 songs stored in a CSV file.

Each song has: title, artist, genre, mood, energy (0–1), tempo in BPM, valence (0–1), danceability (0–1), and acousticness (0–1).

There are 15 different genres represented. Lofi has 3 songs. Pop has 2 songs. Every other genre has exactly 1 song.

There are 14 different moods represented, including happy, chill, intense, sad, euphoric, romantic, and peaceful.

The catalog skews toward genres that are popular in online study and productivity playlists. Styles like country, reggae, blues, and classical have only one song each. No songs have explicit lyrics, aggressive themes, or non-English content. The dataset reflects a narrow slice of what music actually looks like in the world.

No songs were added or removed from the original starter dataset.

---

## 5. Strengths

The system works best when your preferences are well-represented in the catalog.

A lofi/chill user at energy 0.4 gets three lofi tracks in the top three, all matching mood. A rock/intense user at energy 0.9 gets Storm Runner as a near-perfect 3.99 out of 4.0.

The scoring is fully transparent. Every recommendation comes with a clear reason showing exactly how many points each song earned and why. There are no hidden factors.

It is also fast. Since the catalog is small and the math is simple, results are instant and easy to trace.

---

## 6. Observed Behavior / Biases

**Genre locks out mood.** A song called "Gym Hero" (pop, intense, energy 0.93) keeps ranking second for users who ask for happy pop. The system rewards a genre match regardless of whether the song's mood fits. It has no way to penalize a mood mismatch — it only rewards a mood hit. So an intense gym track beats a happy indie pop song just because both are labeled "pop."

**Single-song genres create dead ends.** Thirteen of eighteen genres have exactly one song. If you prefer jazz, reggae, blues, or classical, you get one genre-boosted result and then four fallback songs ranked by energy alone. The catalog is too small to serve most genres fairly.

**`likes_acoustic` is collected but ignored.** Users can set an acoustic preference, but the scoring function never reads it. Acoustic and electronic fans get identical recommendations.

**Energy scoring has no floor.** If a user accidentally enters a target energy above 1.0, the formula produces negative energy scores for calm songs, actively punishing them rather than just ranking them lower.

**Calm users get less variety.** Low-energy songs cluster in the 0.22–0.42 range. A user targeting 0.1 energy gets 5 songs that are all similarly quiet but span totally different genres and moods. Energy proximity becomes the only meaningful signal.

---

## 7. Evaluation Process

Eight user profiles were tested: three standard and five adversarial.

**Standard profiles** confirmed basic behavior. Lofi/chill worked well. Rock/intense worked well. Pop/happy mostly worked, except Gym Hero ranked second despite having the wrong mood.

**Adversarial profiles** each targeted a specific weakness:

- *Sad but Pumped* (blues, sad, energy=0.9): The system recommended a slow sad song to a user who asked for high energy. The genre + mood bonus was strong enough to win even with a 0.57 energy gap.
- *Ghost Genre* (metal): No catalog song matched. The system silently fell back to mood + energy with no warning and no score above 2.0.
- *Out-of-Bounds Energy* (target=1.5): Low-energy songs received negative energy scores. The formula has no input validation.
- *Acoustic Blindspot* (classical, likes_acoustic=True): An electronic synthwave track ranked second. The acoustic preference was completely ignored.
- *Mood-Genre Mismatch* (hip-hop, mood=chill): The only hip-hop song has mood "energetic." It still won under original weights because the genre bonus beat three lofi/chill songs that actually matched the user's stated mood.

A weight-shift experiment was also run: genre bonus was halved to 1.0 and energy weight was doubled to a max of 2.0. The max score stayed at 4.0. The most meaningful change was the Mood-Genre Mismatch case — lofi/chill songs finally outranked the hip-hop track with the wrong mood. In most other cases only the gap between ranks changed, not the top result.

---

## 8. Intended Use and Non-Intended Use

**Intended use:**
This system is designed for a classroom simulation to explore how music recommenders work. It is a learning tool. It shows how preferences can be turned into a score and how that score creates a ranked list.

**Not intended for:**
- Real music apps or production use
- Users with diverse or complex taste (it can only handle one genre and one mood at a time)
- Any situation where accuracy, fairness, or personalization actually matters
- Recommending music to people with moods or genres not covered in the 18-song catalog

---

## 9. Ideas for Improvement

**1. Penalize mood mismatches, not just reward matches.**
Right now the system only gives a point when mood matches. If a song's mood is the opposite of what the user asked for (like intense vs. happy), that should cost points. This would stop "Gym Hero" from appearing in every happy pop list.

**2. Use acousticness to honor the `likes_acoustic` preference.**
The field is already collected and stored. A simple rule — give a bonus when a user prefers acoustic and the song's acousticness score is above 0.7 — would make the preference actually mean something.

**3. Expand the catalog and balance genre representation.**
Thirteen genres have only one song each. Adding three to five songs per genre would give the system enough variety to return meaningfully different top-5 lists instead of recycling the same small pool. It would also reduce the advantage that lofi and pop users get just by having more songs to choose from.

---

## 10. Personal Reflection

The biggest learning moment for me was when I ran the "Sad but Pumped" profile — a user who says they want blues music, they're feeling sad, but they want high energy. I expected the system to struggle with that. What I didn't expect was how confidently it came back with a slow, quiet song and basically said "yep, this is your best match." It wasn't wrong by its own rules. The math checked out. But it felt completely wrong as a recommendation. That was the moment I understood what bias in an algorithm actually means in practice. It's not always the system doing something broken — sometimes it's doing exactly what you told it to do, and the problem is that what you told it to do was too simple for the real world.

Using AI tools helped me move faster through the analysis and catch patterns I might have missed on my own, like noticing that 13 of 18 genres have only one song or that `likes_acoustic` was being collected but never used. That second one especially — I had written the field into the data structure myself, but without the comparison across profiles I might not have noticed it was just sitting there doing nothing. Where I needed to double-check was any time the AI described what the code "would do" in a specific case. I always ran it myself to confirm, because explanations of behavior and actual behavior are not always the same thing. The out-of-bounds energy case was a good example of that — the idea that scores could go negative wasn't obvious until I actually saw the numbers.

What surprised me most was how much the results "felt" like recommendations even though the whole algorithm is just three if-statements and some subtraction. When the lofi/chill profile returned Midnight Coding and Library Rain at the top, it genuinely felt right — like it understood something. But it didn't. It just matched a string and did some arithmetic. That gap between "feels smart" and "is smart" is something I'll think about whenever I use a recommendation feature on a real app now. I'll wonder how much of it is actually learning about me versus just pattern-matching on a label I gave it once.

If I kept working on this, the first thing I'd try is adding a penalty for mood mismatch instead of only rewarding a match. Right now the scoring can only go up — nothing makes a score go down except energy distance. Letting a wrong mood cost points would make the recommendations feel a lot more honest. After that I'd want to try using valence and danceability in the score, because those are already in the dataset and they carry real information about whether a song fits a moment. A song can be "chill" by label but still have a high danceability score, and right now the system can't tell the difference.
