''' test feedback program '''
import time

from noise import pnoise1
import random

class World(object):
    ''' the world as we know it '''
    def __init__(self, animals, width=40, height=20):
        self.width = width
        self.height = height
        self.animals = animals
        for animal in animals:
            animal.x = int(random.random() * self.width) 
            animal.y = int(random.random() * self.height)
            animal.maxx = self.width
            animal.maxy = self.height

    def render(self):
        ''' dump out the state of things '''
        print self

    def __str__(self):
        first, last = animals[0], animals[1]
        if animals[1].x < animals[0].x:
            first, last = last, first
        if first.x == last.x:
            anstring = "*"
        else:
            anstring = "{0}{1}{2}".format(first.symbol,'.'*(last.x -first.x -1),last.symbol)
        return "{0}{1}".format(' '*(first.x-1),anstring)
       

    def update(self):
        ''' let every animal move '''
        for animal in self.animals:
            animal.move()

    def run(self):
        ''' execute the world '''
        while True:
            self.update()
            self.render()
            time.sleep(0.1)


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
    def __init__(self, name="Target", delta=0.07, symbol='R'):
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
    def __init__(self, name, target, kp=0.2, symbol='F'):
        super(Follower, self).__init__(name=name, symbol=symbol)
        self.kp = kp
        self.target = target

    def move(self):
        ''' update self.   Move proportionally toward target '''
        self.x += int(self.kp * (self.target.x - self.x))
        self.y += int(self.kp * (self.target.y - self.y))


if __name__ == "__main__":
    prey = RandomMover(name="Prey", symbol = 'o')
    hunter = Follower(name="Hunter", target=prey, symbol='<')
    animals = [hunter, prey]
    World(animals).run()
    

