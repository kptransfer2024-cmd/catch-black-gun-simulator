# Model Overview: Catch-the-Black-Gun Simulator

All models simulate the same game: 54 cards dealt 18 each to three players. Player 0 always holds the Ace of Spades (the "black gun"). The research question is whether P0 wins at the expected 1/3 rate or whether holding the Ace creates a structural bias.

Each model represents all three players using the **same policy** (except Models 4 and 5, where P1 and P2 deliberately differ from P0). A single fixed random seed of 2026 and 100,000 games per experiment are used for reproducibility and statistical power.

---

## Model 0 — Random Policy
**File:** `agents/random_policy.py`
**Result:** P0 win rate ~34.9%, p < 0.001 (significant)

Every player chooses uniformly at random from all legal moves on each turn. No strategy, no structure awareness. This is the pure baseline — it measures whether card distribution alone creates any bias before any decision-making is introduced.

The significant result here is a **policy artifact**: the first player (holder of 3♥) plays first and often plays a single, which interacts with P0's hand composition in a way that inflates P0's apparent win rate. It is not a true structural advantage.

---

## Model 1 — Heuristic Policy
**File:** `agents/heuristic_policy.py`
**Result:** P0 win rate ~39.9%, p < 0.001 (significant)

A simple deterministic rule: if the hand has 5 or fewer cards, play the combo that uses the most cards (finish fast). Otherwise, always play the lowest-rank legal non-bomb move, and pass if none exists.

This model was intended to represent rational play, but the "always play the lowest card" rule causes players to lead singles excessively. This creates an even stronger first-player bias than Model 0, pushing P0's win rate further above 1/3. The significance here is again a policy artifact — the heuristic is too unsophisticated to isolate structural effects.

---

## Model 2 — Combo-Aware Policy
**File:** `agents/combo_policy.py`
**Result:** P0 win rate ~33.4%, p = 0.636 (not significant) | Avg turns: ~29

The first model that plays like a real card player. Key behaviors:

- **Lead priority**: prefers straights and consecutive pairs over triples and pairs, never leads singles if a structured combo is available
- **Maximal sequences**: only leads the longest possible straight or consecutive pair run — never splits a run into shorter sub-sequences
- **Structure protection**: identifies cards that belong to valuable structures (triple cores, straights ≥ 5 cards, consecutive pair runs ≥ 3 pairs, high standalone pairs vs weak tricks) and refuses to break them when following
- **Bomb conservation**: never plays a bomb unless no other legal move exists

This model removes the policy artifacts from Models 0 and 1. The result is the first fair measurement: P0 wins at essentially 1/3, and the null hypothesis holds. The Ace of Spades carries no structural advantage under symmetric rational play.

Avg turns drop dramatically (~29 vs ~50) because players now play combos instead of singles, emptying hands far more efficiently.

---

## Model 3 — Tactical Policy
**File:** `agents/tactical_policy.py`
**Result:** P0 win rate ~33.2%, p = 0.362 (not significant) | Avg turns: ~32

Extends Model 2 with two tactical refinements:

- **Smart kicker selection**: when leading a triple+kicker or triple+pair combo, prefers to use unprotected cards as the kicker rather than cards that belong to another valuable structure (e.g. don't use a straight card as a kicker). This avoids accidentally destroying a structure just to complete a triple lead.
- **Danger mode**: when any opponent has 3 or fewer cards remaining, the player drops all protection logic and plays the largest available combo, including bombs, to try to finish before the opponent wins.

P0's win rate remains near 1/3, confirming the null hypothesis holds under more sophisticated play. The avg turns are slightly higher than Model 2 (~32 vs ~29) because smarter protection means more passes in normal play, partially offset by danger mode accelerating endgames.

Also introduces `opponent_hand_sizes` passing from the engine to all policies — each player now knows how many cards each opponent holds on every turn.

---

## Model 4 — Coalition Policy (Basic)
**File:** `agents/coalition_policy.py`
**Result:** P0 win rate ~29%, p < 0.05 (significant) | Avg turns: ~33

The first **asymmetric** model: P0 still plays like Model 3, but P1 and P2 have a coalition-aware policy. The coalition activates only **after P0 plays the Ace of Spades** — before that reveal, P1 and P2 also behave like Model 3.

Once the Ace is revealed, P1 and P2 enter coalition mode with three behaviors:

- **Partner passing**: when the coalition partner (the other non-P0 player) currently holds the trick, pass unconditionally to let them keep the lead
- **Aggressive P0 blocking**: when P0 holds the trick, beat P0 with the minimum card regardless of protection — unlike normal play, protected structures are ignored in order to deny P0 control. Bombs are used if P0's move cannot be beaten otherwise.
- **Finish fast override**: if P0 has 3 or fewer cards, or own hand has 5 or fewer cards, immediately play the largest available combo (including bombs)

This is the first model to show a meaningful drop in P0's win rate below 1/3, confirming that coalition dynamics — not card composition — are the primary driver of P0's disadvantage in real games.

---

## Model 5 — Coalition Refined Policy
**File:** `agents/coalition_refined_policy.py`
**Result:** TBD (100K run pending) | Avg turns: ~33

Extends Model 4 with three refinements that reflect how experienced players actually coordinate:

- **Priority protocol**: at any point during the game, whichever coalition member has fewer cards is the "winner candidate" (priority player) and plays to finish; the other becomes the "sacrificer" and plays purely to support. Roles swap dynamically as hand sizes change.

- **Tempo transfer**: the sacrificer, when leading freely, leads the cheapest available unprotected single instead of a structured combo. The goal is to offer a weak trick that the partner can easily beat, transferring the lead to the partner so they can control the next sequence of plays.

- **Selective coalition bombing**: the sacrificer, who has no interest in preserving their own hand quality, uses bombs immediately against P0's moves without waiting for a situation where only a bomb can respond. The priority player also deploys bombs against P0 when P0 has 4 or fewer cards remaining — at that point bomb conservation matters less than denying P0 any more leads.

The priority/sacrificer split means the coalition is no longer symmetric: one player is aggressively trying to win while the other is purely a blocker, which more closely mirrors how real players divide responsibilities in this game.

---

## Summary Table

| Model | Policy | BG Win Rate | p-value | Avg Turns | Notes |
|---|---|---|---|---|---|
| 0 | Random | ~34.9% | < 0.001 | ~47 | Artifact from first-player bias |
| 1 | Heuristic | ~39.9% | < 0.001 | ~52 | Artifact from excessive single play |
| 2 | Combo-Aware | ~33.4% | 0.636 | ~29 | First fair measurement; null holds |
| 3 | Tactical | ~33.2% | 0.362 | ~32 | Null holds under smarter play |
| 4 | Coalition (Basic) | ~29% | < 0.05 | ~33 | Coalition activates on Ace reveal |
| 5 | Coalition Refined | TBD | TBD | ~33 | Priority + tempo + selective bombs |

**Conclusion so far:** Under symmetric play (Models 2–3), holding the Ace of Spades conveys no structural advantage — P0 wins at 1/3. The disadvantage emerges only when P1 and P2 coordinate against P0 (Models 4–5), which reflects real-game social dynamics rather than card composition.
