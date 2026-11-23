"""
ساخت موسیقی هشت‌بیتی بازی
--------------------------
دو قطعهٔ حماسی و جنگی با همان «کانال‌های» کنسول‌های قدیمی ساخته می‌شود و در
assets/music ذخیره می‌شود:

  theme.wav   قطعهٔ منو و معرفی؛ آهنگ نظامی و باشکوه (۱۱۲ ضرب در دقیقه)
  battle.wav  قطعهٔ نبرد؛ تند و کوبنده (۱۵۲ ضرب در دقیقه)

هر قطعه ۱۶ میزان در می‌ی‌ر (لا مینور) است و بی‌وقفه تکرار می‌شود. کانال‌ها:
  لید    موج مربعی باریک (ملودی)
  آرپژ   موج مربعی ساده که نت‌های آکورد را پشت‌سرهم می‌زند
  باس    موج مثلثی چهاربیتی (مثل کنسول‌های قدیمی)
  درام   کیک و اسنیر و هت و کراش از نویز و موج سینوسی

بدون هیچ کتابخانهٔ خارجی کار می‌کند.   اجرا:   python tools/make_music.py
"""

import math
import os
import random
import struct
import sys
import wave
from array import array

RATE = 22050
STEPS_PER_BAR = 16               # هر میزان ۴ ضرب و هر ضرب ۴ گام (یک‌شانزدهم)
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "music")
VIB_W = 2 * math.pi * 5.5 / RATE   # ویبراتو با سرعت ۵٫۵ هرتز

# ---------------------------------------------------------------- نت‌ها
_BASE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(name: str) -> int:
    """نام نت مثل A4 یا G#4 را به شمارهٔ میدی تبدیل می‌کند (A4 = 69)."""
    sharp = 1 if name[1] == "#" else 0
    octave = int(name[1 + sharp:])
    return 12 * (octave + 1) + _BASE[name[0]] + sharp


def freq(m: int) -> float:
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def parse(line: str):
    """«A4:4 C5:2 R:2» ← [(نت، طول به گام)]؛ R یعنی سکوت."""
    events = []
    for token in line.split():
        name, length = token.split(":")
        events.append((None if name == "R" else midi(name), int(length)))
    return events


# ریشهٔ باس و نت‌های آرپژ هر آکورد
CHORDS = {
    "Am": dict(root=45, arp=(57, 60, 64, 60)),
    "F":  dict(root=41, arp=(53, 57, 60, 57)),
    "C":  dict(root=48, arp=(60, 64, 67, 64)),
    "G":  dict(root=43, arp=(55, 59, 62, 59)),
    "E":  dict(root=40, arp=(56, 59, 64, 59)),
    "Dm": dict(root=50, arp=(62, 65, 69, 65)),
}

# ---------------------------------------------------------------- قطعه‌ها
THEME = dict(
    name="theme", bpm=112, lead_duty=0.25, lead_vol=0.20, arp_vol=0.05,
    bass="pump", drums="march", fills=(7, 15),
    chords="Am Am F F C G Am E  F G Am C F G E E".split(),
    melody=[
        "A4:4 C5:4 E5:4 A5:4",
        "G5:6 E5:2 C5:4 E5:4",
        "F5:4 A4:4 C5:4 F5:4",
        "C5:6 A4:2 F4:8",
        "G4:4 C5:4 E5:4 G5:4",
        "F5:6 D5:2 B4:4 D5:4",
        "A5:6 G5:2 E5:4 C5:4",
        "B4:4 G#4:4 B4:4 E5:4",
        "A5:4 F5:4 C5:4 F5:4",
        "G5:4 D5:4 B4:4 D5:4",
        "A5:2 G5:2 E5:4 C5:4 E5:4",
        "C5:4 E5:4 G5:4 C6:4",
        "A5:6 F5:2 C5:4 F5:4",
        "G5:6 D5:2 B4:4 G4:4",
        "B4:2 C5:2 B4:2 G#4:2 E5:8",
        "E5:12 R:4",
    ],
)

BATTLE = dict(
    name="battle", bpm=152, lead_duty=0.125, lead_vol=0.19, arp_vol=0.07,
    bass="gallop", drums="attack", fills=(7, 15),
    chords="Am Am F E Am G F E  Dm Dm Am Am F G E E".split(),
    melody=[
        "A4:2 R:2 A4:2 C5:2 E5:4 D5:2 C5:2",
        "A4:2 R:2 A4:2 C5:2 E5:4 G5:4",
        "F5:4 E5:2 C5:2 A4:4 C5:4",
        "B4:4 G#4:4 B4:4 E5:4",
        "A4:2 R:2 A4:2 C5:2 E5:4 D5:2 C5:2",
        "B4:2 R:2 B4:2 D5:2 G5:4 F5:2 D5:2",
        "F5:4 A5:4 G5:4 F5:4",
        "E5:4 D5:2 C5:2 B4:4 G#4:4",
        "D5:2 R:2 D5:2 F5:2 A5:4 G5:2 F5:2",
        "E5:2 R:2 E5:2 F5:2 A5:4 D5:4",
        "C5:2 R:2 C5:2 E5:2 A5:4 G5:2 E5:2",
        "A5:4 G5:4 E5:4 C5:4",
        "F5:2 A5:2 C6:4 A5:4 F5:4",
        "G5:2 D5:2 B4:4 D5:4 G5:4",
        "B4:2 C5:2 B4:2 G#4:2 B4:4 E5:4",
        "E5:8 B4:4 G#4:4",
    ],
)

TRACKS = (THEME, BATTLE)


def validate(track) -> None:
    """بررسی می‌کند هر قطعه ۱۶ میزان دارد و جمع طول نت‌های هر میزان درست است."""
    assert len(track["chords"]) == len(track["melody"]) == 16, track["name"]
    for chord in track["chords"]:
        assert chord in CHORDS, chord
    for bar, line in enumerate(track["melody"]):
        total = sum(length for _m, length in parse(line))
        assert total == STEPS_PER_BAR, f"{track['name']}: میزان {bar + 1} جمعش {total} است، نه {STEPS_PER_BAR}"


# ---------------------------------------------------------------- صداها (هر کدام فهرستی از نمونه‌ها)
def pulse(f, n, duty, vol, decay=2.5, floor=0.5, vibrato=0.0):
    """موج مربعی با پهنای دلخواه؛ شدت آرام تا «floor» پایین می‌آید و پایانش نرم است."""
    out = [0.0] * n
    inc = f / RATE
    k = math.exp(-decay / RATE)
    env, phase = 1.0, 0.0
    release = max(1, min(160, n // 4))
    for i in range(n):
        phase += inc * (1.0 + vibrato * math.sin(i * VIB_W)) if (vibrato and i > 3000) else inc
        if phase >= 1.0:
            phase -= 1.0
        amp = vol * env
        if i < 40:
            amp *= i / 40.0
        left = n - i
        if left < release:
            amp *= left / release
        out[i] = amp if phase < duty else -amp
        env = max(floor, env * k)
    return out


def triangle(f, n, vol, decay=1.5, floor=0.65):
    """موج مثلثی با پله‌های چهاربیتی (صدای باس کنسول‌های قدیمی)."""
    out = [0.0] * n
    inc = f / RATE
    k = math.exp(-decay / RATE)
    env, phase = 1.0, 0.0
    release = max(1, min(200, n // 4))
    for i in range(n):
        phase += inc
        if phase >= 1.0:
            phase -= 1.0
        wave_value = round((4.0 * abs(phase - 0.5) - 1.0) * 7.5) / 7.5
        amp = vol * env
        if i < 30:
            amp *= i / 30.0
        left = n - i
        if left < release:
            amp *= left / release
        out[i] = wave_value * amp
        env = max(floor, env * k)
    return out


def noise(seconds, vol, decay, hold, rng):
    """نویز تصادفی که با نرخ decay محو می‌شود؛ hold بزرگ‌تر یعنی نویز بم‌تر."""
    n = int(RATE * seconds)
    out = [0.0] * n
    k = math.exp(-decay / RATE)
    env, cur = 1.0, 0.0
    for i in range(n):
        if i % hold == 0:
            cur = rng.uniform(-1.0, 1.0)
        out[i] = cur * vol * env
        env *= k
    return out


def kick(vol=0.55):
    n = int(RATE * 0.17)
    out, phase = [0.0] * n, 0.0
    for i in range(n):
        t = i / RATE
        phase += (45.0 + 135.0 * math.exp(-t * 38.0)) / RATE
        out[i] = math.sin(2 * math.pi * phase) * vol * math.exp(-t * 15.0)
    return out


def snare(rng, vol=0.30):
    body = noise(0.15, vol, 26.0, 2, rng)
    tone = triangle(190.0, len(body), vol * 0.55, decay=30.0, floor=0.0)
    return [a + b for a, b in zip(body, tone)]


def mix_into(buf, start, samples, gain=1.0):
    end = min(len(buf), start + len(samples))
    if end <= start:
        return
    seg = buf[start:end]
    if gain == 1.0:
        buf[start:end] = [a + b for a, b in zip(seg, samples)]
    else:
        buf[start:end] = [a + b * gain for a, b in zip(seg, samples)]


# ---------------------------------------------------------------- ساخت قطعه
def bass_events(style, root):
    """(گام شروع، طول، نت) برای یک میزان."""
    if style == "pump":                          # هشتم‌های پمپی: ریشه، ریشهٔ بالا، ...
        return [(2 * i, 2, root + (12 if i % 2 else 0)) for i in range(8)]
    events = []                                  # gallop: «دا-دا-دا» در هر ضرب
    for beat in range(4):
        s = 4 * beat
        events += [(s, 2, root), (s + 2, 1, root), (s + 3, 1, root + 12)]
    return events


def drum_hits(style):
    if style == "march":
        return dict(kick={0, 8, 10}, snare={4, 12}, hat={2, 6, 10, 14})
    return dict(kick={0, 4, 8, 12}, snare={4, 12}, hat=set(range(0, 16, 2)))


def render(track):
    validate(track)
    rng = random.Random(7)
    step_len = RATE * 60.0 / track["bpm"] / 4.0
    bars = len(track["chords"])
    buf = [0.0] * int(round(bars * STEPS_PER_BAR * step_len))

    def pos(step):
        return int(round(step * step_len))

    # لید
    for bar, line in enumerate(track["melody"]):
        step = bar * STEPS_PER_BAR
        for m, length in parse(line):
            if m is not None:
                n = int((pos(step + length) - pos(step)) * 0.92)
                vib = 0.004 if length >= 8 else 0.0
                mix_into(buf, pos(step), pulse(freq(m), n, track["lead_duty"], track["lead_vol"],
                                               decay=2.5, vibrato=vib))
            step += length

    # آرپژ و باس
    for bar, name in enumerate(track["chords"]):
        chord = CHORDS[name]
        base = bar * STEPS_PER_BAR
        for s in range(STEPS_PER_BAR):
            n = int((pos(base + s + 1) - pos(base + s)) * 0.85)
            mix_into(buf, pos(base + s), pulse(freq(chord["arp"][s % 4]), n, 0.5,
                                               track["arp_vol"], decay=6.0, floor=0.2))
        for start, length, m in bass_events(track["bass"], chord["root"]):
            n = int((pos(base + start + length) - pos(base + start)) * 0.9)
            mix_into(buf, pos(base + start), triangle(freq(m), n, 0.34))

    # درام
    pattern = drum_hits(track["drums"])
    kick_s, snare_s = kick(), snare(rng)
    hat_s = noise(0.035, 0.09, 110.0, 1, rng)
    crash_s = noise(0.9, 0.14, 4.5, 1, rng)
    for bar in range(bars):
        base = bar * STEPS_PER_BAR
        fill = bar in track["fills"]
        if bar % 8 == 0:
            mix_into(buf, pos(base), crash_s)                        # کراش در شروع هر بخش
        for s in range(STEPS_PER_BAR):
            at = pos(base + s)
            if s in pattern["kick"] and not (fill and s >= 8):
                mix_into(buf, at, kick_s)
            if s in pattern["hat"] and not fill:
                mix_into(buf, at, hat_s)
            if fill and s >= 8:                                      # رول اسنیر آخر هر بخش
                mix_into(buf, at, snare_s, gain=0.35 + 0.65 * (s - 8) / 7.0)
            elif s in pattern["snare"]:
                mix_into(buf, at, snare_s)

    peak = max(max(buf), -min(buf))
    scale = 0.9 / peak if peak > 0 else 1.0
    return [x * scale for x in buf]


def write_wav(path, samples):
    data = array("h", (int(max(-1.0, min(1.0, x)) * 32767) for x in samples))
    if sys.byteorder == "big":
        data.byteswap()
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.tobytes())


# ---------------------------------------------------------------- خودآزمایی
def goertzel(samples, f):
    """انرژی فرکانس f در samples (تبدیل فوریهٔ تک‌فرکانس)."""
    coeff = 2.0 * math.cos(2 * math.pi * f / RATE)
    s1 = s2 = 0.0
    for x in samples:
        s0 = x + coeff * s1 - s2
        s2, s1 = s1, s0
    return s2 * s2 + s1 * s1 - coeff * s1 * s2


def check_first_bar(track, samples):
    """نت‌های میزان اول لید را در خود صدا پیدا می‌کند و می‌گوید درست و سر وقت هستند یا نه."""
    step_len = RATE * 60.0 / track["bpm"] / 4.0
    events = parse(track["melody"][0])
    wanted = sorted({m for m, _ in events if m is not None})
    step, ok = 0, True
    for m, length in events:
        if m is not None:
            a, b = int(step * step_len), int((step + length) * step_len)
            window = samples[a + 200:b - 200]
            strongest = max(wanted, key=lambda w: goertzel(window, freq(w)))
            ok &= strongest == m
        step += length
    return ok


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for track in TRACKS:
        samples = render(track)
        path = os.path.join(OUT_DIR, track["name"] + ".wav")
        write_wav(path, samples)
        seconds = len(samples) / RATE
        print(f"{track['name']}.wav  {seconds:5.1f} ثانیه  {os.path.getsize(path) / 1e6:.2f} مگابایت  "
              f"نت‌های میزان اول درست: {check_first_bar(track, samples)}")


if __name__ == "__main__":
    main()
