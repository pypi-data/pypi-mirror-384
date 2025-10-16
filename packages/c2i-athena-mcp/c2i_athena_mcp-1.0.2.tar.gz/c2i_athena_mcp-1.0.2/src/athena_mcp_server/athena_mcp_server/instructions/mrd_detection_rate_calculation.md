# MRD Detection Rate Calculation Instructions

## Overview
Calculate Minimal Residual Disease (MRD) detection rates using filtering followed by sample-specific anomaly detection.

**Important:** The MRD detection rate calculation uses the pre-existing view `mrd_site_based_features`.
You do not need to create this view; simply use it as the source for the detection rate calculation query.

The `mrd_site_based_features` view contains:
- For each sample, a full histogram of all genomic positions (chrom, pos, ref, alt)
- Exclusion indicators: `bad_map_ind`, `gnomad_ac3_ind`, `phase_exc_ind`, `pass_ffpe_filter`, `in_normal`, and others
- Key quantitative fields: `refcount`, `nrefcount`, `cov`, and more

Each sample's histogram is represented as a set of rows in the view, with all relevant site-level features and filtering indicators for MRD calculation. See the Example Query section for its full definition and usage.

## Core Formula
```
detection_rate = sites_with_alt / (sites_with_alt + total_ref_sites)
where sites_with_alt = SUM(LEAST(nrefcount, 1))
```

## Data Requirements
- **Primary table**: `main.histograms_snv`
- **Dataset mapping**: `main.dataset_record` (links subjects to VCF file IDs and normal samples)
- **Required partitions**: Specify `dataset`, `run_name`, `algo_version` for each query
-- **View usage**: The `main.mrd_site_based_features` view is already available and should be used as the source for detection rate calculation queries.

## Two-Stage Filtering Process

### Stage 1: Static Quality Filters
Apply these filters first to identify high-quality genomic sites:

1. **FFPE Quality Filter** (`pass_ffpe_filter = 1`)
   - MQ = 60 AND MPOS > 20 from VCF files
   - Uses `strelka` and `mutect_strelka_intersect` tables via `dataset_record.file_id` mapping

2. **Mappability Filter** (`bad_map_ind = 0`)
   - Exclude sites in `external.bad_mappability_all_pos`

3. **Population Frequency Filter** (`gnomad_ac3_ind = 0`)
   - Exclude common variants from `external.gnomad_exclusion_sites`

4. **Phase Exclusion Filter** (`phase_exc_ind = 0`)
   - Exclude problematic regions from `external.phase_exclusion_list`

5. **Normal Sample Filter** (`in_normal = 0`)
   - Exclude sites present in subject's normal sample (identified via `dataset_record.normal`)
   - Only exclude if `alt_tot_count > 0` in normal sample

### Stage 2: Sample-Specific Anomaly Filters
Apply to sites that pass Stage 1 filters:

1. **Global Anomalous Sites** (`is_global_anomalous = 0`)
   - Calculate per-sample: `total_count = refcount + nrefcount`
   - Find sample median total count and MAD (Median Absolute Deviation)
   - Flag if `ABS(total_count - median_total) > 4 * MAD_total`

2. **Unmatched Sites** (`is_unmatched = 0`)
   - Calculate per-sample: `VAF = nrefcount / (nrefcount + refcount)`
   - If sample `median_vaf = 0`: flag if `VAF >= 0.1 OR nrefcount > 1`
   - If sample `median_vaf > 0`: no sites flagged as unmatched

## Count Calculations
- **refcount**: Use `COALESCE(base_ovlp_only, base)` where base matches `ref` allele
- **nrefcount**: Use `COALESCE(base_ovlp_only, base)` where base matches `alt` allele, or `alt_tot_count` for complex variants

## # MRD detection rate - Query Structure Template

The workflow requires you to use the `mrd_site_based_features` view as the input for the detection rate calculation query. The recommended query structure is:

```sql
WITH mrd_site_based_features_filltered AS (
    SELECT
        mf.dataset,
        mf.algo_version,
        mf.run_name, 
        mf.subject,
        mf.sample,
        mf.chrom,
        mf.pos,
        mf.ref,
        mf.alt,
        mf.refcount,
        mf.nrefcount,
        mf.cov
    FROM main.mrd_site_based_features mf 
    WHERE dataset = '<DATASET_NAME>'
        AND mf.pass_ffpe_filter = 1  
        AND mf.bad_map_ind = 0
        --AND mf.gnomad_ac3_ind = 0
        AND mf.phase_exc_ind = 0
        AND mf.in_normal = 0
), 
with_total AS (
    SELECT *, 
        (refcount + nrefcount) AS total_count, 
        CAST(nrefcount AS DOUBLE) / NULLIF((nrefcount + refcount), 0) AS vaf
    FROM mrd_site_based_features_filltered
    WHERE (refcount + nrefcount) > 0
        AND cov > 0
),
median_stats AS (
    SELECT dataset, algo_version, subject, sample,
        (CASE 
            WHEN COUNT(*) % 2 = 1 THEN 
                element_at(array_sort(array_agg(total_count)), (COUNT(*) + 1) / 2)
            ELSE 
                (element_at(array_sort(array_agg(total_count)), COUNT(*) / 2) + 
                 element_at(array_sort(array_agg(total_count)), COUNT(*) / 2 + 1)) / 2.0
        END) AS median_total,
        (CASE 
            WHEN COUNT(*) % 2 = 1 THEN 
                element_at(array_sort(array_agg(vaf)), (COUNT(*) + 1) / 2)
            ELSE 
                (element_at(array_sort(array_agg(vaf)), COUNT(*) / 2) + 
                 element_at(array_sort(array_agg(vaf)), COUNT(*) / 2 + 1)) / 2.0
        END) AS median_vaf
    FROM with_total
    GROUP BY dataset, algo_version, subject, sample
),
with_median AS (
    SELECT w.*, m.median_total, m.median_vaf
    FROM with_total w
    JOIN median_stats m ON w.sample = m.sample AND w.algo_version = m.algo_version
),
mad_stats AS (
    SELECT dataset, algo_version, subject, sample,
        (CASE 
            WHEN COUNT(*) % 2 = 1 THEN 
                element_at(array_sort(array_agg(ABS(total_count - median_total))), (COUNT(*) + 1) / 2)
            ELSE 
                (element_at(array_sort(array_agg(ABS(total_count - median_total))), COUNT(*) / 2) + 
                 element_at(array_sort(array_agg(ABS(total_count - median_total))), COUNT(*) / 2 + 1)) / 2.0
        END) AS mad_total
    FROM with_median
    GROUP BY dataset, algo_version, subject, sample
),
with_anomalies AS (
    SELECT w.*, mad.mad_total,
        CASE WHEN ABS(w.total_count - w.median_total) > 4 * mad.mad_total THEN 1 
            ELSE 0 END AS is_global_anomalous,
        CASE 
            WHEN w.median_vaf = 0 AND (w.vaf >= 0.1 and w.nrefcount > 1) THEN 1
            ELSE 0
        END AS is_unmatched
    FROM with_median w
    JOIN mad_stats mad ON w.sample = mad.sample 
        AND w.algo_version = mad.algo_version 
        AND w.dataset = mad.dataset 
        AND w.subject = mad.subject
),
detection_rates AS (
    SELECT 
        dataset,
        run_name,
        algo_version,
        subject,
        sample,
        SUM(LEAST(nrefcount, 1)) AS sites_with_alt,
        SUM(LEAST(nrefcount, 1)) + SUM(refcount) AS total_sites,
        CASE 
            WHEN SUM(LEAST(nrefcount, 1)) + SUM(refcount) = 0 THEN 0
            ELSE CAST(SUM(LEAST(nrefcount, 1)) AS DOUBLE) / (SUM(LEAST(nrefcount, 1)) + SUM(refcount))
        END AS detection_rate
    FROM with_anomalies
    WHERE is_global_anomalous = 0
        AND is_unmatched = 0
    GROUP BY dataset, run_name, algo_version, subject, sample
)
SELECT 
    dataset,
    run_name,
    algo_version,
    subject,
    sample,
    sites_with_alt,
    total_sites,
    FORMAT('%.8f', detection_rate) AS detection_rate
FROM detection_rates
ORDER BY dataset, run_name, algo_version, subject, sample;
```

## Output Requirements
Always include these columns for traceability:
- `dataset`
- `run_name` 
- `algo_version`
- `subject`
- `sample`
- `sites_with_alt`
- `total_sites`
- `detection_rate`

## Key Implementation Notes
1. **Static filters must be applied first** - anomaly detection statistics are calculated only on pre-filtered sites
2. **Sample-specific calculations** - median/MAD computed per sample, not globally, calculated only on pre-filtered sites
3. **File ID mapping** - Use `dataset_record` table to map subjects to VCF file IDs for quality data joins
4. **Normal sample identification** - Use `dataset_record.normal` field, not naming patterns
5. **Overlap-only preference** - Use `*_ovlp_only` columns when available, fall back to base columns

## Critical Filter Order
1. Apply all static filters except for gnomad_ac3_ind and centromere_ind 
2. Calculate sample statistics on filtered population
3. Apply anomaly filters 
4. Calculate detection rates on final filtered sites

This ensures consistent, reproducible MRD detection rate calculations across all datasets and samples.

## Example Query
## VIEW "main"."mrd_site_based_features" :
```sql
SELECT
  h.dataset
, h.run_name
, h.algo_version
, h.subject
, h.sample
, h.rp_file_id
, h.chrom
, h.pos
, h.ref
, h.alt
, h.sample_type
, (CASE WHEN (h.ref = 'A') THEN COALESCE(h.a_ovlp_only, h.a, 0) WHEN (h.ref = 'T') THEN COALESCE(h.t_ovlp_only, h.t, 0) WHEN (h.ref = 'G') THEN COALESCE(h.g_ovlp_only, h.g, 0) WHEN (h.ref = 'C') THEN COALESCE(h.c_ovlp_only, h.c, 0) ELSE 0 END) refcount
, (CASE WHEN (h.alt = 'A') THEN COALESCE(h.a_ovlp_only, h.a, 0) WHEN (h.alt = 'T') THEN COALESCE(h.t_ovlp_only, h.t, 0) WHEN (h.alt = 'G') THEN COALESCE(h.g_ovlp_only, h.g, 0) WHEN (h.alt = 'C') THEN COALESCE(h.c_ovlp_only, h.c, 0) ELSE 0 END) nrefcount
, h.alt_tot_count
, h.cov
, h.tcov
, h.a
, h.t
, h.g
, h.c
, h.n
, h.indel
, h.a_ovlp_only
, h.t_ovlp_only
, h.g_ovlp_only
, h.c_ovlp_only
, h.n_ovlp_only
, h.indel_ovlp_only
, h.cov_ovlp_only
, h.ta
, h.tc
, h.tg
, h.tt
, h.tn
, h.tindel
, h.inversions
, h.translocs
, h.chmrs
, (CASE WHEN ((TRY_CAST(s.info_mq AS DOUBLE) = 6E1) AND (TRY_CAST(mi.info_mpos AS INTEGER) > 20)) THEN 1 ELSE 0 END) pass_ffpe_filter
, (CASE WHEN (mp.chrom IS NOT NULL) THEN 1 ELSE 0 END) bad_map_ind
, (CASE WHEN (gn.pos IS NOT NULL) THEN 1 ELSE 0 END) gnomad_ac3_ind
, (CASE WHEN (pel.chrom IS NOT NULL) THEN 1 ELSE 0 END) phase_exc_ind
, (CASE WHEN ((cr.chr IS NOT NULL) AND (h.pos BETWEEN cr."start" AND cr."end")) THEN 1 ELSE 0 END) centromere_ind
, (CASE WHEN ((CASE WHEN (h_nor.alt = 'A') THEN h_nor.a WHEN (h_nor.alt = 'T') THEN h_nor.t WHEN (h_nor.alt = 'G') THEN h_nor.g WHEN (h_nor.alt = 'C') THEN h_nor.c ELSE h_nor.alt_tot_count END) > 0) THEN 1 ELSE 0 END) in_normal
FROM
  ((((((((main.histograms_snv h
INNER JOIN main.dataset_record dr ON ((dr.dataset = h.dataset) AND (dr.subject = h.subject)))
LEFT JOIN external.bad_mappability_positions mp ON ((mp.chrom = h.chrom) AND (mp.pos = h.pos)))
LEFT JOIN external.gnomad_exclusion_sites gn ON ((gn.chrom = h.chrom) AND (gn.pos = h.pos) AND (gn.alt = h.alt)))
LEFT JOIN external.phase_exclusion_list pel ON ((pel.chrom = h.chrom) AND (pel.pos = h.pos)))
LEFT JOIN external.centromere_regions cr ON (cr.chr = h.chrom))
LEFT JOIN main.histograms_snv h_nor ON ((h_nor.dataset = h.dataset) AND (h_nor.subject = h.subject) AND (h_nor.sample = dr.normal) AND (h_nor.chrom = h.chrom) AND (h_nor.pos = h.pos) AND (h_nor.ref = h.ref) AND (h_nor.alt = h.alt) AND (h_nor.run_name = h.run_name) AND (h_nor.algo_version = h.algo_version)))
LEFT JOIN main.mutect_strelka_intersect mi ON ((mi.file_id = dr.snv_vcf_file_id) AND (mi.chrom = h.chrom) AND (CAST(mi.pos AS INTEGER) = h.pos) AND (mi.ref = h.ref) AND (mi.alt = h.alt)))
LEFT JOIN main.strelka s ON ((s.file_id = dr.strelka_vcf_file_id) AND (s.chrom = h.chrom) AND (CAST(s.pos AS INTEGER) = h.pos) AND (s.ref = h.ref) AND (s.alt = h.alt)))
ORDER BY h.dataset ASC, h.run_name ASC, h.algo_version ASC, h.subject ASC, h.sample ASC, h.chrom ASC, h.pos ASC
```

