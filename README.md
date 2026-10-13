# GO(A)LF — Park(ing) Day Project Site

A mobile-sized (phone-width) one-page site for the **GO(A)LF** Park(ing) Day
installation — Urban Ecology, University of Utah (CMP 4280).

GO(A)LF combines a wish activity with a simple mini-golf experience: visitors
write a personal goal, seal it in a gatchapon capsule, putt it down the course,
and the selected wishes go up on the GO(A)LF board.

## Stack

Plain HTML / CSS / JavaScript — no build step. Open `index.html`, or serve it:

```bash
python3 -m http.server 8000
# → http://localhost:8000
```

## Structure

```
index.html          single page: concept → how it works → interaction →
                    details → making process → materials → installation →
                    poster sheets → budget
css/style.css       palette + layout (phone-width shell, max 460px)
js/main.js          drawer nav, EN/KO switch, tap-to-enlarge lightbox,
                    scroll reveal, progress bar
site.webmanifest    name + icons for "add to home screen"
assets/goalf-logo.png     the project logo (poster design team)
assets/logo-uofu.png      the university mark, for dark backgrounds only
assets/icon.svg     tab icon (green tile, red golf flag)
assets/icon-*.png   32px favicon, 180px apple-touch, 512px manifest
assets/img/         artwork rendered from the poster PDF at 400 dpi, split
                    into its individual drawings and trimmed to each one's
                    own content box — a poster panel is a wide strip and
                    becomes unreadable at phone width, so the slope (3),
                    chair (6) and site application (4) are separate steps
.work/extract.py    the extraction script (untracked); re-run it to rebuild
                    assets/img from the poster PDF
assets/GOALF-poster.pdf   the submitted poster, linked for download
```

All imagery is rendered straight from the original poster PDF, so the
drawings stay sharp instead of being photographs of a printed sheet.

## Languages

The page ships in English; every translatable element also carries a
`data-ko` attribute with the Korean text. `js/main.js` swaps the two,
remembers the choice in `localStorage`, and sets `<html lang>` so the
Korean typography rules in the stylesheet apply. First-time visitors
whose browser is set to Korean get Korean automatically.

To change a Korean string, edit the `data-ko` attribute next to the
English text — the two always live side by side.

## Palette

Taken from the GO(A)LF logo the poster team made.

| Token | Hex | From the logo |
| --- | --- | --- |
| `--red` | `#E5211C` | the flag — fills and the footer wordmark |
| `--red-ink` | `#C21A16` | the same red, dark enough for small text |
| `--green-500` | `#3F723F` | the `(A)` — section bands, buttons, primary |
| `--green-700` | `#2D5A30` | the tree — labels and headings on light |
| `--green-300` | `#A3C968` | the grass — highlights on dark |
| `--plate` | `#D8DDC9` | the logo's own field, behind the lockup |
| `--cream` | `#F8F2DC` | the bunker sand |
| `--ink` | `#272725` | the `LF` — body text and the footer |
| `--green-100` | `#DFECDE` | kept: the poster artwork's own green |

Background is white; the layout is capped at 460px so it reads as a phone
screen on any device.
