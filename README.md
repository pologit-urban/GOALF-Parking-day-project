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
js/main.js          drawer nav, EN/KO switch, scroll reveal, progress bar
site.webmanifest    name + icons for "add to home screen"
assets/icon.svg     tab icon (green tile, white golf flag)
assets/icon-*.png   32px favicon, 180px apple-touch, 512px manifest
assets/img/         artwork rendered from the poster PDF at 400 dpi, then
                    trimmed to each drawing's own content box, so nothing
                    carries the poster's internal padding
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

Sampled from the project poster.

| Token | Hex | Use |
| --- | --- | --- |
| `--green-500` | `#7E9E82` | header band, accents |
| `--green-050` | `#E6EFE3` | mint panels |
| `--cream` | `#F6F1E4` | caption / quote blocks |
| `--card` | `#E3C9A3` | cardboard tiles |
| `--ink` | `#24301F` | text, footer |
| `--white` | `#FFFFFF` | page background |

Background is white; the layout is capped at 460px so it reads as a phone
screen on any device.
