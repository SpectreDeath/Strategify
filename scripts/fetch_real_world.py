"""Script to fetch and process real-world GeoJSON data."""

from pathlib import Path

import geopandas as gpd


def fetch_and_save_regions(output_path: Path) -> None:
    """Fetch Natural Earth data from URL and save a subset of regions."""
    url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    print(f"Downloading from {url}...")
    world = gpd.read_file(url)

    # Let's pick 4 neighboring countries in Eastern Europe/Asia to map to our 4 regions
    target_countries = ["Ukraine", "Russia", "Belarus", "Poland"]
    # Alpha -> Ukraine
    # Bravo -> Russia
    # Charlie -> Belarus
    # Delta -> Poland

    subset = world[world["ADMIN"].isin(target_countries)].copy()

    # Rename 'ADMIN' to 'region_id' so it matches our existing logic
    # We will map them to our internal IDs for continuity, or just use the country names
    mapping = {
        "Ukraine": "alpha",
        "Russia": "bravo",
        "Belarus": "charlie",
        "Poland": "delta",
    }
    subset["region_id"] = subset["ADMIN"].map(mapping)

    # Drop unnecessary columns
    subset = subset[["region_id", "geometry"]]

    # Save to file
    subset.to_file(output_path, driver="GeoJSON")
    print(f"Saved real-world GeoJSON to {output_path}")


if __name__ == "__main__":
    out_file = Path(__file__).parent.parent / "strategify" / "geo" / "real_world.geojson"
    fetch_and_save_regions(out_file)
