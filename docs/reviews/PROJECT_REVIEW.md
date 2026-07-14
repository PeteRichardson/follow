# Project Review: follow

**Generated:** 2026-07-13 (repeat run — supersedes the 33c4f97-scoped review)
**Scope:** whole repo (single-file project)
**Commit:** d5aa9da (chore: add __pycache__/ to .gitignore)
**Previous review:** commit 33c4f97 — see "What changed since the last run" below.

## Executive summary

- **All 16 findings from the previous run are still open.** Nothing was fixed since 33c4f97; only line numbers shifted from the SimPy tick-loop port. None are marked `RESOLVED`.
- **New, high-value finding:** `__main__`'s `finally: cleanup()` calls `sys.exit(0)` unconditionally (follow.py:213-214, `cleanup()` at 67-71). An exception raised in a `finally` block discards whatever was propagating from the `try` — so *every* crash this program can currently hit (the curses corner-cell crash below, or the new SimPy timeout crash) silently exits with status 0 and zero diagnostic output. This is the single biggest lever in the repo: fixing it makes every other bug in this list visible instead of invisible.
- **New finding from the SimPy port:** `RealtimeEnvironment`'s default `strict=True` (follow.py:58) raises `RuntimeError` if any single `move()`/`draw()` tick overruns its 0.1s interval — a failure mode the old hand-rolled loop never had. This was an explicit, documented tradeoff in the port's design spec, not an oversight, but it's worth flagging because of the masking issue above: if it ever fires, nobody will know.
- **Elevated finding:** the curses "bottom-right corner cell" crash (`curses.error` from `addstr` on a double-width emoji or fixed string landing on the window's last cell) was rated Low-Medium in the prior run. Independent re-verification this pass shows it's worse than described: `RandomMover.move()` (follow.py:131-138) never calls `self.limit()` at all, so `randy` — one of only three animals in `__main__` — is drawn with completely unclamped coordinates. This is now rated High, matching the independent `/code-review` pass's rating (see Phase 1.5 note on why that report isn't cited directly).
- `CLAUDE.md`'s "Known Quirks" section is still stale — both listed bugs were fixed in commit `c84f919`, well before either review's baseline commit. Still the most misleading doc in the repo.
- `Escaper` (follow.py:163-176) is still dead code — superseded by `Escaper2`, never instantiated.
- `signal.signal(SIGINT, cleanup_handler)` is still a module-level import side effect (follow.py:78).
- Zero tests still exist.
- No CLI configurability still exists — tick interval, roster, and symbols are hardcoded in `__main__`.
- Nothing found in dependency-CVE dimensions (no `pip-audit`/`ruff`/`vulture`/`mypy` installed in `.venv` — noted, not blocking, per skill policy of not installing tooling globally without permission).
- Given the codebase is a single ~214-line file, this list stays at 18 findings rather than padding to 30-80 — that reflects actual codebase size.

## Architectural mental model

`follow.py` is the entire application. Since the last review, the central tick loop changed from a hand-rolled `while True: update(); draw(); sleep()` to a `simpy.rt.RealtimeEnvironment`: each animal is now an independent SimPy process (`Mover.run`, defined once on the base class) that loops "move, then `yield env.timeout(self.interval)`", and `World` gained a parallel `draw_loop` process of the same shape. `World.run()` is now purely the setup/launch point — it builds the environment, registers one process per animal plus the draw process, and calls `env.run()`.

This is a scheduling change, not a behavioral one — `move()`/`draw()` themselves are untouched, and the class hierarchy (`Mover` → `RandomMover` → `Follower`/`Escaper`/`Escaper2`) and `__main__` wiring (`prey: Escaper2` ← `hunter: Follower` ← `prey`, + `randy: RandomMover`) are exactly as before. One subtlety worth naming: the old loop guaranteed "every animal moves, then we draw" as a single synchronous step; the new port only preserves that ordering as a side effect of process *registration* order (animals registered before `draw_loop`) combined with `interval == draw_interval` by default, so every process's events land at the same simulated timestamps and animal-move events sort before the draw event at each tick. This is called out and accepted as a "cosmetic non-issue" in `docs/specs/2026-07-13-simpy-port-design.md` — see "Things that look bad but are actually fine" below.

This matches `CLAUDE.md`'s architecture description (the `World` bullet was correctly updated for the port in commit `e4f43ea`). The one place docs and code still diverge is "Known Quirks" (findings #1/#2) — unchanged since the last review, because this pass's commits (`def7329` through `d5aa9da`) never touched that section.

## Phase 1.5: prior reports

Two reports exist in `docs/reviews/`:

- **`code-review_follow.py_2026-07-14.md`** — has frontmatter (`git_sha: 33c4f97`). Per protocol, `git log --oneline 33c4f97..HEAD -- follow.py` shows the file *has* changed since (the SimPy port, commits `e265cf2`/`e4f43ea`), so this report is technically stale for its one in-scope file and its findings are not used as input evidence here. In practice the port only touched `World`'s tick-loop plumbing — `draw()`, `Mover.limit()`, `Escaper`/`Escaper2`, `signal.signal`, and the constructors are byte-for-byte unchanged — so independent re-reading this pass confirms nearly all of that report's findings (curses.wrapper, enumerate, if-chain clamp, dead `Escaper`, `target=None`, `self.quit` dead state, no type hints) still hold against current line numbers. Its two HIGH findings (both `curses.error` corner-cell crashes) are the basis for this review's elevated finding #12 below — re-derived independently rather than copied, per Phase 1.5 rules.
- **`follow_py_2026-06-04.md`** — no frontmatter, still treated as fully stale (unchanged from last review).

Recommend regenerating `code-review_follow.py_2026-07-14.md` against current HEAD so the next `/project-review` run can use it as evidence without the staleness caveat.

## Findings table

| ID | Category | File:Line | Severity | Effort | Description | Recommendation |
|----|----------|-----------|----------|--------|--------------|-----------------|
| 1 | Documentation drift | CLAUDE.md ("Known Quirks") | High | S | Both listed quirks (global `animals` ref, `Escaper2` freeze) were fixed in commit `c84f919`, well before either review baseline. Still misleads anyone treating CLAUDE.md as ground truth. | Remove or rewrite the "Known Quirks" section to match current behavior. |
| 2 | Documentation drift | CLAUDE.md (Escaper2 description) | Medium | S | CLAUDE.md says Escaper2 "otherwise stays still (no random walk either)"; current code (follow.py:189-196) calls `super().move()` unconditionally, so it always wanders and only adds a flee bias when close. | Update to: "always wanders via Perlin noise; adds a directional flee step when within the proximity buffer." |
| 3 | Architectural decay | follow.py:163-176 | Medium | S | `Escaper` is fully superseded by `Escaper2` and never instantiated (`__main__` only builds `Escaper2`). Dead abstraction. | Delete `Escaper`, or document it as an intentional simpler reference implementation. |
| 4 | Architectural decay | follow.py:172-174, 193-195 | Low | S | `Escaper.move()` and `Escaper2.move()` duplicate the identical flee-vector calculation. | Extract a shared `_flee_step()` helper and call it from both. |
| 5 | Consistency rot | follow.py:78 | Medium | S | `signal.signal(SIGINT, cleanup_handler)` executes at module import time, not inside `__main__`. Importing `follow.py` anywhere installs a global SIGINT handler as a side effect. | Move inside `if __name__ == "__main__":`, right before `World(animals).run(...)`. |
| 6 | IDIOM | follow.py:30-37, 67-78 | Medium (idiom floor) | S/M | Curses setup/teardown is hand-rolled instead of `curses.wrapper()`, which guarantees terminal restoration on *any* exception (not just SIGINT) and calls `noecho()`/`cbreak()` for you — neither of which this code calls today. | Wrap the entry point in `curses.wrapper(main)`; drop manual `initscr`/`endwin`/signal-handler plumbing. Also resolves finding #18 (see Top 5). |
| 7 | IDIOM | follow.py:43, 45-47 | Medium (idiom floor) | S | Manual `n = 0` / `n = n + 1` counter numbers legend rows instead of `enumerate(self.animals)`. | `for n, animal in enumerate(self.animals):` |
| 8 | IDIOM | follow.py:105-114 | Medium (idiom floor) | S | `Mover.limit()` clamps with sequential `if` statements, while `Follower`'s integrator clamp (follow.py:158-159) uses the more idiomatic `max(-bound, min(bound, value))` for the same kind of operation. | `self.x = max(0, min(self.x, self.maxx - 1))` (same for `y`). |
| 9 | Test debt | repo-wide | Medium | M | Zero tests exist. `dist()`, `Mover.limit()`, `Follower.move()`'s PI math, and `RandomMover.move()`'s noise-to-coordinate mapping are all pure and curses-independent. The SimPy `run()`/`draw_loop()` generators are also untested. | Add `test_follow.py` covering `dist()`, `limit()` boundary clamping, and a couple of `Follower.move()` ticks against a fixed target. |
| 10 | UX & CLI ergonomics | follow.py:204-214 | Low-Medium | M | Tick interval, animal roster, and symbols/gains are hardcoded in `__main__`. No argparse exists, despite the file's own TODO acknowledging the gap. | Add a minimal `argparse` for `--interval`, and optionally `--kp`/`--ki`. |
| 11 | UX & CLI ergonomics | follow.py:116-118 | Low | S | The legend shows symbol and coordinates (`🐇: 12,4`) but not role (prey/hunter/random). | Include `animal.name` in the legend string. |
| 12 | Error handling & observability | follow.py:36-37, 45, 105-114, 131-138 | **High** *(elevated — see summary)* | S | `Mover.limit()` clamps to `maxx - 1`/`maxy - 1` for single-width chars, but every symbol drawn (`🐇`,`🐕`,`🦋`) is double-width; a clamped position can still put the symbol's second column on the window's true last cell, raising `curses.error`. Worse than previously scoped: `RandomMover.move()` (follow.py:131-138) never calls `self.limit()` at all — `randy` draws at fully unclamped Perlin-derived coordinates, making it the most exposed of the three animals to this crash, not the least. Reachable through ordinary long-running use, not a contrived edge case. | Clamp to `maxx - 2` to leave room for double-width cells, and add the missing `self.limit()` call to `RandomMover.move()`; or wrap `draw()`'s `addstr` calls in `try/except curses.error: pass` as a cheap backstop. |
| 13 | Error handling & observability | follow.py:27-37 | Low | M | Window dimensions are captured once at startup and never revisited; no `SIGWINCH` handling. Resizing mid-run can leave animals outside new (smaller) bounds, tripping #12 on the next `draw()`. | Document as a known startup-only-sizing limitation, or catch `curses.error` in the draw loop. |
| 14 | Type & contract debt | follow.py:166, 185 | Low | M | No type hints anywhere. `target` defaults to `None` with no validation before `move()` dereferences `self.target.x/.y`. Currently safe only because `__main__` always assigns a target first. | Make `target` a required argument instead of `None`-defaulted, at minimum. |
| 15 | Dependency & config debt | requirements.txt:1-2 | Low | S | `noise == 1.2.2` / `simpy == 4.1.2` use non-standard spacing around `==` (PEP 508 style is `noise==1.2.2`) — now applied consistently across both deps. No dev dependencies declared despite historical Black formatting. | Tighten pin spacing; optionally add `requirements-dev.txt` if linting/testing tooling gets adopted (#9). |
| 16 | Documentation drift | follow.py:127-128 | Low | S | Comment "y multiplier bigger because generally maxx >> maxy" next to `self.currenty = random.random() * 100000` describes an initial noise-phase offset, not a per-tick multiplier — both axes increment by `+= 1` identically each tick. | Reword to "y phase offset range is larger" or similar. |
| 17 | **NEW** — Error handling & observability | follow.py:58 | Medium | S | `simpy.rt.RealtimeEnvironment(factor=1.0)` keeps the default `strict=True`, so a single `move()`/`draw()` tick that overruns its 0.1s interval raises `RuntimeError` — a failure mode the pre-port hand-rolled loop never had (a slow frame there just delayed the next `sleep()`, no crash). This is a deliberate, documented tradeoff in `docs/specs/2026-07-13-simpy-port-design.md`, not an oversight — flagged because of #18: if it fires, there's currently no way to know. | Keep `strict=True` (per the design doc's own reasoning), but fix #18 so a violation is actually visible instead of silently exiting 0. |
| 18 | **NEW** — Error handling & observability | follow.py:67-71, 204-214 | **High** | S | `__main__`'s `finally: cleanup()` (follow.py:213-214) unconditionally calls `cleanup()`, which ends with `sys.exit(0)` (follow.py:71). An exception raised inside a `finally` block replaces whatever exception was propagating from the `try` body — so *any* crash during `World(animals).run(...)` (the `curses.error` from #12, or the new `RuntimeError` from #17) is silently discarded and the process exits with status **0**, identical to a clean `ctrl-c`. There is currently no way to distinguish "the user quit" from "the simulation crashed" from the shell or a script wrapping this program. | Adopting `curses.wrapper()` (#6) fixes this for free — `wrapper()` restores the terminal in its own internal `try/finally` but does *not* swallow exceptions; they propagate normally to the caller. If not adopting `curses.wrapper()`, at minimum stop calling `sys.exit(0)` unconditionally inside `cleanup()` — only exit-clean on the SIGINT path, and let other exceptions propagate after terminal teardown. |

## Related tactical findings

- `docs/reviews/code-review_follow.py_2026-07-14.md` — line-level detail on the two `curses.error` crash paths that inform finding #12 above (rated HIGH there too, via the same double-width-glyph corner-cell math), plus `#5`/`#7`/`#8`/`#14` here in tactical form. Technically stale per its `git_sha` (33c4f97) vs. current HEAD (the SimPy port touched `follow.py` since), though manual re-verification this pass confirms its findings still hold against current line numbers — see Phase 1.5 note above. Worth regenerating fresh before the next `/project-review` run.

## Top 5 "if you fix nothing else, fix these"

1. **Stop masking exceptions as clean exits** (#18) — this is the highest-leverage fix in the repo: every other bug on this list (and any future one) is currently invisible because of it.
   ```diff
    if __name__ == "__main__":
   -    try:
   -        ...
   -        World(animals).run(interval=0.1)
   -    finally:
   -        cleanup()
   +    def main(scrn):
   +        World(animals, scrn).run(interval=0.1)
   +    curses.wrapper(main)
   ```
   This single change also resolves #6 (idiom) and #5 (module-level `signal.signal` becomes unnecessary, since `curses.wrapper()` lets `KeyboardInterrupt` propagate cleanly on its own).

2. **Fix the double-width-emoji corner-cell crash** (#12) — concrete, reachable, and worse than previously scoped:
   ```diff
    def limit(self):
   -    if self.x >= self.maxx:
   -        self.x = self.maxx - 1
   +    if self.x >= self.maxx - 1:
   +        self.x = self.maxx - 2   # leave room for a double-width glyph
        ...

    def move(self):  # RandomMover
        self.x = abs(int(n / 2 * self.maxx + self.maxx / 2))
        self.y = abs(int(m / 2 * self.maxy + self.maxy / 2))
   +    self.limit()   # currently missing entirely
   ```

3. **Update `CLAUDE.md`'s "Known Quirks" section** (#1/#2) — still the most misleading doc in the repo, unchanged since last review:
   ```diff
   - ## Known Quirks
   -
   - - `World.draw` references the global `animals` list instead of `self.animals` (line 46) — a bug in the original code.
   - - `Escaper2.move` doesn't call `super().move()` when outside the buffer, so the entity freezes rather than wandering freely when not threatened.
   + (section removed — both issues were fixed in commit c84f919)
   ```

4. **Delete or repurpose `Escaper`** (#3) and dedupe the flee logic (#4) — same diff as the prior review, still unapplied.

5. **Add a small test file** (#9) covering `dist()`, `Mover.limit()` boundary behavior (including the corrected double-width clamp from #12), and a couple of `Follower.move()` ticks.

## Quick wins

- [ ] Fix the `finally: cleanup()` exception-masking pattern, ideally via `curses.wrapper()` (#18, #6)
- [ ] Update `CLAUDE.md`'s "Known Quirks" section to match reality (#1, #2)
- [ ] Move `signal.signal(SIGINT, cleanup_handler)` inside `if __name__ == "__main__":`, or drop it if adopting `curses.wrapper()` (#5)
- [ ] Replace the manual `n`/`n + 1` counter in `World.draw` with `enumerate()` (#7)
- [ ] Use `max(0, min(x, bound))` clamping in `Mover.limit()` to match the style already used for the PI integrator clamp (#8)

## Things that look bad but are actually fine

- **`Mover.move()` is a no-op `pass`.** Deliberate template method — every real subclass overrides it, and the docstring already flags the oddity. Not a finding.
- **`abs()` around the noise-to-coordinate calculation** (follow.py:137-138). Algebraically redundant for `n ∈ [-1, 1]`, but `pnoise1` can occasionally return values slightly outside that range, so this is plausible cheap insurance rather than dead code.
- **`draw_loop` may render mid-tick relative to some animal's move, in principle** (follow.py:50-54, 99-103). The SimPy port makes each animal and the draw step independent processes rather than one synchronous "move all, then draw" step. In practice, with default `interval == draw_interval` and animal processes registered before `draw_loop`, every event lands at identical simulated timestamps and sorts in registration order, so the old ordering guarantee holds today. This coupling is implicit rather than enforced, but it's explicitly named and accepted as a "cosmetic non-issue" in `docs/specs/2026-07-13-simpy-port-design.md` rather than an oversight. Not escalated to a finding; worth a comment in code if `draw_interval` is ever set differently from `interval`, which is already possible via `World.run()`'s signature.
- **The TODO comments at the top of the file** (keyboard input, collision avoidance). Honestly labeled backlog in a solo hobby project, not silently dropped scope. The "Convert to SimPy?" TODO was correctly removed in commit `e4f43ea` once done.
- **`docs/` and `.venv/` are fully gitignored**, including `docs/reviews/*.md`, `docs/specs/*.md`, `docs/plans/*.md`. Matches the documented design of these skills (reports/specs/plans are local, personal artifacts, not meant to be committed). Not a finding.
- **No type hints anywhere in the file.** For a stable ~214-line script with no external consumers, full annotation is more ceremony than value — noted at Low severity (#14) rather than escalated.

## Open questions for the maintainer

- `docs/reviews/code-review_follow.py_2026-07-14.md` is now stale by `git_sha` (predates the SimPy port). Worth regenerating against current HEAD so the next `/project-review` run can use it as clean evidence?
- Is `Escaper` (follow.py:163-176) intentionally kept as a simpler reference implementation alongside `Escaper2`, or dead code from an earlier iteration that should be deleted?
- Is the lack of test coverage acceptable for this project's scope, or worth adding minimal unit tests on the pure-math logic?
- Is the absence of `SIGWINCH`/terminal-resize handling a deliberate, accepted limitation?
- **New this pass:** on the SIGINT path, `cleanup_handler` → `cleanup()` calls `sys.exit(0)` from *inside* `World.run()`'s call stack (raising `SystemExit`), which then also triggers the outer `finally: cleanup()` in `__main__` a second time — a second `curses.echo()`/`curses.endwin()`/`sys.exit(0)` on an already-torn-down curses session. This wasn't verified empirically (curses needs a real terminal, and ctrl-c behavior is timing-dependent), so it's not asserted as a confirmed bug — but if `curses.wrapper()` is adopted per #6/#18, this whole double-cleanup question becomes moot, which is one more argument for that fix.
- `docs/reviews/follow_py_2026-06-04.md` has no frontmatter and every finding in it already appears fixed (per the prior review). Worth deleting now that it's fully resolved?
