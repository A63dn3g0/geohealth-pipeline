# AOD hospitalisations — source integration and limitations

Source file: `Alcohol and other drug hospitalisations_LHD.csv` (unmodified; supplied October 2026).
Citation: https://www.healthstats.nsw.gov.au/r/137803

## Verified file structure

- **368 observed records**, 16 published geography labels (15 individual NSW LHDs and `All LHDs`), 23 annual financial-year periods **2001–02 to 2023–24**.
- Rates are **age-standardised hospitalisation rates per 100,000 population** (standard reference: Australian population 30 June 2001), with published lower/upper 95% CIs.
- Drug category is `Total alcohol and other drug-related` throughout.
- Numerator: hospitalisation episodes, with principal **or additional** relevant ICD-10-AM diagnoses. **Not** treatment episodes, unique people, ED visits, prevalence, or incidence.
- LHD geography refers to **residence** rather than hospital location.
- Contains Far West and Western NSW observations that are *not* present in the mental-health ED source. Geography/missingness is **indicator-specific**.
- Counts, crude rates, age-standardised rates, and different time intervals must not be added together or compared as if they are the same measure.
- Source CSV has 34 single-field metadata/footer rows; the adapter parses the 368 six-column source records only.
- Source SHA-256: `6581d824a8565d7493f055227ed01233e5897822878a331d5321a5f7699cb7ea`.

## Running

Save the original file unchanged to `data/raw/Alcohol and other drug hospitalisations_LHD.csv`, alongside the original mental-health source, then:

```bash
python -m etl.build
streamlit run app.py
```

Both indicators appear in the indicator selector at their actual frequency and rate methodology. AOD results are **historical annual financial-year rates**; the quarterly forecasting model is **not used for AOD**. A separate backtested annual model is needed before enabling AOD projections, especially given coding/policy and intervention-regime changes.

## Licensing

HealthStats NSW publishes limitations on commercial use/resale. Local development is not a commercial redistribution licence. See `docs/DATA_LICENSING.md`.
