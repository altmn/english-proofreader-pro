## Summary

Describe the change and why it is useful.

## Verification

- [ ] `python3 -m unittest discover -s tests -p 'test_*.py'`
- [ ] `python3 scripts/release.py validate`
- [ ] `python3 scripts/release.py build` (when package inputs or release tooling change)
- [ ] Examples and fixtures use synthetic text only
- [ ] Skill behavior and the under-8,000-character limit remain intentional

## Notes for review

Link related issues and call out behavior, privacy, or packaging impact.
