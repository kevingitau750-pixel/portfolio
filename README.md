# Personal portfolio — Streamlit

A multi-page portfolio site for an aeronautical engineer: About, Projects,
Experience & education, Skills, Professional memberships, and Contact.

## Structure

```
portfolio/
├── streamlit_app.py        # entry point + top navigation
├── content.py              # <-- EDIT THIS: all text, links, images
├── .streamlit/config.toml  # theme (light + dark, aviation blue)
├── requirements.txt
├── app_pages/              # one script per page
│   ├── about.py
│   ├── projects.py
│   ├── experience.py
│   ├── skills.py
│   ├── memberships.py
│   ├── contact.py
│   └── admin.py            # "Manage" — hidden, password-gated upload area
├── utils/
│   ├── ui.py               # shared rendering helpers + upload resolvers
│   ├── store.py            # upload store (public / private, see below)
│   └── style.py            # the one place custom CSS lives: page-background
│                           #   texture + gradient hero banners + card media
├── uploads/
│   ├── public/             # photo, résumé, certificates — commit this
│   └── private/            # passport, ID — git-ignored, never published
└── assets/
    ├── backgrounds/        # generated SVGs used by style.py (edit colours there)
    └── ...                 # your images + resume.pdf (see assets/README.md)
```

## Visual design

Colours, fonts and radius come from `.streamlit/config.toml` (native theming,
light + dark). `utils/style.py` adds the parts native Streamlit has no
equivalent for, and is the only place custom CSS lives:

- **Page artwork** — `page-light.svg` / `page-dark.svg`: an atmospheric wash,
  orbital tracks, great-circle flight paths, a planetary limb, and (in dark
  mode) a star field, over a faint blueprint grid.
- **Hero banners** — a gradient band per page with one of three artworks:
  `hero-horizon.svg` (earth curve + aircraft), `hero-orbit.svg` (orbits +
  satellites), `hero-network.svg` (systems-decomposition tree).
- **Card media** — `card-sat/globe/hub/rocket/flight.svg`, illustrated tiles
  used when a project has no screenshot. Pick one per project with the
  `"icon"` field in `content.py`.
- **Card surfaces** — bordered cards are frosted panels so text never sits
  directly on the artwork.

All artwork is generated SVG in `assets/backgrounds/`, embedded as data URIs —
no external requests, works offline and on Streamlit Cloud. Any real photo you
drop into `assets/` and reference from `content.py` overrides the generated
placeholder.

Note: Streamlit's hot reload does not reliably pick up edits to modules under
`utils/`. Restart the server after changing `style.py` or `ui.py`.

## Manage — uploading your photo, résumé, certificates and documents

The site has a private upload area at **`/manage`** (e.g.
`http://localhost:8501/manage`). It is registered as a hidden page, so it never
appears in the public navigation, and it is password-gated.

### First-time setup

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set a
password:

```toml
admin_password = "a-long-random-passphrase"
```

`secrets.toml` is git-ignored. On Streamlit Community Cloud, put the same line
in **App settings → Secrets** instead of committing it. With no password set
(or the example value left unchanged) the page refuses all uploads.

### What you can upload

| Tab | Goes where |
|-----|-----------|
| Photo | About page headshot + the site logo |
| Résumé | Download button on About and Skills |
| Certificates | Experience → Certifications & licences |
| Project images | Replaces a project card's illustrated tile |
| Private documents | **Nowhere public** — passport, ID, transcripts |

Uploads beat anything set in `content.py`, so you never have to edit code to
change a picture.

### Public vs private

Two separate stores, `uploads/public/` and `uploads/private/`, each with its
own index. The code that renders the site only ever opens the public index, so
a private document cannot reach a public page even by mistake.
`uploads/private/` is git-ignored — it is never committed and never deployed.
Put your passport, national ID and transcripts there; put your passport-style
*photo* under the Photo tab.

### Persistence

Uploads are written to `portfolio/uploads/`. **Streamlit Community Cloud wipes
the filesystem on every restart and redeploy**, so anything uploaded on the
live site is temporary. To make public files permanent, upload them locally and
commit `uploads/public/` to the repo. If you would rather upload straight on
the live site and have it stick, that needs external storage (S3, Cloudflare
R2, Supabase) — the store in `utils/store.py` is the only module that touches
the filesystem, so that is the one file to swap.

Limits: 15 MB per file; PNG, JPG, WEBP and PDF only. Stored filenames are
randomised, so a crafted filename cannot escape the upload folder.

## Run locally

```bash
cd portfolio
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Editing content

Everything on the site comes from `content.py`. Placeholders start with
`TODO` and are hidden or shown as an "add this in content.py" hint until you
fill them in, so the site always renders.

Add images and a `resume.pdf` under `assets/` — see `assets/README.md`.

## Deploy — Streamlit Community Cloud (free)

1. Push this repo to GitHub.
2. Go to https://share.streamlit.io → New app.
3. Set the main file path to `portfolio/streamlit_app.py`.
4. Deploy — dependencies install from `portfolio/requirements.txt`.

For a custom domain, put it behind a reverse proxy or use a paid host
(Render, Railway, Fly.io, a VM + Nginx).
