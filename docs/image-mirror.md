# Cloudflare scan-image mirror

The public review interface remains on GitHub Pages. Its scan images are served
separately by the Direct Upload Cloudflare Pages project
[`nippo-jisho-images.pages.dev`](https://nippo-jisho-images.pages.dev/). This
separation keeps the Git repository and routine UI deployments small while
removing Gallica availability and rate limiting from the reading loop.

## Published assets

All 651 Gallica leaves are published at three stable paths:

```text
scans/native/f0017.jpg   downloaded native-resolution master
scans/1000/f0017.jpg     fast preview
scans/2200/f0017.jpg     normal reading image
```

The deployment root also contains `manifest.json`, including dimensions,
paths, and the original Gallica page URL for every leaf. Image responses permit
cross-origin use and carry a one-year immutable browser-cache policy. Filenames
and image contents must therefore remain immutable; a changed scan should use a
new path or an explicit cache-busting version.

The mirror preserves the downloaded scan pixels. Attribution is presented in
the review interface, this repository, the mirror landing page, and links to
the original Gallica object; it is not burned into the source image.

> Source gallica.bnf.fr / Bibliothèque nationale de France

## Building and deploying

The local Gallica acquisition must first contain all 651 masters. Build the
static directory with:

```sh
python3 scripts/build_image_mirror.py
```

Generated 1000px and 2200px variants are retained under the ignored
`.cache/image-mirror/` directory. The disposable deployment tree is written to
the ignored `build/nippo-jisho-images/` directory. Native masters are hard-linked
where the filesystem permits, so constructing the tree does not consume a
second gigabyte locally.

After inspecting the build, deploy it with the authenticated Wrangler client:

```sh
npx wrangler pages deploy build/nippo-jisho-images \
  --project-name nippo-jisho-images \
  --branch main
```

The binary assets are deliberately not committed to Git. Cloudflare's upload
manifest avoids retransmitting asset hashes already held by the service during
later direct deployments.
