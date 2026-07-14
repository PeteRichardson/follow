# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Terminal-based animal simulation using Python curses. Animals with different behaviors (follower, escaper, random wanderer) move around the terminal window. Movement randomness is driven by Perlin noise; the `Follower` class uses a PI feedback loop to chase its target.

## Running

```bash
pip install -r requirements.txt
python follow.py
```

Press `ctrl-c` to exit. The simulation auto-sizes to the current terminal window.

## Architecture

Everything lives in `follow.py`. The class hierarchy:

- `World` — owns the curses screen. `World.run()` builds a `simpy.rt.RealtimeEnvironment`, spawns one process per animal (`Mover.run`, defined once on the base class) plus a `draw_loop` process for `World` itself, then calls `env.run()`. Each animal drives its own movement on a timer instead of being stepped by a central loop. Assigns random initial positions and sets `maxx`/`maxy` bounds on each animal at startup.
- `Mover` — base: holds `x`, `y`, `symbol`; `limit()` clamps position to window bounds.
- `RandomMover(Mover)` — moves via `pnoise1` (Perlin noise) to produce smooth wandering. Maintains independent `currentx`/`currenty` noise offsets.
- `Follower(RandomMover)` — PI controller (`kp`, `ki`) that steers toward `self.target` each tick.
- `Escaper(RandomMover)` — always moves one step away from `self.target` on top of the random walk.
- `Escaper2(RandomMover)` — only flees when within a proximity buffer (default 10 units); otherwise stays still (no random walk either).

The `__main__` block wires up: `prey` (Escaper2 fleeing `hunter`) ← `hunter` (Follower chasing `prey`) + `randy` (RandomMover).
