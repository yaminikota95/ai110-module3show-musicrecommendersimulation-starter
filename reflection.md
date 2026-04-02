# Reflection: Profile Comparisons

## Why "Gym Hero" keeps showing up for Happy Pop users

Imagine you walk into a record store and tell the clerk: "I love pop music, and I'm in a happy mood today."
The clerk looks at the pop section and hands you two records: "Sunrise City" (upbeat, cheerful) and "Gym Hero" (loud, aggressive gym pump-up track). Both are labeled pop, so both get handed to you.

That is exactly what this recommender does. It checks whether the genre label matches and gives a point if it does — but it has no rule for *penalizing* a song whose mood is the opposite of what you asked for. "Gym Hero" is pop, so it scores well. The fact that it is intense and you said happy never costs it anything. The system rewards hits but never punishes misses.

---

## Pair 1: High-Energy Pop vs. Mood-Genre Mismatch (hip-hop / chill)

**High-Energy Pop** (genre=pop, mood=happy, energy=0.85)
→ Top result: Sunrise City (pop/happy/0.82) at 3.97. Strong match across all three signals.

**Mood-Genre Mismatch** (genre=hip-hop, mood=chill, energy=0.5)
→ Top result under original weights: Golden Hour Drive (hip-hop/energetic/0.78) at 2.72 — despite its mood being "energetic," not "chill."

**What changed and why it makes sense:**
The pop user got lucky — their genre has two songs and one of them happens to match their mood too. The hip-hop user was not so lucky: the catalog only has one hip-hop song, and it has the wrong mood. The genre bonus still fired and pushed that song to the top, completely overriding the mood preference the user stated. This is the filter bubble in action: the system locks onto the genre label and stops caring whether the song actually fits how the user feels. After the weight-shift experiment (genre halved, energy doubled), three lofi/chill songs outranked the hip-hop track — the first time the system gave the hip-hop user songs that matched their stated mood, even though none of them were hip-hop.

---

## Pair 2: Deep Intense Rock vs. Sad but Pumped (blues / sad / energy=0.9)

**Deep Intense Rock** (genre=rock, mood=intense, energy=0.9)
→ Top result: Storm Runner (rock/intense/0.91) at 3.99. Genre, mood, and energy all align.

**Sad but Pumped** (genre=blues, mood=sad, energy=0.9)
→ Top result: 3AM Rain (blues/sad/0.33) at 3.43. Genre and mood match, but energy is 0.57 off.

**What changed and why it makes sense:**
Both profiles want high-energy music (0.9). The rock user gets it — Storm Runner is actually a high-energy track. The blues user asks for the same intensity, but the only blues song in the catalog is slow and quiet (0.33 energy). The system still recommends it, confidently, because genre + mood together earn more points than the energy penalty costs. A real music app would flag this conflict: "We found a blues/sad song but it doesn't match your energy level — want something else?" This system has no such check. The genre + mood bonus is so strong that the recommender can look at a slow blues song and tell you it is the best match for your high-energy request.

---

## Pair 3: Ghost Genre (metal / intense) vs. Deep Intense Rock

**Ghost Genre** (genre=metal, mood=intense, energy=0.92)
→ Top result: Storm Runner (rock/intense/0.91) at 1.99. No genre match possible.

**Deep Intense Rock** (genre=rock, mood=intense, energy=0.9)
→ Top result: Storm Runner (rock/intense/0.91) at 3.99. Genre + mood + energy all match.

**What changed and why it makes sense:**
Same song ends up at the top for both profiles, but the score is almost exactly half (1.99 vs 3.99). The metal user and the rock user end up with identical top-5 lists — the system just quietly drops the genre bonus and keeps going. This reveals a silent failure mode: if your favorite genre does not exist in the catalog, the system gives you no warning and no different behavior. It simply pretends genre does not matter and falls back to mood + energy. A better system would at least tell the user: "No metal songs found — showing closest matches by mood and energy instead." The identical recommendations also show that Storm Runner is basically the system's default for anyone who wants intense, high-energy music regardless of genre.

---

## Pair 4: Chill Lofi vs. Acoustic Blindspot (classical / peaceful / energy=0.1)

**Chill Lofi** (genre=lofi, mood=chill, energy=0.4, likes_acoustic=True)
→ Top results: three lofi/chill songs in the top three. The acoustic preference had no effect.

**Acoustic Blindspot** (genre=classical, mood=peaceful, energy=0.1, likes_acoustic=True)
→ Top results: Glass Cathedral at #1, then Spacewalk Thoughts (synthwave/electronic), Hollow Mountain (folk), 3AM Rain (blues), Library Rain (lofi). The acoustic preference had no effect.

**What changed and why it makes sense:**
Both profiles set `likes_acoustic=True`. Neither got any benefit from that setting because the scoring function never reads it. The Acoustic Blindspot profile is the clearest example of the problem: the user is asking for calm, acoustic classical music, and rank #2 is a synthwave track (acousticness=0.22, nearly fully electronic). In real life, someone who wants peaceful classical would never want synthwave. But since the system only compares energy levels (both are low-energy), synthwave looks just as good as a folk or classical song. The `likes_acoustic` field is described in the user preferences, shown in output, and completely ignored — a gap between what the system appears to offer and what it actually does.

---

## Pair 5: Out-of-Bounds Energy (target=1.5) vs. High-Energy Pop (target=0.85)

**High-Energy Pop** (genre=pop, mood=happy, energy=0.85)
→ Energy scores range from 1.94 (Sunrise City) down to reasonable values. All positive.

**Out-of-Bounds Energy** (genre=edm, mood=euphoric, energy=1.5)
→ Pulse Grid at #1 with score 2.92, but rank #2 drops to 0.86. Low-energy songs would score *negative* on energy.

**What changed and why it makes sense:**
Energy is supposed to be a number from 0 to 1. The system does not check whether the user's target falls in that range. When someone enters 1.5, the formula `2 × (1 - |song_energy - 1.5|)` produces negative values for any song with energy below 0.5. Glass Cathedral (energy 0.22) would score -0.56 on energy alone — it gets actively penalized rather than just ranked lower. The practical effect is that the scoring penalizes calm songs twice: once because they are far from the target, and again because the math goes below zero. A real app would either clamp the user's input to [0, 1] or at least floor the energy score at 0. This is a math validation gap — the formula assumes well-behaved inputs but has no guard against inputs that break its assumptions.
