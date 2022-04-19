# Follow.py

Simple feedback control sample in python: Simulation of animals chasing each other around the curses window.

Movement is randomized using Perlin noise algorithm.

Different animal types have different movements: Follower, Escaper, etc
Follower uses a PI feedback loop

<img width="845" alt="image" src="https://user-images.githubusercontent.com/979694/163905439-ccf43199-4b99-4839-9ed9-ac74738a4f4d.png">

    
To Do:
* Convert this to SimPy?
* Read keyboard for speedup, pause, etc
* Add fixed entities (e.g. walls, plants) and don't allow two things to exist in the same location.
