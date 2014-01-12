''' test feedback program '''
import time

from noise import pnoise1
import random

class World(object):
    def __init__(self, animals, width=40, height=20):
        self.width = width
        self.height = height
        self.animals = animals

    def render(self):
        ''' dump out the state of things '''
        for animal in self.animals:
            print animal

    def update(self):
        ''' let every animal move '''
        for animal in self.animals:
            animal.move()

    def run(self):
        ''' execute the world '''
        while True:
            self.update()
            self.render()
            time.sleep(0.2)


class Mover(object):
    ''' a thing that can move in the World'''
    def __init__(self, name, world, startx, starty):
        self.name = name
        self.x = startx
        self.y = starty
        self.maxx = world.width
        self.maxy = world.height

class RandomMover(Mover):
    """a thing to follow"""
    def __init__(self, name="Target", startx=5, starty=5, delta=0.07, max=40):
        super(Prey, self).__init__(name, startx, starty)
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
        self.y = int(n/2 * self.maxy + self.maxy/2)

    def __str__(self):
        return " "*self.x+'o'

class Follower(Mover):
    def __init__(self, startx=5, starty=5, kp=0.5, target):
        super(Hunter, self).__init__(startx=startx, starty=starty)
        self.kp = kp
        self.target = target

    def move(self, targetx):
        ''' update self.   Move proportionally toward target '''
        self.x += int(self.kp * (self.target.x - self.x))

    def __str__(self):
        return " "*self.x+'x'


if __name__ == "__main__":
    prey = RandomMover()
    hunter = Follower(prey)
    animals = [prey, hunter]
    World(animals).run()
    

