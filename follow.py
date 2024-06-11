#!/usr/bin/env python3

""" Simulation for animals chasing each other around the ncurses window.
    Movement is randomized using Perlin noise algorithm.
    Different animal types have different movements: Follower, Escaper, etc

    TODO: Convert this to SimPy?
    TODO: Read keyboard for speedup, pause, etc
    TODO: Add fixed entities (e.g. walls, plants) and don't allow two things
          to exist in the same location.
"""

import time

from noise import pnoise1
import random
import curses
import signal
import sys
import math


class World(object):
    """the world as we know it

    Contains a list of animals that move, and functions to draw
    """

    def __init__(self, animals):
        self.animals = animals
        self.quit = False
        self.scrn = curses.initscr()
        self.height, self.width = self.scrn.getmaxyx()
        curses.curs_set(0)
        for animal in animals:
            animal.x = int(random.random() * self.width)
            animal.y = int(random.random() * self.height)
            animal.maxx = self.width - 1
            animal.maxy = self.height

    def draw(self):
        """dump out the state of things"""
        self.scrn.clear()
        self.scrn.addstr(self.height - 1, 0, "ctrl-c to exit")
        n = 0
        for animal in animals:
            self.scrn.addch(animal.y, animal.x, animal.symbol)
            self.scrn.addstr(n, 0, str(animal))  # add animal to the legend
            n = n + 1
        self.scrn.refresh()

    def update(self):
        """let every animal move"""
        for animal in self.animals:
            animal.move()
            # animal.evaluate()

    def run(self, interval=0.1):
        """execute the world"""
        while True:
            self.update()
            self.draw()
            time.sleep(interval)


def cleanup():
    """Teardown curses.  Otherwise terminal maybe left in a bad state"""
    curses.echo()
    curses.endwin()
    sys.exit(0)


def cleanup_handler(signum, frame):
    cleanup()


signal.signal(signal.SIGINT, cleanup_handler)


def dist(obj1, obj2):
    """Note to self:  square in python is _not_ x^2!  It's x**2!"""
    return math.sqrt((obj1.x - obj2.x) ** 2 + (obj1.y - obj2.y) ** 2)


class Mover(object):
    """a thing that can move in the World"""

    def __init__(self, name, symbol="M"):
        self.name = name
        self.symbol = symbol
        self.x = 0
        self.y = 0

    def move(self):
        """a bit odd that the base Mover doesn't move, I suppose."""
        pass

    def limit(self):
        """Constrain location to be within the window"""
        if self.x <= 0:
            self.x = 0
        if self.x >= self.maxx:
            self.x = self.maxx - 1
        if self.y <= 0:
            self.y = 0
        if self.y >= self.maxy:
            self.y = self.maxy - 1

    def __str__(self):
        """string representation is used to populate the legend"""
        return self.symbol + ": " + str(self.x) + "," + str(self.y)


class RandomMover(Mover):
    """a thing that wanders around"""

    def __init__(self, name="Target", delta=0.06, symbol="R"):
        super(RandomMover, self).__init__(name, symbol=symbol)
        self.currentx = random.random() * 10000
        # y multiplier bigger because generally maxx >> maxy
        self.currenty = random.random() * 100000
        self.delta = delta

    def move(self):
        """move according to Perlin noise"""
        self.currentx += 1
        self.currenty += 1
        n = pnoise1(self.currentx * self.delta, 1)
        m = pnoise1(self.currenty * self.delta, 1)
        self.x = abs(int(n / 2 * self.maxx + self.maxx / 2))
        self.y = abs(int(m / 2 * self.maxy + self.maxy / 2))


class Follower(RandomMover):
    """a thing that follows something else"""

    def __init__(self, name, target, kp=0.4, ki=0.03, symbol="F"):
        super(Follower, self).__init__(name=name, symbol=symbol)
        self.kp = kp
        self.ki = ki
        self.target = target
        self.sum_xerr = 0
        self.sum_yerr = 0

    def move(self):
        """Move proportionally toward target"""
        xerr = self.target.x - self.x
        yerr = self.target.y - self.y
        self.x += int(self.kp * xerr + self.ki * self.sum_xerr)
        self.y += int(self.kp * yerr + self.ki * self.sum_yerr)
        self.sum_xerr += xerr
        self.sum_yerr += yerr
        self.limit()


class Escaper(RandomMover):
    """a thing that runs from something else"""

    def __init__(self, name, target=None, symbol="E"):
        super(Escaper, self).__init__(name=name, symbol=symbol)
        self.target = target

    def move(self):
        """Move away from target"""
        super(Escaper, self).move()
        self.x += 1 if self.x > self.target.x else -1
        self.y += 1 if self.y > self.target.y else -1
        self.limit()


class Escaper2(RandomMover):
    """a thing that runs from something else, if it's too close"""

    last_move_was_random = False

    @property
    def distance_to_target(self):
        return dist(self, self.target)

    def __init__(self, name, target=None, symbol="E"):
        super(Escaper2, self).__init__(name=name, symbol=symbol)
        self.target = target

    def move(self):
        """_If too close_, move away from target"""
        buffer = 10.0
        if self.distance_to_target <= buffer:
            super(Escaper2, self).move()
            self.x += 1 if self.x > self.target.x else -1
            self.y += 1 if self.y > self.target.y else -1
        self.limit()

    def __str__(self):
        """string representation is used to populate the legend"""
        dist = str(self.distance_to_target)[0:5]
        return f"{self.symbol}: {str(self.x)}, {str(self.y)}  distance: {dist}"


if __name__ == "__main__":
    try:
        prey = Escaper2(name="Prey", symbol="🐇")
        hunter = Follower(name="Hunter", target=prey, symbol="🐕", kp=0.25, ki=0.03)
        randy = RandomMover(name="Randy", symbol="🦋")
        prey.target = hunter

        animals = [prey, hunter, randy]
        World(animals).run(interval=0.1)
    finally:
        cleanup()
