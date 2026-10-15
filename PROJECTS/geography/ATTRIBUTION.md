# Geography data attribution and license notice

## Data sources

- **Natural Earth 1:10m land and minor-island polygons:** public-domain cartographic data. Source pages: https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-land/ and https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-minor-islands/
- **Seven-continent partition polygons:** GBIF `continents` project, fixed at commit `5f2aaf608f2f828bb1d03ae0d2ef3f41feacd5be`. The project states that its terrestrial boundaries follow OpenStreetMap-derived lines/polygons and that the dataset is licensed as an ODbL derivative. Source: https://github.com/gbif/continents

## Attribution

> Continent partition: GBIF `continents`, derived from OpenStreetMap contributors; ODbL 1.0. Natural Earth land and minor-island polygons are public domain.

## License treatment for generated data

The generated `continent_land_polygons.geojson`, `continent_land_area.csv`, and `antarctica_area_scenarios.csv` are derived from intersections with the GBIF/OpenStreetMap-derived continent partition. To respect the stated share-alike basis of the partition source, these derived geographic database outputs in the audit artifact are made available under the **Open Data Commons Open Database License (ODbL) 1.0**, subject to the license terms. The country-classification baseline sourced only from Natural Earth remains separately documented as preliminary and public-domain-source-derived.

- ODbL 1.0 text: https://opendatacommons.org/licenses/odbl/1-0/
- GBIF source and license statement: https://github.com/gbif/continents#license

The PNG map is a rendered work, not the raw polygon database; it carries the source attribution in its footer. Natural Earth source data remains public domain. This notice documents the project's intended attribution and licensing treatment; it is not legal advice.
