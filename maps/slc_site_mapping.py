#!/usr/bin/env python3
"""Site mapping figure for the Salt Lake City panel.

Three daylighting projects along City Creek and the Jordan River, drawn on a
downtown base map with a legend, scale bar and a row of site summaries -- the
Salt Lake counterpart to the Cheonggyecheon mapping panel.

Usage:
    python3 slc_site_mapping.py --outdir out

Set an Overpass mirror with --overpass-url or OVERPASS_URL; the default
overpass-api.de is unreachable from sandboxed networks.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import osmnx as ox
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch

# Map extent: downtown and the west side, wide enough to hold all three sites
# plus the Jordan River corridor they drain toward.
WEST, SOUTH, EAST, NORTH = -111.950, 40.736, -111.865, 40.781

SITES = [
    {
        "n": 1,
        "lat": 40.7722146,
        "lon": -111.8877012,
        "name": "City Creek Park",
        "year": "1995",
        "label_offset": (0.004, 0.0035),
        "bullets": [
            "Canyon Road, below Memory Grove",
            "Creek piped since the early 1900s",
            "Church parking lot swapped to the city",
            "US$2.26m — green space with a creek as ornament",
        ],
    },
    {
        "n": 2,
        "lat": 40.7417148,
        "lon": -111.9174261,
        "name": "Three Creeks Confluence",
        "year": "2021",
        "label_offset": (0.004, -0.004),
        "bullets": [
            "1300 S / 900 W, at the Jordan River",
            "Red Butte, Emigration and Parley’s uncovered",
            "c. 61 m daylighted",
            "US$3m — SLC Public Lands with Seven Canyons Trust",
        ],
    },
    {
        "n": 3,
        "lat": 40.7690,
        "lon": -111.9115,
        "name": "City Creek at Folsom Trail",
        "year": "2022–",
        "label_offset": (0.0035, 0.0035),
        "bullets": [
            "700–1000 West, a disused rail corridor",
            "Trail opened 2022; 300 ft mural 2023",
            "Creek still underground — design plan 2024",
            "Awaits funding",
        ],
    },
]

# Faint context labels, as the reference panel labels its districts.
DISTRICTS = [
    ("Capitol Hill", 40.7775, -111.8905),
    ("Downtown", 40.7645, -111.8920),
    ("Fairpark", 40.7735, -111.9270),
    ("Poplar Grove", 40.7545, -111.9305),
    ("Glendale", 40.7405, -111.9330),
]

C = {
    "urban": "#f1ede6",
    "street": "#ffffff",
    "street_edge": "#dcd7cd",
    "arterial": "#ffffff",
    "arterial_edge": "#ccc6b9",
    "park": "#cfe3c4",
    "park_edge": "#b4d0a5",
    "water": "#a8cfe8",
    "water_edge": "#6ba8d4",
    "creek": "#2f80c2",
    "creek_culvert": "#8fbddd",
    "river": "#2f80c2",
    "marker": "#cf3a2e",
    "text": "#1f2933",
    "muted": "#7b8794",
    "box_edge": "#c7c2b8",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--outdir", type=Path, default=Path("out"))
    p.add_argument("--basename", default="slc_site_mapping")
    p.add_argument("--width", type=float, default=15.0, help="figure width in inches (default: 15)")
    p.add_argument("--dpi", type=int, default=300)
    p.add_argument("--no-streets", action="store_true")
    p.add_argument("--no-boxes", action="store_true", help="omit the row of site summaries")
    p.add_argument("--title", default="Site Mapping: Salt Lake City")
    p.add_argument("--overpass-url", default=os.environ.get("OVERPASS_URL"))
    p.add_argument("--timeout", type=int, default=240)
    return p.parse_args(argv)


def fetch(label, fn, *a, **k):
    print(f"  fetching {label} ... ", end="", flush=True)
    try:
        gdf = fn(*a, **k)
    except Exception as exc:  # noqa: BLE001
        print(f"failed ({type(exc).__name__}: {exc})")
        return None
    if gdf is None or gdf.empty:
        print("nothing found")
        return None
    print(f"{len(gdf)} features")
    return gdf


def subset(gdf, types):
    if gdf is None:
        return None
    out = gdf[gdf.geometry.type.isin(types)]
    return out if not out.empty else None


def draw_scalebar(ax, lat, km=1.0):
    """A scale bar in kilometres, sized for this latitude."""
    deg = km / (111.320 * math.cos(math.radians(lat)))
    x0 = EAST - 0.030
    y0 = SOUTH + 0.0045
    h = 0.0011
    for i in range(2):
        ax.add_patch(
            plt.Rectangle(
                (x0 + i * deg / 2, y0), deg / 2, h,
                facecolor="#ffffff" if i else C["text"],
                edgecolor=C["text"], linewidth=0.7, zorder=20,
            )
        )
    for frac, lbl in ((0, "0"), (0.5, f"{km/2:g}"), (1, f"{km:g} km")):
        ax.text(
            x0 + frac * deg, y0 + h * 2.2, lbl, ha="center", va="bottom",
            fontsize=7.5, color=C["text"], zorder=20,
        )


def draw_north_arrow(ax):
    x, y = EAST - 0.0075, NORTH - 0.010
    ax.annotate(
        "", xy=(x, y), xytext=(x, y - 0.0062),
        arrowprops=dict(arrowstyle="-|>", color=C["text"], linewidth=1.3), zorder=20,
    )
    ax.text(x, y + 0.0008, "N", ha="center", va="bottom", fontsize=9.5,
            fontweight="bold", color=C["text"], zorder=20)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.overpass_url:
        ox.settings.overpass_url = args.overpass_url.rstrip("/")
    ox.settings.requests_timeout = args.timeout
    ox.settings.overpass_settings = f"[out:json][timeout:{args.timeout}]"
    ox.settings.use_cache = True
    ox.settings.log_console = False

    bbox = (WEST, SOUTH, EAST, NORTH)
    print(f"Overpass endpoint: {ox.settings.overpass_url}")
    print(f"Extent: {bbox}")
    print("Querying OpenStreetMap ...")

    waterways = subset(
        fetch("waterways", ox.features_from_bbox, bbox,
              tags={"waterway": ["river", "stream", "canal", "ditch", "drain"]}),
        ["LineString", "MultiLineString"],
    )
    water = subset(
        fetch("water bodies", ox.features_from_bbox, bbox,
              tags={"natural": ["water"], "waterway": ["riverbank"]}),
        ["Polygon", "MultiPolygon"],
    )
    parks = subset(
        fetch("green space", ox.features_from_bbox, bbox,
              tags={"leisure": ["park", "garden", "nature_reserve"], "landuse": ["grass", "cemetery"]}),
        ["Polygon", "MultiPolygon"],
    )

    streets = arterials = None
    if not args.no_streets:
        # A full drive network is more than a public Overpass mirror will serve
        # for this bbox, and residential streets are noise at this scale -- the
        # grid only has to place the sites. Tertiary and up is one light query.
        roads = subset(
            fetch("roads", ox.features_from_bbox, bbox,
                  tags={"highway": ["motorway", "trunk", "primary", "secondary", "tertiary",
                                    "motorway_link", "trunk_link", "primary_link", "secondary_link"]}),
            ["LineString", "MultiLineString"],
        )
        if roads is not None:
            big = roads["highway"].astype(str).str.contains("motorway|trunk|primary")
            arterials, streets = roads[big], roads[~big]
            arterials = arterials if not arterials.empty else None
            streets = streets if not streets.empty else None

    aspect = 1.0 / math.cos(math.radians((SOUTH + NORTH) / 2.0))
    map_ratio = ((NORTH - SOUTH) * aspect) / (EAST - WEST)
    map_h = args.width * map_ratio
    box_h = 0.0 if args.no_boxes else 2.5
    fig_h = map_h + box_h + 1.25

    print("Rendering ...")
    fig = plt.figure(figsize=(args.width, fig_h), facecolor="white")
    top = 1 - 0.62 / fig_h
    map_bottom = (box_h + 0.5) / fig_h
    ax = fig.add_axes([0.035, map_bottom, 0.93, top - map_bottom])
    ax.set_facecolor(C["urban"])

    if parks is not None:
        parks.plot(ax=ax, facecolor=C["park"], edgecolor=C["park_edge"], linewidth=0.3, zorder=2)
    if streets is not None:
        streets.plot(ax=ax, color=C["street_edge"], linewidth=1.3, zorder=3)
        streets.plot(ax=ax, color=C["street"], linewidth=0.7, zorder=4)
    if arterials is not None:
        arterials.plot(ax=ax, color=C["arterial_edge"], linewidth=2.6, zorder=5)
        arterials.plot(ax=ax, color=C["arterial"], linewidth=1.7, zorder=6)
    if water is not None:
        water.plot(ax=ax, facecolor=C["water"], edgecolor=C["water_edge"], linewidth=0.5, zorder=7)

    # Culverted reaches dashed: the panel's whole argument is that City Creek
    # runs underground through downtown, so a buried reach must not read the
    # same as an open one.
    if waterways is not None:
        culvert = None
        for col in ("tunnel", "covered"):
            if col in waterways.columns:
                flag = waterways[col].notna() & (waterways[col].astype(str) != "no")
                culvert = flag if culvert is None else (culvert | flag)
        if culvert is None:
            culvert = waterways.geometry.isna()
        open_w, buried = waterways[~culvert], waterways[culvert]
        if not open_w.empty:
            open_w.plot(ax=ax, color=C["creek"], linewidth=2.3, zorder=8, capstyle="round")
        if not buried.empty:
            buried.plot(ax=ax, color=C["creek_culvert"], linewidth=1.9,
                        linestyle=(0, (4, 2.5)), zorder=8)
        print(f"  open channel: {len(open_w)} | culverted: {len(buried)}")

    for name, lat, lon in DISTRICTS:
        ax.text(lon, lat, name, fontsize=9.5, color=C["muted"], style="italic",
                ha="center", va="center", zorder=9)

    for s in SITES:
        dx, dy = s["label_offset"]
        ax.plot(s["lon"], s["lat"], "o", markersize=15, color=C["marker"],
                markeredgecolor="white", markeredgewidth=1.6, zorder=15)
        ax.text(s["lon"], s["lat"], str(s["n"]), color="white", fontsize=9,
                fontweight="bold", ha="center", va="center", zorder=16)
        ax.text(
            s["lon"] + dx, s["lat"] + dy, f"{s['name']}\n{s['year']}",
            fontsize=10, fontweight="bold", color=C["text"],
            ha="left", va="center", zorder=16, linespacing=1.35,
            bbox=dict(boxstyle="round,pad=0.32", facecolor="white",
                      edgecolor=C["box_edge"], linewidth=0.6, alpha=0.93),
        )

    legend_items = [
        Line2D([0], [0], color=C["creek"], lw=2.3, label="Creek / river, open channel"),
        Line2D([0], [0], color=C["creek_culvert"], lw=1.9, ls=(0, (4, 2.5)), label="Culverted / piped reach"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=C["marker"],
               markeredgecolor="white", markersize=10, label="Daylighting site"),
        Patch(facecolor=C["park"], edgecolor=C["park_edge"], label="Green space"),
        Patch(facecolor=C["urban"], edgecolor=C["box_edge"], label="Surrounding urban area"),
    ]
    leg = ax.legend(handles=legend_items, loc="upper left", fontsize=8.5,
                    frameon=True, framealpha=0.95, borderpad=0.7, labelspacing=0.55)
    leg.get_frame().set_edgecolor(C["box_edge"])
    leg.get_frame().set_linewidth(0.7)
    leg.set_zorder(20)

    draw_north_arrow(ax)
    draw_scalebar(ax, (SOUTH + NORTH) / 2)

    ax.set_xlim(WEST, EAST)
    ax.set_ylim(SOUTH, NORTH)
    ax.set_aspect(aspect)
    for sp in ax.spines.values():
        sp.set_edgecolor(C["box_edge"])
        sp.set_linewidth(0.8)
    ax.set_xticks([])
    ax.set_yticks([])

    fig.text(0.035, 1 - 0.30 / fig_h, args.title, ha="left", va="top",
             fontsize=17, fontweight="bold", color=C["text"])
    fig.text(0.035, 1 - 0.56 / fig_h,
             "City Creek and the Jordan River — three daylighting projects, 1995 to present",
             ha="left", va="top", fontsize=10.5, color=C["muted"])

    if not args.no_boxes:
        gap, left, right = 0.018, 0.035, 0.965
        w = (right - left - gap * (len(SITES) - 1)) / len(SITES)
        for i, s in enumerate(SITES):
            x = left + i * (w + gap)
            bh = (box_h - 0.35) / fig_h
            by = 0.28 / fig_h
            fig.patches.append(
                FancyBboxPatch(
                    (x, by), w, bh, boxstyle="round,pad=0.004",
                    transform=fig.transFigure, facecolor="#faf8f4",
                    edgecolor=C["box_edge"], linewidth=0.8, zorder=1,
                )
            )
            fig.text(x + 0.012, by + bh - 0.30 / fig_h, f"{s['n']}", fontsize=10,
                     fontweight="bold", color="white", ha="center", va="center", zorder=4,
                     bbox=dict(boxstyle="circle,pad=0.34", facecolor=C["marker"], edgecolor="none"))
            fig.text(x + 0.026, by + bh - 0.30 / fig_h, f"{s['name']}  ({s['year']})",
                     fontsize=10.5, fontweight="bold", color=C["text"],
                     ha="left", va="center", zorder=4)
            for j, b in enumerate(s["bullets"]):
                fig.text(x + 0.012, by + bh - (0.62 + j * 0.30) / fig_h, f"•  {b}",
                         fontsize=8.8, color=C["text"], ha="left", va="center", zorder=4)

    fig.text(0.965, 0.10 / fig_h, "Data: OpenStreetMap contributors (ODbL)",
             ha="right", va="bottom", fontsize=7.5, color=C["muted"])

    args.outdir.mkdir(parents=True, exist_ok=True)
    svg = args.outdir / f"{args.basename}.svg"
    png = args.outdir / f"{args.basename}.png"
    fig.savefig(svg, format="svg", facecolor="white")
    fig.savefig(png, format="png", dpi=args.dpi, facecolor="white")
    plt.close(fig)
    for p in (svg, png):
        print(f"wrote {p} ({p.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
