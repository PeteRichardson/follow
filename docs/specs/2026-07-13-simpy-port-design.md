# Port `follow.py`'s simulation loop to SimPy

## Purpose

`follow.py` currently drives its animation with a hand-rolled loop in
`World.run()`: `while True: update(); draw(); sleep(interval)`. This is
listed as a TODO in both `follow.py` and `README.md` ("Convert this to
SimPy?"). The goal of this change is **learning/exploration** — to
properly exercise SimPy's process/event idioms in a small, low-stakes
codebase — rather than to fix a real limitation of the current loop.

## Scope

- Replace the central tick loop with a `simpy.rt.RealtimeEnvironment`.
- Turn each animal into its own independent SimPy **process**: a
  generator that loops "move, then wait," instead of being called
  externally by `World.update()` every tick.
- Turn drawing into its own SimPy process on `World`.
- Leave all existing movement behavior (`RandomMover`, `Follower`,
  `Escaper`, `Escaper2`) untouched — their `move()` methods are pure
  computation and don't change.
- Default timing (0.1s for both movement and drawing) is preserved, so
  the simulation should look and behave identically to today.

Out of scope: SimPy `Resource`/`Container`/event-based collision
detection, keyboard controls, or any other TODO-list item. Those are
separate future explorations, not part of this port.

## Architecture

Each animal becomes an independent active component (a SimPy process)
that advances itself on a timer, rather than a passive object stepped
by a central loop. `World` becomes a process too, responsible only for
periodically drawing the current state. This is the core SimPy idiom:
independent generators cooperatively scheduled by an environment, each
yielding `env.timeout(...)` to give control back.

Because animals no longer share one synchronous "everybody moves, then
we draw" step, `draw_loop` may occasionally render mid-tick relative to
some animal's move — a cosmetic non-issue for a curses animation, and
itself a natural consequence of modeling components independently.

## Components

### `Mover`

- Gains an `interval` attribute, set by `World` the same way `maxx`/
  `maxy` are set today (an attribute assigned post-construction, not a
  constructor parameter — keeps every subclass constructor unchanged).
- Gains a `run(self, env)` generator method, inherited by all
  subclasses without override:

  ```python
  def run(self, env):
      """SimPy process: move, then wait, forever."""
      while True:
          self.move()
          yield env.timeout(self.interval)
  ```

- `RandomMover.move()`, `Follower.move()`, `Escaper.move()`, and
  `Escaper2.move()` are unchanged.

### `World`

- Drops `update()` — no longer needed, since each animal drives itself.
- Gains a `draw_loop(self, env)` process:

  ```python
  def draw_loop(self, env):
      while True:
          self.draw()
          yield env.timeout(self.draw_interval)
  ```

- `run()` becomes the setup and launch point:

  ```python
  def run(self, interval=0.1, draw_interval=0.1):
      env = simpy.rt.RealtimeEnvironment(factor=1.0)
      for animal in self.animals:
          animal.interval = interval
          env.process(animal.run(env))
      self.draw_interval = draw_interval
      env.process(self.draw_loop(env))
      env.run()
  ```

- `draw()` itself is unchanged.

### `__main__`

- Call site is effectively unchanged: `World(animals).run()` (defaults
  match today's behavior). No change to how `prey`/`hunter`/`randy` are
  constructed or wired to each other.

### Data flow

Target references (`prey.target = hunter`, `hunter.target = prey`)
remain plain attribute access on shared objects — unaffected by which
process last ran, since state (`x`, `y`) still lives directly on each
animal instance.

### Optional demonstration (not required by default behavior)

Because `interval` is just a per-animal attribute, a follow-up
experiment — giving `randy` a different tick rate than `hunter`/`prey`
— is a one-line change. Worth trying once the port lands, as a way to
see process independence in action, but not part of this port itself.

## Error Handling

Ctrl-c cleanup (the `signal`/`curses.endwin()` handler) is unaffected —
`RealtimeEnvironment.run()` is an ordinary blocking call from Python's
perspective, and SIGINT still interrupts it and reaches the existing
handler.

`RealtimeEnvironment` defaults to `strict=True`, which raises
`RuntimeError` if any single step (e.g. a slow `draw()`) overruns its
interval. This is left enabled rather than disabled: it should never
fire given how simple `draw()` and `move()` are today, and if it ever
does, that's a real signal worth seeing rather than silently swallowing
dropped frames.

## Testing

No automated test suite exists for this project (it's an interactive
curses program). Verification remains manual: run `python follow.py`
and confirm `hunter`, `prey`, and `randy` move exactly as they did
before, with no visible change in behavior or timing.

## Dependencies

Add `simpy` to `requirements.txt`.
