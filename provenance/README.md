# Academia import provenance

**Status:** Informative preservation record, 2026-09-22.

The import contains 121 committed source files from `b98730b46eca5fdf441937aef0180f5b3d4f94dd` in `git@github.com:huangwanhong-maker/Generative-Relational-Academia-Application.git`. The original working tree was clean when inspected and was not modified by this import.

The import baseline was captured **before relocation edits**. The [corrected import manifest](import_manifest.json) distinguishes raw Git blob bytes, Git archive export bytes, source working-tree bytes, the initial imported bytes, and the final relocated bytes. Every form has its own SHA-256 hash and byte length. The import used `git archive` output; it did not copy raw Git blob bytes directly.

A subsequent independent audit identified an incorrect label in the initial manifest: `committed_sha256` described archive export bytes, and the accompanying text called them committed bytes. Git's archive export converted LF to CRLF in 56 of the 121 files in this Windows configuration. The correction recomputed all raw blob hashes with `git cat-file blob`, verified that a fresh archive matched all 121 initial imported hashes, and recorded the distinction explicitly. The initial manifest is preserved verbatim as [import_manifest.initial.json](import_manifest.initial.json), an explicitly superseded record whose original labels remain incorrect. Its hash and the correction details appear in the corrected manifest.

The baseline `imported_sha256` values have not changed. After relocation, **111 files remain byte-identical to that initial archive-export import**, and 10 have documented edits. This count does not claim byte identity with the raw Git blobs. The [relocation change inventory](relocation_changes.json) uses the initial imported bytes as its before-edit basis and records final hashes separately.

| Original path | Imported path |
|---|---|
| `web/` | `web_application/` |
| `grrp/` | `domain_packages/grrp/` |
| `README.md` | `docs/history/original_README.md` |
| Other tracked paths | Same relative path |

`original-history.bundle` contains all source Git references and their reachable history, created with `git bundle create --all` and successfully checked with `git bundle verify`. It is a portable history archive, separate from the parent programme's working-tree history. It does not pretend that the imported files were always at their new paths.

```powershell
git bundle verify provenance/original-history.bundle
# Restore into a NEW directory when the original layout or history is needed:
git clone provenance/original-history.bundle <new-restore-directory>
```

The source archive excludes untracked and ignored state. No `.git` directory, virtual environment, `node_modules`, build output, account database, record runtime, private key file, or `.env` file was copied as source. An all-history tracked-path audit found no runtime database or private-key paths. This path audit is not a claim that a comprehensive secret scan was performed.

Runtime migration is a separate operation managed by the programme: `.runtime/academia` holds retained application state, while `.runtime/environments/academia` holds the recreated Python environment. Neither belongs in this source bundle.

The [validation report](relocation_validation.md) distinguishes relocation changes from inherited implementation limitations. The root README and runtime helper describe current launch paths; imported plans and papers remain historical material and may use the earlier layout or describe unfinished work.
