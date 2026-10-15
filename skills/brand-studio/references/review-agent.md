# Independent review agent

Why: a designer who has looked at their own marks for an hour stops seeing them (letters that read as others, near
copies of known brands, accidental shapes). A fresh agent that knows only the business catches these, provided it is
not told which option you prefer: an agent handed your hypothesis tends to confirm it.

## When
1. **Concept stage**: after the three greyscale sketches are built, audited and rendered, BEFORE showing the user.
2. **Kit stage**: after `build_kit.py`, before handing over (colour, type, favicon sheet, mockups, guidelines pages).
Two rounds maximum per stage. Stop earlier when a round returns no blocker or major findings.

## How
1. Write the client's brief into a file in their words (name, what they do, audience, adjectives, competitors,
   must-work-on list, exclusions). No design opinions in it.
2. `python3 scripts/review_pack.py --brief brief.md --concepts concepts.png --svgs a.svg b.svg c.svg --round 1 --out review/round-1`
3. Spawn ONE sub-agent (Claude Code: Agent tool, `general-purpose` or a design/review type; Codex: spawn an agent) whose
   prompt is the packet. It needs read access to the image and SVG files. Do not add your recommendation. Use a
   strong model (this is judgement work). Do not let it edit files.
4. Read the reply. For each finding decide: **fix** (change the SVG, re-run audit and renders), **dispute** (write
   one line why, e.g. the brief says the opposite), or **note** (cannot be fixed now, e.g. trademark search).
   Blockers and majors are fixed or explicitly disputed in the message to the user; never silently ignored.
5. Round 2: send the changed files with the same packet, `--round 2`, plus a short list of what changed. Same
   agent via SendMessage when available (it keeps context), else a fresh one.
6. In the checkpoint message to the user add a line: "Independent review: N findings, N fixed, N disputed (why)".

## What it is not
It does not replace the user's choice, a trademark search, or looking at the renders yourself. It reviews fit,
craft, distinction and readings; it cannot run searches you did not give it. A reviewer that returns only praise
was probably handed too little: re-send with the competitor names and the "what would a stranger guess" question first.
