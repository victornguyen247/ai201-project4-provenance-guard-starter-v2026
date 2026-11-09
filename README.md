# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

1. A writer sends `POST /submit` with JSON `{"text": "...", "creator_id": "..."}`.
2. The route refuses missing/empty text with HTTP 400 instead of scoring junk.
3. Signal one runs: `detector.model_signal(text)` scores how predictable the text is (higher → more AI-ish).
4. Signal two runs: `stylometry.style_signal(text)` scores the shape of the writing — sentence-length spread, vocabulary variety, punctuation density (higher → more AI-ish).
5. `scoring.combine_signals` averages the two scores 50/50 into one combined score.
6. `scoring.score_to_label` turns that number into a short `guess` (`human` / `unsure` / `ai`) and a full-sentence label a reader can understand.
7. The decision is written to `logs/audit.jsonl` and returned in the JSON response. If the writer disagrees, `POST /appeal` records their reasoning and sets status to `under_review`.

---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:**
How predictable the text is to a local language model (`gpt2`). The raw measure is **perplexity** — how surprised the model is by each next token. `detector.model_signal` maps that onto 0–1 where **higher means more likely AI** (low perplexity → high score). Midpoint for a coin-flip is perplexity 45.

**Why that might differ between human and AI writing:**
A model writes by repeatedly picking a likely next word, so model-written text tends to be text a model finds easy to predict. Human writing wanders more — odd word choices, abrupt turns, the specific rather than the typical — so it usually has higher perplexity.

**What it can't see:**
Predictability is not authorship. It rewards common words in short, ordinary sentences — so plainly written human text (second-language writers, younger writers, anyone writing simply on purpose) can score as machine-like. The reverse also fails: dense prose full of rare words often scores as *human*, because rare words are what the model fails to predict. Formality alone does not decide it.

### Signal two — the style signal

**What it measures:**
The *shape* of the text, not its meaning — three surface measures combined in `stylometry.style_signal` into a 0–1 score (**higher = more likely AI**):
- `sentence_length_spread` — how much sentence length varies
- `type_token_ratio` — how much of the vocabulary is unique vs repeated
- `punctuation_density` — how much (and how varied) the punctuation is

**Why that might differ between human and AI writing:**
Generated prose tends toward even, mid-length sentences and a narrower band of vocabulary, because that is what "most likely next word" produces on average. Human writing is lumpier — a three-word sentence next to a forty-word one, more varied word choice, messier punctuation habits.

**What it can't see:**
This signal cannot read. Anything that changes the shape without changing the substance moves it — adding typos, breaking up sentences, pasting in a quotation. That is cheap to do on purpose, which is exactly the kind of move unit 8's attack set will use.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:**
Weighted average of the two signals. Both already point the same way (higher = more AI-ish), so disagreement lands near the middle — treated as uncertainty rather than letting either signal veto the other. Equal weight for now: neither signal is trusted enough alone (model blind-spots plain humans; style is easy to game).

**The numbers:**
`0.5 × model_signal + 0.5 × style_signal` (`WEIGHT_MODEL_SIGNAL = 0.5`, `WEIGHT_STYLE_SIGNAL = 0.5` in `config.py`).

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**
Plain, conventional human writing — short ordinary sentences, common words, but with uneven sentence lengths. The model signal can score high (predictable → AI-ish); the style signal can score lower (lumpy lengths → human-ish). Equal weights pull the combined score toward ~0.5, into the unsure band, instead of letting the model signal alone accuse the writer.

---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 – 0.35 | We think this was probably written by a person. |
| unsure | 0.35 – 0.65 | We're not sure who wrote this — it could be a person, AI, or a mix of both. |
| high-confidence AI | 0.65 – 1.00 | We think this was probably written with AI help. |

**Why I worded the "unsure" one this way:**
It names the uncertainty without accusing anyone. A writer who did the work themselves should hear "we don't know," not "we suspect you cheated." Saying it could be a person, AI, or both also matches how the two signals can disagree.



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"The implementation of the proposed framework requires careful consideration of several key factors. First, it is important to note that the system must be able to handle a wide variety of different inputs. Additionally, the overall performance of the solution depends on a number of important variables. It is also essential to ensure that the approach remains consistent across cases.\", \"creator_id\": \"ms5-ai\"}"
```

```json
{
  "content_id": "c93c18e8-439d-4fab-8d91-dd908e2e305d",
  "guess": "ai",
  "confidence": 0.7582,
  "label": "We think this was probably written with AI help.",
  "model_score": 0.8801,
  "style_score": 0.6363,
  "combined_score": 0.7582
}
```

(All three labels are reachable. Examples from the same run: human `combined_score` 0.2001 → “We think this was probably written by a person.”; unsure `combined_score` 0.5836 → “We're not sure who wrote this — it could be a person, AI, or a mix of both.”)

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d "{\"content_id\": \"c93c18e8-439d-4fab-8d91-dd908e2e305d\", \"reasoning\": \"I wrote every word myself. The short sentences are just how I draft.\"}"
```

```json
{
  "ok": true,
  "content_id": "c93c18e8-439d-4fab-8d91-dd908e2e305d",
  "status": "under_review",
  "message": "Your appeal was recorded and this item is under review."
}
```

**What the log shows afterwards**

Entries for that `content_id` (decision, then appeal):

```json
[
  {
    "timestamp": "2026-11-09T03:59:41+00:00",
    "content_id": "c93c18e8-439d-4fab-8d91-dd908e2e305d",
    "creator_id": "ms5-ai",
    "guess": "ai",
    "model_score": 0.8801,
    "style_score": 0.6363,
    "combined_score": 0.7582,
    "label": "We think this was probably written with AI help.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-09T03:59:41+00:00",
    "content_id": "c93c18e8-439d-4fab-8d91-dd908e2e305d",
    "creator_id": "ms5-ai",
    "event": "appeal",
    "status": "under_review",
    "reasoning": "I wrote every word myself. The short sentences are just how I draft."
  }
]
```

---

## How I Used AI

**Moment 1**

- *What I asked for:* Help finishing Milestone 3 on `/submit` — pull the payload, call `detector.model_signal`, log with `audit.log_decision`, and leave confidence/label as placeholders.
- *What came back:* A full route that validated input, called the model signal, logged a decision, and returned JSON. It also sketched catching detector failures as HTTP 503.
- *What I changed:* Kept the validation and logging shape, but made sure only `model_score` was “real” at that step and that placeholders stayed placeholders until later milestones — so a broken signal wouldn’t be confused with a broken route.

**Moment 2**

- *What I asked for:* Finish Milestone 4 stylometry and then Milestone 5 (`score_to_label`, `/appeal`, README labels/sample run).
- *What came back:* Implementations for the three style measures and `style_signal`, wiring through `combine_signals`, human-readable label sentences, an `/appeal` handler, and pasted sample curl/log output.
- *What I changed:* Dropped a non-existent `StylometryUnavailable` handler that would have crashed; made sure `score_to_label`’s `(guess, label)` tuple was unpacked instead of stuffing the tuple into `label`; and checked live that all three labels were actually reachable before trusting the README ranges.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
