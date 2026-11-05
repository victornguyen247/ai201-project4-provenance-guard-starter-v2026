# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. False positives on my own writing

Of 10 paragraphs I wrote myself, at most 1 is labelled high-confidence AI — and that holds in each of three separate eval trials (`run_eval.py`).

**Why this target:**
On a writing site, wrongly accusing a real writer costs that person far more than missing some AI text costs the site. "At most 1 in 10" is strict enough to be meaningful, and requiring it across three trials accounts for the model signal's run-to-run variance instead of lucking into one clean pass.

---

## 2. Score spread between clear cases

On a fixed pair of calibration inputs — one clearly AI-generated, one clearly human-written — the combined scores differ by at least 0.30 in every trial (clearly-AI score minus clearly-human score ≥ 0.30).

**Why this target:**
If clear cases sit within a few hundredths of each other, the labels are noise and the unsure band does all the work by accident. A 0.30 gap leaves room for thresholds at 0.35 / 0.65 without the two poles collapsing into the middle.

---

## 3. All three labels are reachable

I can produce at least one successful submission for each label — high-confidence human, unsure, and high-confidence AI — in a single eval run (3 labelled responses, one of each).

**Why this target:**
A label that no score can hit is dead UI. Milestone 5 requires submitting text that lands in each band; if the style signal is still a stub or the thresholds are wrong, one of those three will be unreachable and the criterion fails for a reason I can fix.

---

## 4. Appeal path always moves and records

For every valid `content_id` I appeal (at least 5 appeals in the check), the item's status becomes `under_review` and an appeal entry appears in the audit log for that same `content_id` — 5/5, no silent no-ops.

**Why this target:**
The appeal is the only path a wrongly accused writer has. If it sometimes does nothing (typo handling, missing log write), the service looks fine in demos and fails the person who needs it. 100% on a small set is the right bar because a single missed appeal is already a broken promise.

---

## 5. Bad input is refused, not scored

When `text` is missing, empty, `null`, or enormous (`"word " * 50000`), the service returns HTTP 400 (or another 4xx) in 4/4 of those cases, and never returns a `guess` / `label` as if it had scored the request.

**Why this target:**
Crashing or inventing a verdict on malformed input is a common real failure, and unit 8's attack set will send these. Refusing all four shapes means bad requests stay out of the decision log as scored content — they can be rejections, not fake confidence.



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
