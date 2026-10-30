# City coordinate provenance

`city_coordinates.csv` contains reference place coordinates for city-level AQI plotting. Coordinates do **not** identify air-quality monitoring stations.

## Source

- GeoNames India country extract: <https://download.geonames.org/export/dump/IN.zip>
- GeoNames administrative division lookup: <https://download.geonames.org/export/dump/admin1CodesASCII.txt>
- GeoNames attribution and data information: <https://www.geonames.org/about.html>
- License: Creative Commons Attribution 4.0 (CC BY 4.0)
- Retrieved: 2026-10-30

The downloaded source files are retained as `IN_geonames.zip` and `geonames_admin1CodesASCII.txt`. The extract README is included inside the ZIP.

## Matching method

Each `city_day.csv` city was matched to a GeoNames populated place (`FeatureClass=P`, populated-place feature code), and the candidate's GeoNames administrative division was checked against the city/state pair in `stations.csv`. For candidates in the same state, the administrative seat feature (`PPLA`/`PPLA2`/etc.) is preferred, then larger reported population, then the GeoNames identifier for a stable tie break. `Brajrajnagar` in the air-quality file is matched to GeoNames' ASCII spelling `Brajarajnagar`; the original AQI city label remains unchanged in the output file.

The CSV preserves the original city label, GeoNames feature name and identifier, feature code, state, coordinates, population field, source URL, license, and retrieval date so matches can be reviewed. Coordinates are reference points for city aggregation. They must not be interpreted as station placement or exact exposure locations. GeoNames describes its data as provided without a warranty of accuracy or completeness.
