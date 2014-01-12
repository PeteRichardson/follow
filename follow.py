''' test feedback program '''
import time

from noise import pnoise1
import random
class Prey(object):
    """a thing to follow"""
    def __init__(self, name="Target", startx=5, delta=0.07, max=40):
        self.name = name
        self.x = startx
        self.current = random.random() * 10000
        self.delta = delta
        self.max = max
        
    def move(self):
        ''' move according to Perlin noise'''
        self.current += 1
        n = pnoise1(self.current * self.delta, 1) 
        self.x = int(n/2 * self.max + self.max/2)

    def __str__(self):
        return " "*self.x+'o'

class Hunter:
    def __init__(self, startx=5, kp=0.5):
        self.x = startx
        self.kp = kp

    def move(self, targetx):
        self.x += int(self.kp * (targetx - self.x))

    def __str__(self):
        return " "*self.x+'x'


class Globals:
    prey = Prey()
    hunter = Hunter(startx=4)

if __name__ == "__main__":
    gb = Globals()
    while True:
        gb.prey.move()
        gb.hunter.move(gb.prey.x)
        print gb.hunter
        print gb.prey
        time.sleep(0.1)

