# Assets

Drop images and your résumé here, then point to them in `../content.py`.
Paths in `content.py` are relative to this folder.

## Recommended files

| File | Used for | Notes |
|------|----------|-------|
| `headshot.jpg` | About page + sidebar logo | Square, ~600×600 px, professional |
| `resume.pdf` | Download button on About + Skills | Keep filename simple |
| `projects/wirelist.png` | SysML Wirelist project card | Screenshot, ~1200 px wide |
| `projects/starlink.png` | Starlink Visualizer project card | Screenshot of the globe |

Create the `projects/` subfolder yourself when you add project screenshots.

Any missing image degrades gracefully to an icon placeholder — the site
always renders.

## Generated artwork (`backgrounds/`)

These SVGs are drawn by hand and used by `../utils/style.py`. You do not need
to touch them, but you can recolour them freely:

| File | Used for |
|------|----------|
| `page-light.svg` / `page-dark.svg` | full-page artwork behind every page |
| `grid-light.svg` / `grid-dark.svg` | the faint blueprint grid tile |
| `hero-horizon.svg` | About / Contact hero — earth curve + aircraft |
| `hero-orbit.svg` | Projects / Memberships hero — orbits + satellites |
| `hero-network.svg` | Experience / Skills hero — systems decomposition |
| `card-sat/globe/hub/rocket/flight.svg` | project card tiles (`"icon"` field) |
| `card-avatar.svg` | headshot placeholder |

Adding your own photos always wins over these — set `"image"` on a project or
`"headshot"` on the profile in `content.py`.
