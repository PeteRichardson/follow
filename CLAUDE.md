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

- `World` — owns the curses screen and the main loop (`run` → `update` → `draw`). Assigns random initial positions and sets `maxx`/`maxy` bounds on each animal at startup.
- `Mover` — base: holds `x`, `y`, `symbol`; `limit()` clamps position to window bounds.
- `RandomMover(Mover)` — moves via `pnoise1` (Perlin noise) to produce smooth wandering. Maintains independent `currentx`/`currenty` noise offsets.
- `Follower(RandomMover)` — PI controller (`kp`, `ki`) that steers toward `self.target` each tick.
- `Escaper(RandomMover)` — always moves one step away from `self.target` on top of the random walk.
- `Escaper2(RandomMover)` — only flees when within a proximity buffer (default 10 units); otherwise stays still (no random walk either).

The `__main__` block wires up: `prey` (Escaper2 fleeing `hunter`) ← `hunter` (Follower chasing `prey`) + `randy` (RandomMover).

## Known Quirks

- `World.draw` references the global `animals` list instead of `self.animals` (line 46) — a bug in the original code.
- `Escaper2.move` doesn't call `super().move()` when outside the buffer, so the entity freezes rather than wandering freely when not threatened.
