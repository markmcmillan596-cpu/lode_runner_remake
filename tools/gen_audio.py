"""Generates every sound for the Lode Runner-style seasonal asset pack.

    python3 tools/gen_audio.py              # all themes in VOICES
    python3 tools/gen_audio.py halloween    # one theme

Writes assets/themes/<theme>/sfx/<name>.wav and assets/themes/<theme>/music.wav
(22050 Hz, mono, 16-bit).

The lesson in this file:
  * The original Apple II game had NO music, only short effects, and every effect
    told the player about a rule (you dug, you got gold, the exit is open, you died).
    So the effects are the core of this pack; the music loop is optional polish.
  * Each effect is described once, as notes and slides. A theme only changes the
    VOICE (the waveform) and the musical scale, so fall and Halloween play the same
    "gold" cue on different instruments.
  * Every effect is normalised to the same loudness here, so the Lua side needs no
    per-theme volume table.
"""
import os
import sys
import wave
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "assets", "themes")
SR = 22050
rng = np.random.default_rng(1983)


# ---------------------------------------------------------------------------
# Voices: a voice turns a phase array (in cycles) into samples in -1..1
# ---------------------------------------------------------------------------
def pulse(duty):
    return lambda ph: np.where((ph % 1.0) < duty, 1.0, -1.0)


def triangle(ph):
    return 4 * np.abs((ph % 1.0) - 0.5) - 1


def soft_square(ph):            # square with the corners rounded off: warmer
    return np.tanh(3 * np.sin(2 * np.pi * ph))


def bell(ph):                   # sine plus a bright overtone: a small glass bell
    return 0.8 * np.sin(2 * np.pi * ph) + 0.25 * np.sin(2 * np.pi * ph * 2.76)


def sine(ph):
    return np.sin(2 * np.pi * ph)


def airy(ph):                   # sine with a faint octave: cold and clear
    return 0.85 * np.sin(2 * np.pi * ph) + 0.15 * np.sin(4 * np.pi * ph)


VOICES = {
    "fall":      {"lead": soft_square, "fx": pulse(0.25), "bass": triangle, "vibrato": 0.0},
    "halloween": {"lead": pulse(0.125), "fx": pulse(0.125), "bass": triangle, "vibrato": 0.012},
    "christmas": {"lead": bell, "fx": bell, "bass": sine, "vibrato": 0.0},
    "winter":    {"lead": airy, "fx": sine, "bass": sine, "vibrato": 0.004},
}

# Semitone offsets from the root for each theme's scale (used by jingles and music)
SCALES = {
    "fall":      [0, 2, 4, 7, 9, 12, 14, 16],        # major pentatonic: open, folky
    "halloween": [0, 3, 5, 7, 8, 12, 15, 17],        # natural minor flavour: spooky
    "christmas": [0, 2, 4, 5, 7, 9, 11, 12],         # plain major: carol-like
    "winter":    [0, 2, 4, 6, 7, 9, 11, 12],         # lydian: bright and icy
}
ROOT_HZ = {"fall": 293.66, "halloween": 220.0, "christmas": 392.0, "winter": 246.94}   # D4, A3, G4, B3


def env(n, attack=0.004, release=0.04):
    """Linear attack / release envelope so no note starts or ends with a click."""
    e = np.ones(n)
    a, r = max(1, int(attack * SR)), max(1, int(release * SR))
    a, r = min(a, n // 2), min(r, n // 2)
    e[:a] = np.linspace(0, 1, a)
    e[n - r:] = np.linspace(1, 0, r)
    return e


def tone(voice, f0, f1, dur, vol=1.0, vibrato=0.0, decay=0.0):
    """A note that slides from f0 to f1 Hz (exponentially, like a pitch bend)."""
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / dur)
    if vibrato:
        f = f * (1 + vibrato * np.sin(2 * np.pi * 6 * t))
    ph = np.cumsum(f) / SR
    y = voice(ph) * env(n)
    if decay:
        y = y * np.exp(-t * decay)
    return y * vol


def noise(dur, vol=1.0, decay=12.0, step=1):
    """Noise burst. step > 1 holds each value for several samples: a grittier, lower crunch."""
    n = int(dur * SR)
    v = rng.uniform(-1, 1, n // step + 1).repeat(step)[:n]
    t = np.arange(n) / SR
    return v * np.exp(-t * decay) * env(n) * vol


def seq(parts, gap=0.0):
    """Join sounds end to end with an optional silence between them."""
    out = []
    for p in parts:
        out.append(p)
        if gap:
            out.append(np.zeros(int(gap * SR)))
    return np.concatenate(out)


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def note(theme, degree, octave=0):
    s = SCALES[theme]
    k = degree % len(s)
    o = degree // len(s) + octave
    return ROOT_HZ[theme] * 2 ** ((s[k] + 12 * o) / 12)


# ---------------------------------------------------------------------------
# The effects. Each one is a gameplay message; the comment says which.
# ---------------------------------------------------------------------------
def effects(theme):
    v = VOICES[theme]
    fx, lead, vib = v["fx"], v["lead"], v["vibrato"]
    N = lambda d, o=0: note(theme, d, o)  # noqa: E731
    E = {}
    # You dug a hole: a gritty crunch and a short downward scrape.
    E["dig"] = mix(noise(0.16, 0.8, decay=18, step=6), tone(fx, 420, 160, 0.14, 0.5))
    # A hole is closing / closed: low thump. Players learn to hear holes shut.
    E["fill"] = mix(tone(v["bass"], 140, 70, 0.12, 1.0, decay=20), noise(0.06, 0.35, decay=40, step=10))
    # Gold picked up: two quick rising notes.
    E["gold"] = seq([tone(lead, N(4), N(4), 0.05, vibrato=vib), tone(lead, N(7), N(7), 0.09, vibrato=vib)])
    # All gold taken, exit ladder appears: the most important cue in the game.
    E["all_gold"] = seq([tone(lead, N(d), N(d), 0.07, vibrato=vib) for d in (0, 2, 4, 5)]
                        + [tone(lead, N(7), N(7), 0.4, vibrato=vib * 2, decay=4)])
    # Falling (loops while you fall; stop it on landing): a long downward whistle.
    E["fall"] = tone(fx, 1100, 280, 0.6, 0.6)
    # A guard dropped into your hole.
    E["trapped"] = seq([tone(fx, 600, 260, 0.08), tone(fx, 330, 330, 0.08, 0.7)])
    # A guard was crushed by a refilling hole.
    E["guard_die"] = mix(noise(0.3, 0.9, decay=10, step=4), tone(v["bass"], 200, 50, 0.3, 0.8))
    # A guard reappears at the top of the screen.
    E["guard_spawn"] = seq([tone(fx, f, f * 1.5, 0.05, 0.6) for f in (300, 400, 530, 700)])
    # You were caught: a sad falling phrase.
    E["player_die"] = seq([tone(lead, N(d), N(d) * 0.97, 0.16, vibrato=vib * 2) for d in (7, 5, 4, 2)]
                          + [tone(lead, N(0), N(0, -1), 0.45, decay=3)])
    # Level start: short call to action.
    E["level_start"] = seq([tone(lead, N(d), N(d), 0.1, vibrato=vib) for d in (0, 4, 2, 5, 4)]
                           + [tone(lead, N(7), N(7), 0.35, decay=3)], gap=0.01)
    # Level clear: you climbed off the top.
    E["level_clear"] = seq([tone(lead, N(d), N(d), 0.08) for d in (0, 2, 4, 7, 4, 7)]
                           + [mix(tone(lead, N(9), N(9), 0.5, decay=3), tone(v["bass"], N(0, -1), N(0, -1), 0.5, 0.6))])
    E["extra_life"] = seq([tone(fx, N(d, 1), N(d, 1), 0.06, 0.7) for d in (0, 2, 4, 0, 2, 4, 7)])
    E["game_over"] = seq([tone(lead, N(d), N(d), 0.35, vibrato=vib * 2, decay=1.5) for d in (4, 3, 2, 1)]
                         + [tone(lead, N(0), N(0), 0.9, decay=2)], gap=0.03)
    E["pause"] = seq([tone(fx, 880, 880, 0.05, 0.6), tone(fx, 660, 660, 0.07, 0.6)], gap=0.03)
    E["select"] = tone(fx, 990, 990, 0.04, 0.6)
    return E


def normalise(y, target_rms=0.2, peak=0.85):
    """Bring every effect to the same loudness (RMS), but never past the peak limit."""
    loud = y[np.abs(y) > 0.01]
    rms = np.sqrt(np.mean(loud ** 2)) if len(loud) else 1
    y = y * (target_rms / rms)
    m = np.max(np.abs(y))
    if m > peak:
        y = y * (peak / m)
    return y


def write_wav(path, y):
    y = np.clip(y, -1, 1)
    data = (y * 32767).astype("<i2").tobytes()
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)


# ---------------------------------------------------------------------------
# Music: a quiet 16-bar loop. Notes that ring past the end wrap to the start,
# so the loop is seamless by construction (no seam fixing needed later).
# ---------------------------------------------------------------------------
SONGS = {
    #            bpm  chord roots per bar (scale degrees), 4 bars repeated with a variation
    "fall":      (104, [0, 0, 3, 0, 4, 3, 0, 4]),
    "halloween": (92,  [0, 4, 2, 3, 0, 4, 1, 3]),
    "christmas": (112, [0, 3, 4, 0, 3, 4, 0, 4]),
    "winter":    (80,  [0, 4, 2, 4, 0, 5, 2, 4]),
}


def music(theme):
    v = VOICES[theme]
    bpm, roots = SONGS[theme]
    beat = 60 / bpm
    bars = 16
    total = int(bars * 4 * beat * SR)
    out = np.zeros(total)
    r = np.random.default_rng(len(theme) * 7)

    def place(y, t):
        i = int(t * SR) % total
        end = i + len(y)
        if end <= total:
            out[i:end] += y
        else:                       # wrap the tail round to the start
            k = total - i
            out[i:] += y[:k]
            out[:end - total] += y[k:]

    melody_deg = 4
    for bar in range(bars):
        root = roots[bar % len(roots)]
        t0 = bar * 4 * beat
        # bass on beats 1 and 3
        for b in (0, 2):
            f = note(theme, root, -2 if theme == "fall" else -1)
            place(tone(v["bass"], f, f, beat * 1.6, 0.55, decay=1.5), t0 + b * beat)
        # soft arpeggio on the off-beats
        for i in range(4):
            d = root + (0, 2, 4, 2)[i]
            f = note(theme, d)
            place(tone(triangle, f, f, beat * 0.4, 0.14, decay=6), t0 + (i + 0.5) * beat)
        # sparse lead melody: a gentle random walk on the scale, rests on purpose
        if bar % 4 != 3:
            for i in range(4):
                if r.random() < 0.35:
                    continue
                melody_deg = int(np.clip(melody_deg + r.choice([-2, -1, 1, 2]), root, root + 7))
                f = note(theme, melody_deg, 1 if theme == "halloween" else 0)
                place(tone(v["lead"], f, f, beat * 0.8, 0.16, vibrato=v["vibrato"] * 1.5, decay=2), t0 + i * beat)
    m = np.max(np.abs(out))
    return out * (0.7 / m)


def build(theme):
    d = os.path.join(OUT, theme, "sfx")
    os.makedirs(d, exist_ok=True)
    for name, y in effects(theme).items():
        write_wav(os.path.join(d, name + ".wav"), normalise(y))
    write_wav(os.path.join(OUT, theme, "music.wav"), music(theme))
    print("%-10s %d effects + music" % (theme, len(effects(theme))))


if __name__ == "__main__":
    for name in (sys.argv[1:] or list(VOICES)):
        build(name)
