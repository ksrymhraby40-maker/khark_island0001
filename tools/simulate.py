"""
شبیه‌سازی بدون پنجره برای سنجش سختی بازی
------------------------------------------
چند «بازیکن مجازی» با مهارت‌های متفاوت هر مرحله را بارها بازی می‌کنند و درصد
برد چاپ می‌شود. اجرا:   python tools/simulate.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import config                      # noqa: E402
from game.logic import World, PLAYING, WON   # noqa: E402

# (نام، زمان واکنش بین دو شلیک به ثانیه، خطای نشانه‌روی به پیکسل)
PLAYERS = (
    ("تازه‌کار", 0.60, 30.0),
    ("معمولی", 0.40, 20.0),
    ("ماهر", 0.25, 12.0),
)


def play_once(level, reaction, sigma, seed):
    rng = random.Random(seed)
    world = World(level, random.Random(seed + 1000))
    dt = 1 / 60
    wait = 0.0
    while world.state == PLAYING:
        world.update(dt)
        world.pop_events()
        wait -= dt
        if wait > 0 or not world.planes:
            continue
        # مهم‌ترین هدف: هواپیمایی که زودتر بمب می‌اندازد (کمترین فاصله تا نقطهٔ رها کردن)
        pending = [p for p in world.planes if not p.bomb_dropped and 0 < p.x + p.kind.width]
        pool = pending or world.planes
        plane = min(pool, key=lambda p: p.drop_x - p.x if not p.bomb_dropped else 9999)
        world.fire(plane.x + rng.gauss(0, sigma), plane.y + rng.gauss(0, sigma))
        wait = reaction * rng.uniform(0.7, 1.3)
    return world


def main(runs=120):
    for level in config.LEVELS:
        print(f"--- {level.name} ---")
        for name, reaction, sigma in PLAYERS:
            wins = 0
            tanks_left = 0
            for seed in range(runs):
                w = play_once(level, reaction, sigma, seed)
                wins += w.state == WON
                tanks_left += w.tanks_alive
            print(f"{name}: برد {100 * wins / runs:5.1f}٪   میانگین مخزن سالم‌مانده {tanks_left / runs:.1f}")


if __name__ == "__main__":
    main()
