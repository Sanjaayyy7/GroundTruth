## What and why

<!-- Engineering intent: what does this change, and what evidence motivates it? -->

## Release-procedure checklist (Constitution Law 13)

- [ ] `pytest -q` green
- [ ] `groundtruth audit` rc 0
- [ ] `groundtruth audit --root examples/minijudge --name minijudge` rc 0
- [ ] `groundtruth steward` rc 0
- [ ] Derived artifacts regenerated and committed (`git diff` clean over
      declared `derived_artifacts` paths — CI diffs them)
- [ ] Working tree clean after all of the above

## Constitution

- [ ] No new tracked file, **or** the declarations block in
      `docs/CONSTITUTION.md` is amended in this same commit with the
      justification in the commit message (Law 2, catch-none roles)
- [ ] No new claim, **or** the claim is registered in `docs/claims.yaml`
      with evidence path and threat references

## Published numbers

- [ ] No detector/behavior change, **or** the pinned quality numbers were
      deliberately updated with the regression test
