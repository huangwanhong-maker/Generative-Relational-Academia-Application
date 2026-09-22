# Generative Relational Academia

**Class:** Domain application and development guide  
**Status:** Experimental application retaining native GRRP v0.1

Generative Relational Academia records research as an evolving trajectory: questions, positions, objections, transformations, decisions and connections can remain inspectable alongside the material through which inquiry develops. The web application presents projects, trajectories and record workspaces; the native Python implementation also supports local command-line use.

This repository is the academia application within the Generativity Standards Program. Its existing GRRP identifiers, signatures, transition rules and domain behavior are preserved. Alignment with the generalized application's record protocol remains separate design and implementation work. Imported theoretical papers retain their historical role; the current programme manuscripts and recorded decisions guide programme-level interpretation.

## Current capabilities

- Browse shared projects and search their records; signed-in users can create and operate their own projects.
- Open questions within a project and follow the trajectories of identified states and transitions.
- Explore graph views, select a record or connection, and inspect its record, disclosure and workspace panels.
- Retain research material and working content beside the relevant subject rather than only at project level.
- Invoke native research acts through the interface and Python CLI, including claims, challenges, transformations, decisions and connections.
- Use native GRRP validation, signatures, registrations, disclosure declarations and portable record tooling within that protocol's existing scope.

The [web guide](web_application/README.md) explains the hosted model, and the [Python package guide](domain_packages/grrp/README.md) documents the CLI. Search is a filtering facility rather than a participant or trajectory ranking. A cryptographically valid or well-formed record does not by itself establish that the recorded claim is true.

## Repository layout and authority

~~~text
gr_academia_application/                This application Git repository
├── web_application/
│   ├── packages/client/               React and Vite interface
│   ├── packages/server/               Fastify host, accounts, SQLite and record operations
│   └── packages/protocol/             Native @gra/protocol TypeScript implementation
├── domain_packages/grrp/              Native Python implementation and CLI
├── provenance/                       Import manifest and original Git history bundle
├── docs/                             Interface guides and historical overview
├── notes/  plans/  papers/            Imported domain research and design history
└── LICENSE  LICENSE.md  CONTRIBUTORS.md
~~~

The application is a submodule of [applicative_infrastructure](../README.md), which pins a specific revision. Its original Git ancestry is retained, and the [provenance guide](provenance/README.md) records the original source commit, archived bundle and path mapping. The original overview remains in [docs/history/original_README.md](docs/history/original_README.md); its historical status and licensing statements should be read with the current scope notes.

Native Python grrp and TypeScript @gra/protocol remain domain packages. This application does not yet use the common generalized record protocol or Git transaction implementation. It has independent accounts, permissions and runtime records. Links to the parent [Programme Brief](../../PROGRAMME_BRIEF.md) and [specifications](../../specifications/) resolve when the complete programme is checked out.

## Install and run

Use Python 3.11 or later, Git, and Node.js/npm. Node 22.12 or later on the Node 22 release line supports the current frontend tools and matches the validated major version.

The supported combined setup runs from the **parent infrastructure directory**, with its application submodules initialized:

~~~powershell
python common/tools/setup_application.py academia --dev
python common/tools/run_application.py academia
~~~

Open **http://127.0.0.1:8001**. Setup creates a separate Python environment, installs the relocated native package, installs the npm lockfile and builds the protocol, server and client. The development option includes Python test dependencies. It does not create demonstration accounts or seed research records.

The shared tools belong to the infrastructure repository. A clone of this application alone contains its Python and Node sources but not those tools or the predefined environment layout. For a manually configured installation, install the Python package, run npm's lockfile installation/build in the web workspace, and provide explicit absolute paths for the runtime and Python interpreter.

After setup, the compiled server can be launched directly:

~~~powershell
node "<absolute-academia-directory>/web_application/packages/server/dist/main.js"
~~~

Defaults are resolved from source location instead of shell working directory. The default interpreter still expects the parent infrastructure environment unless GRA_PYTHON selects another installed interpreter.

For interface development, run these in separate terminals from this application's web_application directory:

~~~powershell
npm.cmd run dev --workspace @gra/server
npm.cmd run dev --workspace @gra/client
~~~

Use npm on POSIX. The optional Vite client uses port 5174 and proxies API requests to the server on port 8001.

## Accounts

Academia preserves its existing account-provisioning behavior. When public registration is closed, the operator CLI creates accounts. From this application's web_application directory:

~~~powershell
npm.cmd run account --workspace @gra/server -- list
npm.cmd run account --workspace @gra/server -- add "<account-name>" --password "<chosen-password>" --party "<user-generated-public-party-key>"
~~~

Replace placeholders locally. The password must be at least eight characters; the current CLI accepts it as a command argument, so shell history and process visibility need consideration. Supplying a party key generated by the participant avoids the CLI generating and displaying a private key. Omitting the party flag invokes the existing key-generation bootstrap flow.

The same runtime configuration applies to the server and account CLI. Accounts represent access to this host, while native record identities and signing material have their own custody. Account database columns alone do not establish that a host cannot sign for a party: native record directories can contain private keys.

## Runtime configuration and backups

Default locations below are relative to the parent infrastructure directory.

| Variable | Default | Purpose |
|---|---|---|
| GRA_RUNTIME | .runtime/academia | Parent runtime |
| GRA_RECORDS | .runtime/academia/records | Native record trees, Git histories, material and keys |
| GRA_DB | .runtime/academia/index.sqlite | Retained accounts plus rebuildable indexes |
| GRA_PYTHON | .runtime/environments/academia/Scripts/python.exe on Windows; bin/python on POSIX | Interpreter with the native Python package installed |
| GRA_CLIENT | gr_academia_application/web_application/packages/client/dist | Built client |
| GRA_HOST / GRA_PORT | 127.0.0.1 / 8001 | Direct-server address |

Supply absolute paths for location overrides. The shared launcher selects host and port through its command arguments. GRA_PYTHON is one executable path and supports spaces; GRA_GRRP remains the legacy simple-command override. The session cookie is gra_session, distinct from generalized's cookie.

Back up the complete account database and records tree, including private key material and active journals, with appropriate access restrictions. Stop the writer for a filesystem backup or use a verified online procedure. Accounts are not reconstructable from the derived record index. Source history, npm dependencies and virtual environments cannot replace a runtime backup.

Relocation preserved the existing three academia accounts, two projects and five trajectories without altering native record semantics. Those are properties of the migrated local runtime; source clones contain none of that private data. The original source checkout/runtime remains separate and unchanged. See [migration evidence](../common/design/migration_verification.md) for the backup and comparison boundary.

## Verification

After development setup, from this application directory on PowerShell:

~~~powershell
& ../.runtime/environments/academia/Scripts/python.exe -m pytest domain_packages/grrp/tests --basetemp ../.runtime/test-output/academia -q
npm.cmd --prefix web_application test
npm.cmd --prefix web_application run build
~~~

Use bin/python and npm on POSIX. The test-output directory is disposable and must not name retained user data. The native Python and TypeScript vector suites check agreement on protocol identifiers.

The [relocation validation report](provenance/relocation_validation.md) records **208 Python tests passed, one platform-specific skip, 43 TypeScript protocol tests passed and 48 server tests passed**, plus a production build and isolated deep-path record operations. These assess the native domain application; they do not verify a generalized-protocol adapter.

## Current limits and next work

The inherited lockfile's dated migration audit reports six affected npm packages. Dependency maintenance remains open. Native identity/custody choices, disclosure behavior, account recovery and production operation also need dedicated review before broader deployment.

Generalized transaction receipts, modules, concurrency behavior and epistemic recording requirements are not automatically supplied by relocating this application. Future alignment needs an explicit preservation mapping, including signed bytes, native identifiers, registrations, disclosure and unmapped content. Avoid rewriting imported records or papers to make them appear to have used later programme concepts.

Demo tools create accounts and research records. Use a separate explicitly configured runtime when exercising them; they are not setup prerequisites.

## Contributing and license

Commit academia source changes here, then update the application reference in infrastructure and its reference in the programme. Keep native protocol vectors and preservation tests alongside behavioral changes. Record cross-domain mapping decisions in the programme and shared design material rather than silently changing domain meaning.

Project-authored software, documentation and research material are available under the [MIT License](LICENSE), with copyright held by contributors recorded in [CONTRIBUTORS.md](CONTRIBUTORS.md). [LICENSE.md](LICENSE.md) and [licensing provenance](provenance/LICENSING_NOTES.md) explain the additional grant and retained historical notices. Third-party components and user-created research records retain their own terms.
