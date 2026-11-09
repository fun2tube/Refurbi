# Instructions for the Refurbi build agent

You are building Refurbi, a refurbished-smartphone retail + counter-distribution platform for India. You run unattended about once an hour. The founder is not watching; they read PROGRESS.md and the hourly summary.

## Source of truth (read every run)
1. docs/CTO_DECISIONS.md - overrides the original blueprint.
2. ROADMAP.md - the ordered task list.
3. PROGRESS.md - previous runs, blockers, notes for next run.

## Each run
1. Read the files above. Run existing test suites; if main is red, fixing it IS this run's task.
2. Pick the first [ ] task in ROADMAP.md. If too big for one run, split into TxxA/TxxB in ROADMAP.md and do the first part.
3. Implement properly: code, migrations, tests. Done only when tests, lint, typecheck and build pass.
4. Tick the task [x] in ROADMAP.md.
5. Append an entry to PROGRESS.md and update its Status block.
6. Commit as `Txx: <summary>` and push.
7. End your final message with the hourly summary line.

## Hard rules
- Never commit secrets. Use .env.example with placeholders. Integrations go behind adapters with fake implementations used in dev/tests.
- Never expose IMEI, purchase cost, supplier, commission or customer PII through public endpoints; add a test for each public endpoint.
- Money is integer paise. Timestamps UTC. All device status changes go through the lifecycle service.
- Never invent business facts (GSTIN, addresses, real prices, ratings, reviews, warranty terms). Use clearly labelled demo seed data and list needs under Founder inputs in PROGRESS.md.
- No claims like 'Apple certified' or '100% original parts' in UI copy.
- If blocked (needs key, business decision, paid service): mark [!], explain in PROGRESS.md, move to next unblocked task.
- Keep the build green. Never leave broken half-done code on the branch.

## PROGRESS.md entry template
### <ISO datetime UTC> - Txx <title>
- Done: ...
- Tests: <counts, pass/fail>
- Decisions made: ...
- Blockers / founder inputs needed: ...
- Next: Tyy

## Hourly summary line (last line of every run)
Refurbi build: <done>/<total> tasks (<pct>%). This hour: Txx <title>. Next: Tyy. Blockers: <none | short list>.
