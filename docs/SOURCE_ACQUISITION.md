# GeoHealth source acquisition

Use **source-published observations** with documented geography, units and strata. A CSV download button does not guarantee a stable public CSV URL.

## NSW HealthStats: first forecast target
Mental-health-related emergency department visits, monthly (LHD comparison):
https://www.healthstats.nsw.gov.au/indicator?name=-men-sui-mth-ed&location=LHD

Open the source dashboard, choose the *number* of presentations, intended LHD comparison, persons, all ages, total mental-health presentation category, then **Download data as CSV**. Preserve the original download. Inspect column names with `python -m etl.build --inspect ...`. Do not assume the export has YYYY-MM dates or numeric columns until checked.

## Official LHD boundaries
ArcGIS official layer:
https://portal.data.nsw.gov.au/arcgis/rest/services/Hosted/SAPHARI_Version_LHD_Areas_2/FeatureServer/0

GeoHealth `python -m etl.download --boundaries` requests real GeoJSON at EPSG:4326 with `lhd_name` and `lhd_code`. It preserves retrieval URL, date and file SHA-256.

## Other sources for subsequent milestones

Bureau of Health Information downloadable quarterly activity:
https://www.bhi.nsw.gov.au/downloadable-data

ABS regional population:
https://www.abs.gov.au/statistics/people/population/regional-population/latest-release

ABS SEIFA:
https://www.abs.gov.au/statistics/people/people-and-communities/socio-economic-indexes-areas-seifa-australia/latest-release

AIHW AOD treatment services by PHN:
https://www.aihw.gov.au/reports/alcohol-other-drug-treatment-services/alcohol-other-drug-treatment-services-australia/contents/data-primary-health-network

Government PHN concordances:
https://www.health.gov.au/resources/collections/primary-health-networks-phns-collection-of-concordance-files

## Rules
- Verify source geography, frequency and observed vs modelled status before loading.
- Count of *presentations* does not equal count of persons or prevalence.
- Funding at statewide level is **not** an observed LHD allocation.
- Suppressed small cells and missing values are **not zero**.
- Verify copyright, licence and commercial redistribution rights before selling or embedding data.
