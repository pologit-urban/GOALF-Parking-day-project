# GO(A)LF — Park(ing) Day Project Site

A mobile-sized (phone-width) one-page site for the **GO(A)LF** Park(ing) Day
installation, made for **CMP 4280**.

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
index.html        single page: concept → how it works → details →
                  making process → materials → budget → installation
css/style.css     palette + layout (phone-width shell, max 460px)
js/main.js        drawer nav, scroll reveal, reading-progress bar
assets/           poster sheets 01 & 02
```

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
