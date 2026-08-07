# Gallery artefacts

Real output from a real record, not mock-ups. Regenerate them from scratch:

```bash
bash grrp/examples/walkthrough.sh 1        # builds the trajectory
cd grrp-walkthrough/trust
grrp graph -o …/docs/gallery/trajectory.svg
grrp release <state> && grrp export <release> -o …/docs/gallery/release.md
```

`trajectory.svg` carries its own colours and responds to a dark background. It reaches for nothing:
no scripts, no external references, no fonts to fetch. A drawing of a record that needs no network
should not itself need one.
