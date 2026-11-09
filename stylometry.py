"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies.

    Returns:
        Coefficient of variation (stdev / mean) of words-per-sentence.
        Higher = lumpier lengths = more human-ish. One sentence (or empty)
        has no spread, so returns 0.0.
    """
    lengths = [len(words(s)) for s in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return 0.0
    mean = statistics.mean(lengths)
    if mean == 0:
        return 0.0
    return statistics.stdev(lengths) / mean


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words.

    Returns:
        A float between 0 and 1. Higher means more varied vocabulary.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def punctuation_density(text: str) -> float:
    """
    How much "interesting" punctuation, relative to word count.

    Counts commas, semicolons, colons, dashes, and question/exclamation marks
    (not full stops — almost every sentence has those). Higher usually means
    more human-ish variety.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    marks = re.findall(r"[,;:!?—–\-]", text)
    return len(marks) / len(tokens)


# ── Combining them ───────────────────────────────────────────────────────────

def _clip01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.**

    Each raw measure is higher for more human-ish shape, so each is flipped
    after scaling onto 0–1:

      - low sentence-length spread  → AI-ish
      - low type-token ratio        → AI-ish
      - low punctuation density     → AI-ish

    Equal average of the three. Empty / near-empty text scores as uncertain
    (0.5) rather than inventing a confident reading.
    """
    if not text or not text.strip() or not words(text):
        return 0.5

    # CV ~1.0 is already very lumpy; denser than that still maps to "human".
    spread_human = _clip01(sentence_length_spread(text) / 1.0)
    ttr_human = _clip01(type_token_ratio(text))
    # ~0.25 marks/word is a busy, human-looking density for short prose.
    punct_human = _clip01(punctuation_density(text) / 0.25)

    ai_from_spread = 1.0 - spread_human
    ai_from_ttr = 1.0 - ttr_human
    ai_from_punct = 1.0 - punct_human

    score = (ai_from_spread + ai_from_ttr + ai_from_punct) / 3.0
    return round(_clip01(score), 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text):.4f}")
    print(f"type_token_ratio         {type_token_ratio(text):.4f}")
    print(f"punctuation_density      {punctuation_density(text):.4f}")
    print(f"style_signal             {style_signal(text):.4f}   (higher = more likely AI)")
