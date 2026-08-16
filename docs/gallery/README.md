# Gallery

Real output from a real record, not mock-ups.

| file | what it is | made by |
|---|---|---|
| `01-front-page.png` … `08-search.png` | the hosted interface, signed out and signed in | `node web/tools/gallery.mjs`, against a running server |
| `trajectory.svg` | a trajectory drawn from the record | `grrp graph -o trajectory.svg` |
| `release.md` | the document a release emits | `grrp export` |

To remake the screenshots:

```bash
cd web
npm run account --workspace @gra/server -- add ada --password '…'
npm run dev                  # in one terminal
node tools/gallery.mjs       # in another; needs a project with some work in it
```

The script needs `puppeteer`, which is deliberately **not** a dependency of anything —
`npm install -D --no-save puppeteer` when you want it. A gallery tool should not be
something the project needs in order to build.
