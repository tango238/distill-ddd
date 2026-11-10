# untie-export (golden fixtures)

`docs/domain/*.md` written by [Untie](https://github.com/tango238/untie)'s
"ドメインモデルを書き出す (distill-ddd)" for its ネットショップ sample.

`scripts/test_diagrams.py` (`test_untie_export_golden`) reads these files with
`diagrams.py` / `build_site.py` and checks that contexts, relations, aggregates,
commands, events and the glossary are still picked up. If a parser regex changes
in a way that drops them, that test fails here — before Untie users notice.

The same files live in Untie as a snapshot
(`packages/core/src/model/__tests__/__fixtures__/domain-export/`). When Untie
changes its export format, replace these files with that snapshot and re-run
`python3 scripts/test_diagrams.py`.

This directory is test data only; `install.sh` / `install.ps1` do not copy it.
(`README.md` here is not part of the fixture and is ignored by the test.)
