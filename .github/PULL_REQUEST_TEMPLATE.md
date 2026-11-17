## Summary

Describe the change and why it is useful.

## Verification

- [ ] `python3 -m unittest discover -s tests -p 'test_*.py'`
- [ ] `python3 scripts/release.py validate`
- [ ] `python3 scripts/release.py build` (when package inputs or release tooling change)
- [ ] Examples and fixtures use synthetic text only
- [ ] Skill behavior remains intentional and the skill meets the UTF-8 byte ceiling

## Notes for review

Link related issues and call out behavior, privacy, or packaging impact.
