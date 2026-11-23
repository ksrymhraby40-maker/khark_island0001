"""آزمون موسیقی: درستی قطعه‌ها در اسکریپت و فایل‌های wav همراه پروژه.  اجرا:  python -m unittest discover -s tests"""

import os
import sys
import unittest
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import make_music                                            # noqa: E402


class NoteTests(unittest.TestCase):
    def test_midi_numbers(self):
        self.assertEqual(make_music.midi("A4"), 69)
        self.assertEqual(make_music.midi("C5"), 72)
        self.assertEqual(make_music.midi("G#4"), 68)
        self.assertAlmostEqual(make_music.freq(69), 440.0)

    def test_parse_rest_and_lengths(self):
        self.assertEqual(make_music.parse("A4:4 R:2"), [(69, 4), (None, 2)])


class TrackTests(unittest.TestCase):
    def test_every_bar_is_complete(self):
        for track in make_music.TRACKS:
            make_music.validate(track)                       # اگر جمع طول نت‌های میزانی غلط باشد خطا می‌دهد

    def test_loop_ends_on_dominant_and_starts_on_tonic(self):
        for track in make_music.TRACKS:
            self.assertEqual(track["chords"][0], "Am")
            self.assertEqual(track["chords"][-1], "E")      # آکورد آخر به شروع (لا مینور) برمی‌گردد

    def test_shipped_wav_files_match_the_script(self):
        for track in make_music.TRACKS:
            path = os.path.join(make_music.OUT_DIR, track["name"] + ".wav")
            self.assertTrue(os.path.exists(path), path)
            with wave.open(path) as w:
                self.assertEqual((w.getnchannels(), w.getsampwidth(), w.getframerate()), (1, 2, 22050))
                if track["name"] == "battle":                # موسیقی نبرد فایل آمادهٔ گروه است، نه خروجی اسکریپت
                    continue
                expected = 16 * 16 * 60.0 / track["bpm"] / 4.0
                self.assertAlmostEqual(w.getnframes() / w.getframerate(), expected, delta=0.05)


if __name__ == "__main__":
    unittest.main()
