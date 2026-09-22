# Relocation validation

**Status:** Informative implementation report, 2026-09-22.

The academia application was imported from source commit `b98730b46eca5fdf441937aef0180f5b3d4f94dd` without modifying that repository. Its GRRP v0.1 semantics, canonicalization, identifiers, protocol test vectors, and TypeScript package names remain unchanged. Python `grrp` and TypeScript `@gra/protocol` remain academia-specific packages.

## Relocation changes

- Moved `web` to `web_application` and `grrp` to `domain_packages/grrp`.
- Added a server runtime resolver that derives source and runtime paths independently of the process working directory. The server and account CLI use the same retained database location.
- Set the independent server port to 8001 and the client development proxy to the same port.
- Selected the isolated Python executable with `GRA_PYTHON`, passed as one argument even when the executable path contains spaces. The default environment is `.runtime/environments/academia`.
- Kept retained records and the account database under `.runtime/academia`, outside source and environments. Corrected inherited wording that implied the account database was entirely disposable or that private keys could never exist anywhere on the host.
- Updated demo tool locations; demo seeding requires an explicit separate runtime and server URL. Corrected an inherited malformed string literal in `tools/demo.ts`. Demo seeding was not run against migrated data.
- Preserved the original root README, licensing statement, research documents, and complete Git history. Added current installation documentation, the missing official AGPL licence text, and explicit licensing preservation notes.

## Executed checks

| Check | Result |
|---|---|
| Source archive import | 121 files; initial imported hashes preserved; corrected manifest distinguishes raw blobs, archive export, source worktree, and final relocated bytes |
| Provenance correction | 56 archive exports differ from raw blobs only by LF-to-CRLF conversion; all 121 initial imported hashes independently reproduced |
| Relocation comparison | 111 files unchanged against the initial archive-export import; 10 files contain documented edits |
| Original Git history | 7,255,564-byte bundle; `git bundle verify` succeeds and reports complete history |
| Original repository after import | Same HEAD and clean working tree |
| Python package | Installed editable from the relocated domain package into the isolated environment |
| Python suite | **208 passed, 1 skipped**; the skipped test is a POSIX editor fallback on Windows |
| TypeScript protocol vectors | **43 passed** |
| Relocated Python vector generator | Reproduces the original TypeScript fixture byte for byte |
| Fastify application and path tests | **48 passed**, including 3 new runtime-boundary tests |
| Production build | Protocol, server, and React client builds pass |
| Optional demo tool | TypeScript syntax transform passes; no seeding performed |
| Deep Windows runtime path | Isolated project and question creation both return 201; graph returns 200; `grrp check` succeeds |

The Python tests used a fresh explicit `--basetemp` because the machine's pre-existing shared pytest temporary directory was inaccessible. Windows sandbox ancestor-directory access also blocked esbuild configuration discovery; running the scoped build/test commands outside that sandbox restriction succeeded. Neither issue required changing machine-wide long-path or execution-policy settings.

The server suite creates temporary accounts and projects, invokes the relocated Python implementation, tests Git repositories and record operations, and checks graph behavior. These checks do not certify conformance to the generalized protocol or establish production readiness.

The long-path check used a separate `.runtime/academia-relocation-smoke` tree under the programme, with an in-memory account database. It exercised the new runtime depth without adding records to retained user data. That temporary tree was removed after verification.

## Inherited dependencies and limitations

`npm ci` reproduced the existing lockfile without a dependency upgrade. The npm advisory report on 2026-09-22 reported six affected packages: three high (`@fastify/static`, `drizzle-orm`, `fast-uri`) and three moderate (`fastify`, `vitest`, `@vitest/mocker`). Several suggested fixes require version changes outside the existing declared ranges. A separate dependency-maintenance review is needed before public deployment; advisory presence alone is not a finding that every reported path is exploitable in this application.

Installed Python and Node versions are recorded separately in `installed_dependencies.json`; this is a validation environment record, not a new dependency lock or compatibility guarantee.

The migration preserves application behavior, including existing custody choices and historical documentation. It does not introduce the generalized application's transaction receipts, relation module semantics, concurrency behavior, or standards-alignment claims. Future convergence requires an explicit domain compatibility design.

Actual retained-data backup, transfer, and live-service verification are handled separately by the programme migration. The source import did not include account databases, runtime records, private keys, or generated dependency trees.
