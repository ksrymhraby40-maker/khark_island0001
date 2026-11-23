"""آزمون‌های منطق بازی (بدون نیاز به pygame).  اجرا:  python -m unittest discover tests"""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import config                                   # noqa: E402
from game.logic import World, Plane, Bomb, PLAYING, WON, LOST   # noqa: E402


def make_world(seed=1):
    return World(config.LEVELS[0], random.Random(seed))


def add_plane(world, kind=config.F16, x=300.0, y=200.0, tank_index=0, speed=0.0):
    """هواپیمایی با مشخصات دلخواه برای آزمایش در جهان می‌گذارد."""
    tank = world.tanks[tank_index]
    tank.reserved += 1
    plane = Plane(kind=kind, x=x, base_y=y, speed=speed, hp=kind.hp,
                  target=tank, drop_x=9999.0)
    world.planes.append(plane)
    return plane


class FireTests(unittest.TestCase):
    def test_one_hit_plane_goes_down(self):
        w = make_world()
        p = add_plane(w, config.F16)
        self.assertEqual(w.fire(p.x, p.y), "down")
        self.assertNotIn(p, w.planes)
        self.assertEqual(w.downed, 1)

    def test_two_hit_plane_needs_two_shots(self):
        w = make_world()
        p = add_plane(w, config.F35)
        self.assertEqual(w.fire(p.x, p.y), "hit")
        self.assertIn(p, w.planes)
        w.update(config.FIRE_COOLDOWN + 0.01)
        self.assertEqual(w.fire(p.x, p.y), "down")

    def test_miss_and_cooldown(self):
        w = make_world()
        add_plane(w, x=300, y=200)
        self.assertEqual(w.fire(900, 600), "miss")
        self.assertEqual(w.fire(900, 600), "cooldown")   # بلافاصله دوباره نمی‌شود شلیک کرد

    def test_killed_plane_releases_its_tank_reservation(self):
        w = make_world()
        p = add_plane(w, config.F16)
        self.assertEqual(w.tanks[0].reserved, 1)
        w.fire(p.x, p.y)
        self.assertEqual(w.tanks[0].reserved, 0)


class BombTests(unittest.TestCase):
    def run_until_bombs_land(self, w, seconds=6.0):
        for _ in range(int(seconds * 60)):
            w.update(1 / 60)

    def test_plane_that_survives_damages_tank_in_two_steps(self):
        w = make_world()
        w.time_left = 1000.0
        w._spawn_timer = 1e9                    # فقط هواپیمای دستی داریم
        tank = w.tanks[0]
        for expected_hits in (1, 2):
            tank.reserved += 1
            plane = Plane(kind=config.F16, x=tank.x - 200, base_y=200, speed=0,
                          hp=1, target=tank, drop_x=0.0)
            w.planes.append(plane)
            self.run_until_bombs_land(w, 3.0)
            self.assertEqual(tank.hits, expected_hits)
        self.assertTrue(tank.destroyed)

    def test_planes_target_tanks_in_order(self):
        w = make_world()
        targets = []
        for _ in range(12):
            self.assertTrue(w._spawn_plane())
            targets.append(w.planes[-1].target.index)
        self.assertEqual(targets, [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5])
        self.assertFalse(w._spawn_plane())      # ظرفیت پر است، هواپیمای بیشتری نمی‌آید

    def test_all_tanks_destroyed_means_lost(self):
        w = make_world()
        w._spawn_timer = 1e9
        for tank in w.tanks:
            tank.hits = config.TANK_MAX_HITS - 1
            tank.reserved = 1
            w.bombs.append(Bomb(tank.x, tank.y - 40, tank))
        w.update(0.1)
        self.assertEqual(w.state, LOST)
        names = [e.name for e in w.pop_events()]
        self.assertEqual(names.count("tank_destroyed"), 6)
        self.assertIn("game_lost", names)


class TimerTests(unittest.TestCase):
    def test_win_when_time_runs_out(self):
        w = make_world()
        w._spawn_timer = 1e9
        w.time_left = 0.05
        w.update(0.1)
        self.assertEqual(w.state, WON)

    def test_state_is_playing_at_start(self):
        w = make_world()
        self.assertEqual(w.state, PLAYING)
        self.assertEqual(w.time_left, 120.0)

    def test_no_planes_in_first_second(self):
        w = make_world()
        for _ in range(55):
            w.update(1 / 60)
        self.assertEqual(len(w.planes), 0)

    def test_spawn_rate_increases_over_time(self):
        counts = []
        for start in (0.0, 0.9):               # ابتدا و انتهای مرحله
            w = make_world(seed=5)
            w.time_left = w.level.duration * (1 - start)
            w._spawn_timer = 0.0
            spawned = 0
            for _ in range(20 * 60):
                before = len(w.planes) + w.downed
                w.update(1 / 60)
                if w.planes:                   # هواپیماها را فوراً حذف می‌کنیم تا ظرفیت پر نشود
                    spawned += len(w.planes)
                    for p in w.planes:
                        p.target.reserved -= 1
                    w.planes.clear()
                w.time_left = w.level.duration * (1 - start)
            counts.append(spawned)
        self.assertGreater(counts[1], counts[0])



class AfterWinTests(unittest.TestCase):
    def test_after_win_planes_leave_without_new_bombs(self):
        w = make_world()
        w._spawn_timer = 1e9
        plane = add_plane(w, config.F16, x=300.0, y=200.0, speed=100.0)
        plane.drop_x = 350.0                    # در حالت عادی باید بمب می‌انداخت
        w.state = WON
        for _ in range(60):
            w.update(1 / 60)
        self.assertAlmostEqual(plane.x, 400.0, delta=2.0)     # پرواز ادامه دارد
        self.assertEqual(len(w.bombs), 0)                      # ولی بمب جدیدی نمی‌اندازد
        self.assertFalse(plane.bomb_dropped)

    def test_bomb_in_flight_still_lands_after_win_but_cannot_cause_loss(self):
        w = make_world()
        w._spawn_timer = 1e9
        for tank in w.tanks:
            tank.hits = config.TANK_MAX_HITS - 1
        tank = w.tanks[0]
        tank.reserved = 1
        w.bombs.append(Bomb(tank.x, tank.y - 60, tank))
        w.state = WON
        for _ in range(30):
            w.update(1 / 60)
        self.assertTrue(tank.destroyed)
        self.assertEqual(w.state, WON)          # برد با رسیدن بمب به باخت تبدیل نمی‌شود


if __name__ == "__main__":
    unittest.main()
