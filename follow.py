''' test feedback program '''
import time

from noise import pnoise1
import random
import curses
import signal
import sys
import logging


class World(object):
    ''' the world as we know it '''
    def __init__(self, animals, width=40, height=20):
        self.width = width
        self.height = height
        self.animals = animals
        self.quit = False
        self.scrn = curses.initscr()
        curses.curs_set(0)
        for animal in animals:
            animal.x = int(random.random() * self.width) 
            animal.y = int(random.random() * self.height)
            animal.maxx = self.width
            animal.maxy = self.height

    def render(self):
        ''' dump out the state of things '''
        self.scrn.clear()
        for animal in animals:
            self.scrn.addch(animal.y, animal.x, animal.symbol)
        self.scrn.refresh()

    def update(self):
        ''' let every animal move '''
        for animal in self.animals:
            animal.move()

    def run(self, interval = 0.1):
        ''' execute the world '''
        while True:
            self.update()
            self.render()
            time.sleep(interval)


def cleanup():
    curses.echo()
    curses.endwin()
    sys.exit(0)
def cleanup_handler(signum, frame):
    cleanup()

signal.signal(signal.SIGINT, cleanup_handler)



class Mover(object):
    ''' a thing that can move in the World'''
    def __init__(self, name, symbol='o'):
        self.name = name
        self.symbol = symbol
        self.x = 0
        self.y = 0

    def __str__(self):
        return " "*self.y+self.symbol


class RandomMover(Mover):
    """a thing that wanders around """
    def __init__(self, name="Target", delta=0.06, symbol='R'):
        super(RandomMover, self).__init__(name, symbol=symbol)
        self.currentx = random.random() * 10000
        self.currenty = random.random() * 100000
        self.delta = delta
        
    def move(self):
        ''' move according to Perlin noise'''
        self.currentx += 1
        self.currenty += 1
        n = pnoise1(self.currentx * self.delta, 1) 
        m = pnoise1(self.currenty * self.delta, 1) 
        self.x = int(n/2 * self.maxx + self.maxx/2)
        self.y = int(m/2 * self.maxy + self.maxy/2)


class Follower(Mover):
    ''' a thing that follows something else '''
    def __init__(self, name, target, kp=0.4, ki=0.03, symbol='F'):
        super(Follower, self).__init__(name=name, symbol=symbol)
        self.kp = kp
        self.ki = ki
        self.target = target
        self.sum_xerr = 0
        self.sum_yerr = 0

    def move(self):
        ''' update self.   Move proportionally toward target '''
        xerr = self.target.x - self.x
        yerr = self.target.y - self.y
        self.x += int(self.kp * xerr + self.ki * self.sum_xerr)
        self.y += int(self.kp * yerr + self.ki * self.sum_yerr)
        self.sum_xerr += xerr
        self.sum_yerr += yerr


class Escaper(RandomMover):
    ''' a thing that runs from something else '''
    def __init__(self, name, target=None, symbol='F'):
        super(Escaper, self).__init__(name=name, symbol=symbol)
        self.target = target

    def move(self):
        ''' update self.   Move away from  target '''
        logging.debug('moving prey. x={0},y={1}'.format(self.x, self.y))
        super(Escaper, self).move()
        buffer = 3
        xdistance = self.x - self.target.x
        targetonleft = xdistance > 0
        if abs(xdistance) < buffer:
            if targetonleft:
                self.x += 1
            else:
                self.x -= 1
        if self.x < 0:
            self.x = 1
        if self.x >= self.maxx:
            self.x = self.maxx - 1

        ydistance = self.y - self.target.y
        targetontop = ydistance > 0
        if abs(ydistance) < buffer:
            if targetontop:
                self.y += 1
            else:
                self.y -= 1
        if self.y < 0:
            self.y = 1
        if self.y >= self.maxy:
            self.y = self.maxy - 1
        logging.debug('moved  prey. x={0},y={1}'.format(self.x, self.y))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, filename = 'follow.txt')
    try:
        prey = Escaper(name="Prey", symbol = '*')
        hunter = Follower(name="Hunter", target=prey, symbol='@')
        prey.target = hunter
        animals = [hunter, prey]
        World(animals).run(interval = 0.1)
    except Exception as err:
        logging.debug(err)
        cleanup()
        print  err
    finally:
        print "finally"
        cleanup()
        print "done"
    

