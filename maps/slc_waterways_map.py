#!/usr/bin/env python3
"""Render a map of Salt Lake City's waterways from OpenStreetMap data.

Draws the rivers, creeks and irrigation canals that run through the Salt Lake
valley -- the Jordan River and the canyon creeks that feed it (City Creek, Red
Butte, Emigration, Parley's, Mill Creek, the Cottonwoods) -- over an optional
faint street grid, and writes both an SVG and a PNG.

Usage:
    python3 slc_waterways_map.py --outdir out

The default Overpass endpoint is often unreachable from sandboxed networks. Set
a mirror with --overpass-url or the OVERPASS_URL environment variable.
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

# Waterway classes drawn, widest first. Each entry is (OSM value, label, width,
# colour) -- rivers read as the spine of the valley, ditches as capillaries.
WATERWAY_STYLES = [
    ("river", "River", 3.4, "#2b7fc4"),
    ("canal", "Canal", 2.0, "#3f9ad1"),
    ("stream", "Stream", 1.2, "#5bb3e0"),
    ("drain", "Drain", 0.7, "#7ac4e8"),
    ("ditch", "Ditch", 0.5, "#9bd4ef"),
]

WATER_BODY_TAGS = {"natural": ["water"], "landuse": ["reservoir"], "waterway": ["riverbank"]}

THEMES = {
    "dark": {
        "bg": "#0d1b2a",
        "street": "#1e3147",
        "water_fill": "#1b5a86",
        "water_edge": "#2b7fc4",
        "boundary": "#4a6b8a",
        "text": "#d8e6f2",
        "subtext": "#8aa6bf",
    },
    "light": {
        "bg": "#f4f1ea",
        "street": "#ddd8cc",
        "water_fill": "#9ecfe8",
        "water_edge": "#2b7fc4",
        "boundary": "#b5ac99",
        "text": "#1d2b36",
        "subtext": "#5d6b76",
    },
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--outdir", type=Path, default=Path("out"), help="directory for the SVG and PNG (default: out)")
    p.add_argument("--basename", default="slc_waterways", help="output filename stem (default: slc_waterways)")
    p.add_argument("--place", default="Salt Lake City, Utah, USA", help="place to geocode for the map extent")
    p.add_argument("--theme", choices=sorted(THEMES), default="dark", help="colour theme (default: dark)")
    p.add_argument("--dpi", type=int, default=300, help="PNG resolution (default: 300)")
    p.add_argument("--width", type=float, default=16.0, help="figure width in inches (default: 16)")
    p.add_argument("--no-streets", action="store_true", help="skip the faint street underlay")
    p.add_argument("--no-legend", action="store_true", help="skip the legend")
    p.add_argument("--title", default="Salt Lake City", help="map title")
    p.add_argument("--subtitle", default="Rivers, creeks and canals of the Salt Lake valley", help="map subtitle")
    p.add_argument(
        "--overpass-url",
        default=os.environ.get("OVERPASS_URL"),
        help="Overpass API base URL, e.g. https://overpass-api.de/api (env: OVERPASS_URL)",
    )
    p.add_argument("--timeout", type=int, default=300, help="per-request timeout in seconds (default: 300)")
    return p.parse_args(argv)


def configure_osmnx(args: argparse.Namespace) -> None:
    if args.overpass_url:
        ox.settings.overpass_url = args.overpass_url.rstrip("/")
    ox.settings.requests_timeout = args.timeout
    ox.settings.overpass_settings = f"[out:json][timeout:{args.timeout}]"
    ox.settings.use_cache = True
    ox.settings.log_console = False


def fetch(label: str, fn, *fn_args, **fn_kwargs) -> gpd.GeoDataFrame | None:
    """Run an OSM query, reporting what came back instead of dying on an empty result."""
    print(f"  fetching {label} ... ", end="", flush=True)
    try:
        gdf = fn(*fn_args, **fn_kwargs)
    except Exception as exc:  # noqa: BLE001 - any upstream failure is non-fatal
        print(f"failed ({type(exc).__name__}: {exc})")
        return None
    if gdf is None or gdf.empty:
        print("nothing found")
        return None
    print(f"{len(gdf)} features")
    return gdf


def lines_only(gdf: gpd.GeoDataFrame | None) -> gpd.GeoDataFrame | None:
    if gdf is None:
        return None
    out = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString"])]
    return out if not out.empty else None


def areas_only(gdf: gpd.GeoDataFrame | None) -> gpd.GeoDataFrame | None:
    if gdf is None:
        return None
    out = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])]
    return out if not out.empty else None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_osmnx(args)

    print(f"Overpass endpoint: {ox.settings.overpass_url}")
    print(f"Geocoding {args.place!r} ...")
    try:
        boundary = ox.geocode_to_gdf(args.place)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not geocode {args.place!r}: {exc}", file=sys.stderr)
        return 1
    polygon = boundary.geometry.iloc[0]
    print(f"  boundary: {polygon.geom_type}, bounds {tuple(round(v, 4) for v in polygon.bounds)}")

    print("Querying OpenStreetMap ...")
    waterways = lines_only(
        fetch(
            "waterways",
            ox.features_from_polygon,
            polygon,
            tags={"waterway": [v for v, *_ in WATERWAY_STYLES]},
        )
    )
    water_bodies = areas_only(fetch("water bodies", ox.features_from_polygon, polygon, tags=WATER_BODY_TAGS))

    streets = None
    if not args.no_streets:
        streets = fetch(
            "streets",
            lambda poly: ox.graph_to_gdfs(
                ox.graph_from_polygon(poly, network_type="drive", retain_all=True), nodes=False
            ),
            polygon,
        )

    if waterways is None and water_bodies is None:
        print(
            "error: no water features returned -- the Overpass endpoint may be blocked or "
            "region-limited. Try another mirror with --overpass-url.",
            file=sys.stderr,
        )
        return 1

    theme = THEMES[args.theme]

    # A degree of longitude is cos(latitude) as wide as a degree of latitude, so
    # plotting raw lat/lon on equal axes stretches the map east-west. Scaling the
    # y-axis by 1/cos(lat) restores the true proportions, and the figure is then
    # sized to match -- otherwise a wide city like Salt Lake sits in a square
    # canvas with empty bands above and below it.
    west, south, east, north = polygon.bounds
    aspect = 1.0 / math.cos(math.radians((south + north) / 2.0))
    map_ratio = ((north - south) * aspect) / (east - west)
    fig_height = args.width * map_ratio + 2.2  # headroom for title and caption

    print(f"Rendering ({args.theme} theme) ...")
    fig, ax = plt.subplots(figsize=(args.width, fig_height), facecolor=theme["bg"])
    ax.set_facecolor(theme["bg"])

    gpd.GeoSeries([polygon], crs=boundary.crs).boundary.plot(
        ax=ax, color=theme["boundary"], linewidth=0.8, linestyle=(0, (6, 4)), zorder=1
    )

    if streets is not None:
        streets.plot(ax=ax, color=theme["street"], linewidth=0.28, alpha=0.9, zorder=2)

    if water_bodies is not None:
        water_bodies.plot(
            ax=ax, facecolor=theme["water_fill"], edgecolor=theme["water_edge"], linewidth=0.4, zorder=3
        )

    drawn: list[tuple[str, float, str]] = []
    if waterways is not None:
        values = waterways["waterway"] if "waterway" in waterways.columns else None
        for value, label, width, color in WATERWAY_STYLES:
            subset = waterways if values is None else waterways[values == value]
            if subset.empty:
                continue
            subset.plot(ax=ax, color=color, linewidth=width, alpha=0.95, zorder=4, capstyle="round")
            drawn.append((label, width, color))
            if values is None:
                break

    pad_x = (east - west) * 0.02
    pad_y = (north - south) * 0.02
    ax.set_xlim(west - pad_x, east + pad_x)
    ax.set_ylim(south - pad_y, north + pad_y)
    ax.set_aspect(aspect)
    ax.set_axis_off()

    line = 0.34 / fig_height  # one text line as a fraction of figure height
    if args.title:
        fig.text(
            0.5, 1 - line, args.title, ha="center", va="top",
            color=theme["text"], fontsize=28, fontweight="bold",
        )
    if args.subtitle:
        fig.text(
            0.5, 1 - 2.35 * line, args.subtitle, ha="center", va="top",
            color=theme["subtext"], fontsize=12,
        )
    fig.text(
        0.5, 0.6 * line, "Data: OpenStreetMap contributors (ODbL)",
        ha="center", va="bottom", color=theme["subtext"], fontsize=9,
    )

    if drawn and not args.no_legend:
        handles = [Line2D([0], [0], color=c, lw=max(w, 1.4), label=lbl) for lbl, w, c in drawn]
        legend = fig.legend(
            handles=handles,
            loc="lower center",
            bbox_to_anchor=(0.5, 1.5 * line),
            ncol=len(handles),
            frameon=False,
            fontsize=10,
            labelcolor=theme["text"],
            handlelength=2.2,
            columnspacing=2.4,
        )
        legend.set_zorder(5)

    fig.subplots_adjust(left=0.03, right=0.97, top=1 - 3.1 * line, bottom=2.9 * line)

    args.outdir.mkdir(parents=True, exist_ok=True)
    svg_path = args.outdir / f"{args.basename}.svg"
    png_path = args.outdir / f"{args.basename}.png"
    fig.savefig(svg_path, format="svg", facecolor=theme["bg"], bbox_inches="tight", pad_inches=0.25)
    fig.savefig(png_path, format="png", dpi=args.dpi, facecolor=theme["bg"], bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)

    for path in (svg_path, png_path):
        print(f"wrote {path} ({path.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
