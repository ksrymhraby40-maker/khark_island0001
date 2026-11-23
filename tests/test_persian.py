"""آزمون‌های ماژول متن فارسی.  اجرا:  python -m unittest discover tests"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.persian import shape, visual, format_time, fa_number, to_persian_digits   # noqa: E402


class ShapeTests(unittest.TestCase):
    def test_initial_and_final_forms(self):
        # «بد»: ب آغازی + د پایانی
        self.assertEqual(shape("بد"), chr(0xFE91) + chr(0xFEAA))

    def test_isolated_letter(self):
        self.assertEqual(shape("ب"), chr(0xFE8F))

    def test_lam_alef_ligature(self):
        self.assertEqual(shape("لا"), chr(0xFEFB))

    def test_non_joining_letters_break_the_chain(self):
        # بعد از «ا» حرف بعدی دوباره آغازی می‌شود: «ابب»
        self.assertEqual(shape("ابب"), chr(0xFE8D) + chr(0xFE91) + chr(0xFE90))

    def test_zwnj_is_removed_and_breaks_joining(self):
        self.assertEqual(shape("ب‌ب"), chr(0xFE8F) + chr(0xFE8F))

    def test_persian_letters_have_forms(self):
        for ch in "پچژگکی":
            self.assertNotEqual(shape(ch), ch)

    def test_digits_and_punctuation_untouched(self):
        self.assertEqual(shape("۱۲:۳۴ !"), "۱۲:۳۴ !")


class VisualTests(unittest.TestCase):
    def test_numbers_keep_their_order(self):
        self.assertEqual(visual("۱۴۰۵/۱۲/۹"), "۱۴۰۵/۱۲/۹")
        self.assertEqual(visual("۰۲:۰۰"), "۰۲:۰۰")

    def test_rtl_text_is_reversed(self):
        self.assertEqual(visual("بد"), chr(0xFEAA) + chr(0xFE91))

    def test_number_moves_to_the_left_of_rtl_word(self):
        text = visual("مرحله ۱")
        self.assertTrue(text.startswith("۱"))

    def test_parentheses_are_mirrored(self):
        self.assertEqual(visual("(ب)"), "(" + chr(0xFE8F) + ")")


class NumberTests(unittest.TestCase):
    def test_digit_conversion(self):
        self.assertEqual(to_persian_digits("12:05"), "۱۲:۰۵")
        self.assertEqual(fa_number(1405), "۱۴۰۵")

    def test_format_time(self):
        self.assertEqual(format_time(120), "۰۲:۰۰")
        self.assertEqual(format_time(59.2), "۰۱:۰۰")
        self.assertEqual(format_time(0), "۰۰:۰۰")



class EngineModeTests(unittest.TestCase):
    """وقتی موتور متن خودش ترتیب را برعکس می‌کند، خروجی باید دقیقاً معکوس حالت عادی باشد."""

    def tearDown(self):
        from game import persian
        persian.set_engine_reorders(False)

    def test_engine_mode_is_exact_reverse(self):
        from game import persian
        for text in ("شروع بازی", "مرحله ۱", "۱۴۰۵/۱۲/۹", "سرنگون\u200cشده: ۱۲"):
            persian.set_engine_reorders(False)
            normal = persian.visual(text)
            persian.set_engine_reorders(True)
            self.assertEqual(persian.visual(text), normal[::-1])


if __name__ == "__main__":
    unittest.main()
