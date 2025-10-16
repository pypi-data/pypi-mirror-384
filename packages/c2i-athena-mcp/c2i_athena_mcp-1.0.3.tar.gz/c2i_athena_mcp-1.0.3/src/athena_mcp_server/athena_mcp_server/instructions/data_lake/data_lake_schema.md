# AWS Athena Data Lake Schema Reference

## Overview
Complete AWS Athena schema documentation for the genomics data lake analytics layer.

**IMPORTANT**: This documentation focuses on `main` (processed) and `external` (reference) databases only. 
**Ignore `raw_main` database** - it contains raw/unprocessed data and should not be used for analytics.

**Primary Databases**: `main` (processed genomic data), `external` (reference data), `sandbox` (development)  
**Purpose**: High-performance genomic data queries and analytics using processed, curated datasets

**Related Documents:**
- **PostgreSQL Schema:** `data_layer_schema.md` - Complete PostgreSQL metadata schemas
- **Query Guide:** `data_platform_query_guide.md` - Query strategies and examples
---

## Database Structure

### Available Databases (Analytics Focus)
1. **`main`** - Primary processed genomic data for analytics
2. **`external`** - External reference datasets and annotations
3. **`sandbox`** - Development and testing environment
4. **`default`** - Default Athena database
5. ~~`raw_main`~~ - **EXCLUDED** - Raw/unprocessed data (do not use)
6. ~~`curated_main`~~ - Currently empty
7. ~~`integration`~~ - Currently empty
---

## Database: `main` (Primary Processed Analytics)

### Tables Overview
- **`histograms_snv`** - Single nucleotide variant histogram data
- **`histograms_het`** - Heterozygous variant histogram data
- **`dataset_record`** - Subject to VCF file mapping
- **`mrd_site_based_features`** - Pre-computed MRD features (VIEW)
- **`mutect`** - Mutect variant calls
- **`strelka`** - Strelka variant calls
- **`mutect_strelka_intersect`** - Intersection of variant calls
- **`normal_het_germline`** - Germline heterozygous variants
- **`strelka_annotated`** - Annotated Strelka variant calls

### Table: `histograms_snv` (SNV Histogram Data)

**Purpose:** Single nucleotide variant histogram data with comprehensive base counts and coverage.

**Complete Schema:**
```sql
histograms_snv (
    chrom string,                    -- Chromosome identifier
    pos bigint,                      -- Genomic position
    a bigint,                        -- Count of A bases
    t bigint,                        -- Count of T bases
    g bigint,                        -- Count of G bases
    c bigint,                        -- Count of C bases
    n bigint,                        -- Count of N (unknown) bases
    indel bigint,                    -- Count of insertions/deletions
    cov bigint,                      -- Total coverage
    tcov bigint,                     -- Total coverage (alternative)
    sample string,                   -- Sample identifier
    sample_type string,              -- Type of sample (tumor/normal)
    ref string,                      -- Reference allele
    alt string,                      -- Alternative allele
    alt_tot_count bigint,            -- Total alternative allele count
    a_ovlp_only bigint,              -- A count (overlap only)
    t_ovlp_only bigint,              -- T count (overlap only)
    g_ovlp_only bigint,              -- G count (overlap only)
    c_ovlp_only bigint,              -- C count (overlap only)
    n_ovlp_only bigint,              -- N count (overlap only)
    indel_ovlp_only bigint,          -- Indel count (overlap only)
    cov_ovlp_only bigint,            -- Coverage (overlap only)
    ta bigint,                       -- Tumor A count
    tc bigint,                       -- Tumor C count
    tg bigint,                       -- Tumor G count
    tt bigint,                       -- Tumor T count
    tn bigint,                       -- Tumor N count
    tindel bigint,                   -- Tumor indel count
    inversions bigint,               -- Inversion count
    translocs bigint,                -- Translocation count
    chmrs bigint                     -- Chromothripsis count
)
PARTITIONED BY (
    dataset string,                  -- Dataset identifier
    run_name string,                 -- Run name
    algo_version string,             -- Algorithm version
    subject string,                  -- Subject identifier
    rp_file_id string                -- RP file identifier
)
```

**Key Columns for Analysis:**
- `chrom`, `pos`: Genomic coordinates
- `ref`, `alt`: Variant information
- `cov`, `alt_tot_count`: Coverage and variant evidence
- `a`, `t`, `g`, `c`: Individual nucleotide counts at position
- `sample`, `sample_type`: Sample identification

### Table: `histograms_het` (Heterozygous Variant Data)

**Purpose:** Heterozygous variant histogram data.

**Complete Schema:**
```sql
histograms_het (
    chrom string,                    -- Chromosome identifier
    pos bigint,                      -- Genomic position
    ref string,                      -- Reference allele
    alt string,                      -- Alternative allele
    a bigint,                        -- Count of A bases
    t bigint,                        -- Count of T bases
    g bigint,                        -- Count of G bases
    c bigint,                        -- Count of C bases
    n bigint,                        -- Count of N bases
    indel bigint,                    -- Count of indels
    cov bigint,                      -- Total coverage
    tcov bigint,                     -- Total coverage (alternative)
    sample string,                   -- Sample identifier
    sample_type string,              -- Sample type
    alt_tot_count bigint,            -- Total alt count
    inversions bigint,               -- Inversion count
    translocs bigint,                -- Translocation count
    chmrs bigint                     -- Chromothripsis count
)
PARTITIONED BY (
    dataset string,                  -- Dataset identifier
    run_name string,                 -- Run name
    algo_version string,             -- Algorithm version
    subject string,                  -- Subject identifier
    rp_file_id string                -- RP file identifier
)
```

### Table: `dataset_record` (VCF File Mapping)

**Purpose:** Maps subjects to VCF files and metadata.

**Complete Schema:**
```sql
dataset_record (
    id bigint,                       -- Unique identifier
    dl_run_id bigint,                -- Data lake run ID
    normal string,                   -- Normal sample identifier
    tumor string,                    -- Tumor sample identifier
    snv_vcf_dataset string,          -- SNV VCF dataset
    snv_vcf_subject string,          -- SNV VCF subject
    snv_vcf_file_uri string,         -- SNV VCF file URI
    snv_vcf_file_id string,          -- SNV VCF file identifier
    het_vcf_dataset string,          -- Het VCF dataset
    het_vcf_subject string,          -- Het VCF subject
    het_vcf_file_uri string,         -- Het VCF file URI
    het_vcf_file_id string,          -- Het VCF file identifier
    file_id string,                  -- General file identifier
    strelka_vcf_file_uri string,     -- Strelka VCF file URI
    strelka_vcf_file_id string,      -- Strelka VCF file identifier
    strelka_ann_vcf_file_uri string, -- Strelka annotated VCF URI
    strelka_ann_vcf_file_id string,  -- Strelka annotated VCF ID
    mutect_vcf_file_uri string,      -- Mutect VCF file URI
    mutect_vcf_file_id string,       -- Mutect VCF file identifier
    region string,                   -- Genomic region
    dl_update_timestamp_utc timestamp, -- Data lake update timestamp
    dl_insert_timestamp_utc timestamp  -- Data lake insert timestamp
)
PARTITIONED BY (
    dataset string,                  -- Dataset identifier
    subject string                   -- Subject identifier
)
```

### Table: `mrd_site_based_features` (MRD Features VIEW)

**Purpose:** Pre-computed MRD features with all filtering indicators. **This is a view, not a table.**

**Complete Schema:**
```sql
mrd_site_based_features (
    dataset string,                  -- Dataset identifier
    run_name string,                 -- Run name
    algo_version string,             -- Algorithm version
    subject string,                  -- Subject identifier
    sample string,                   -- Sample identifier
    rp_file_id string,               -- RP file identifier
    chrom string,                    -- Chromosome identifier
    pos bigint,                      -- Genomic position
    ref string,                      -- Reference allele
    alt string,                      -- Alternative allele
    sample_type string,              -- Sample type
    refcount bigint,                 -- Reference allele count
    nrefcount bigint,                -- Non-reference allele count
    alt_tot_count bigint,            -- Total alternative count
    cov bigint,                      -- Coverage
    tcov bigint,                     -- Total coverage
    -- Base counts (same as histograms_snv)
    a bigint, t bigint, g bigint, c bigint, n bigint, indel bigint,
    a_ovlp_only bigint, t_ovlp_only bigint, g_ovlp_only bigint, 
    c_ovlp_only bigint, n_ovlp_only bigint, indel_ovlp_only bigint,
    cov_ovlp_only bigint,
    ta bigint, tc bigint, tg bigint, tt bigint, tn bigint, tindel bigint,
    inversions bigint, translocs bigint, chmrs bigint,
    -- Filter indicators
    pass_ffpe_filter int,            -- FFPE quality filter (1=pass, 0=fail)
    bad_map_ind int,                 -- Bad mappability indicator (1=bad, 0=good)
    gnomad_ac3_ind int,              -- gnomAD AC≥3 indicator (1=exclude, 0=include)
    phase_exc_ind int,               -- Phase exclusion indicator (1=exclude, 0=include)
    centromere_ind int,              -- Centromere region indicator (1=centromere, 0=not)
    in_normal int                    -- Present in normal sample (1=yes, 0=no)
)
```

### VCF Tables

#### `mutect` (Mutect Variant Calls)

**Complete Schema:**
```sql
mutect (
    chrom string,                    -- Chromosome
    pos string,                      -- Position (note: string type)
    id string,                       -- Variant ID
    ref string,                      -- Reference allele
    alt string,                      -- Alternative allele
    qual string,                     -- Quality score
    filter string,                   -- Filter status
    info string,                     -- Info field
    format string,                   -- Format field
    normal_stat string,              -- Normal sample statistics
    tumor_stat string,               -- Tumor sample statistics
    info_mbq string,                 -- Median base quality
    info_tlod string,                -- Tumor LOD score
    info_mpos string,                -- Median position
    info_mq string,                  -- Mapping quality
    tumor string,                    -- Tumor sample data
    normal string                    -- Normal sample data
)
PARTITIONED BY (
    org_dataset string,              -- Original dataset
    subject string,                  -- Subject identifier
    file_id string                   -- File identifier
)
```

#### Other VCF Tables
- **`strelka`**: Strelka variant calls (same structure as mutect)
- **`mutect_strelka_intersect`**: Intersection of calls (same structure as mutect)
- **`normal_het_germline`**: Germline heterozygous variants
- **`strelka_annotated`**: Annotated Strelka calls

---

## Database: `external` (Reference Data)

### Tables Overview
- **`bad_mappability_regions`** - Regions with poor mappability
- **`bad_mappability_sites`** - Sites with poor mappability
- **`centromere_regions`** - Centromere region coordinates
- **`igv_repeats`** - IGV repeat regions
- **`phase_exclusion_list`** - Sites excluded from phasing

---

## Database: `external` (Reference Data)

### Tables Overview
- **`gnomad_exclusion_sites`** - gnomAD population frequency exclusion sites
- **`bad_mappability_positions`** - Sites with poor mappability
- **`bad_mappability_all_pos`** - All bad mappability positions
- **`phase_exclusion_list`** - Sites excluded from phasing
- **`centromere_regions`** - Centromere region coordinates
- **`bach_results`** - BACH analysis results
- **`digital_pathology_bach`** - Digital pathology datasets
- **`histograms_full`** - Full histogram data (reference)
- **`igv_repeats`** - IGV repeat regions
- **`rna_vcf_variants`** - RNA variant calls

### Table: `gnomad_exclusion_sites`

**Complete Schema:**
```sql
gnomad_exclusion_sites (
    pos bigint,                      -- Genomic position
    alt string                       -- Alternative allele
)
PARTITIONED BY (
    chrom string                     -- Chromosome identifier
)
```

### Table: `bad_mappability_positions`

**Complete Schema:**
```sql
bad_mappability_positions (
    chrom string,                    -- Chromosome identifier
    pos bigint                       -- Genomic position
)
```

### Table: `phase_exclusion_list`

**Complete Schema:**
```sql
phase_exclusion_list (
    count bigint,                    -- Count value
    chrom string,                    -- Chromosome identifier
    pos bigint                       -- Genomic position
)
```

### Table: `centromere_regions`

**Complete Schema:**
```sql
centromere_regions (
    start bigint,                    -- Region start position
    end bigint,                      -- Region end position
    gaptype string,                  -- Type of gap
    chr string                       -- Chromosome identifier
)
```

---

## Database: `sandbox` (Development Environment)

### Tables Overview (21 tables total)
- **`mrd_site_based_features`** - MRD features (sandbox copy)
- **`mrd_sample_based_features`** - Sample-level MRD features
- **`mrd_comprehensive_dataset`** - Comprehensive MRD dataset
- **`alg_ag_outputs`** - Algorithm output results
- **`all_distinct_sites_unfiltered`** - All distinct genomic sites
- **`exclusion_list`** - Exclusion lists for various purposes
- **`site_based_features`** - Site-based feature data
- Various testing and algorithm development tables

### Table: `mrd_comprehensive_dataset`

**Complete Schema:**
```sql
mrd_comprehensive_dataset (
    sample_id string,
    subject_id string,
    chrom string,
    pos bigint,
    ref string,
    alt string,
    refcount bigint,
    nrefcount bigint,
    total_coverage bigint,
    passed_all_dr_filters boolean
)
```

---

## Best Practices

### Query Guidelines
- **Use main database for analytics** - Focus on `main.histograms_snv`, `main.dataset_record`, `main.mrd_site_based_features`
- **Always include partition keys** in WHERE clauses for optimal performance
- **Use specific dataset filters** when querying cross-dataset tables
- **Include subject filters** when analyzing specific subjects
- **Leverage file_id mappings** through `dataset_record` table
- **Use the `mrd_site_based_features` view** for MRD calculations

### Performance Tips
- **Filter by partition values** for optimal performance: `dataset`, `subject`, `run_name`, `algo_version`, `rp_file_id`
- **Avoid broad queries without partition filters**
- **Use two-step process**: metadata discovery → analytics query
- **Limit large result sets** with `LIMIT` clause

### Common Query Patterns

#### Dataset Discovery
```sql
-- Find available datasets and subjects with VCF data
SELECT DISTINCT 
    dataset,
    subject,
    COUNT(DISTINCT snv_vcf_file_id) as vcf_count
FROM main.dataset_record 
WHERE snv_vcf_file_id IS NOT NULL
GROUP BY dataset, subject
ORDER BY dataset, subject;
```

#### Sample Listing
```sql
-- Get all samples for a specific dataset
SELECT DISTINCT dataset, subject, sample
FROM main.histograms_snv
WHERE dataset = 'YOUR_DATASET'
ORDER BY subject, sample;
```

#### MRD Analysis
```sql
-- Use MRD features view for analysis
SELECT dataset, subject, sample, chrom, pos, ref, alt,
       refcount, nrefcount, 
       pass_ffpe_filter, bad_map_ind, phase_exc_ind, in_normal
FROM main.mrd_site_based_features
WHERE dataset = 'YOUR_DATASET'
  AND pass_ffpe_filter = 1
  AND bad_map_ind = 0
  AND phase_exc_ind = 0
  AND in_normal = 0;
```

## Troubleshooting

### Common Issues
1. **Column not found:** Check if column names need double quotes
2. **No partitions found:** Verify partition values are correct  
3. **Query timeout:** Add more specific partition filters
4. **Permission denied:** Ensure AWS credentials are configured

### Data Relationships
- **Histogram Data**: Links to VCF files via `dataset_record` table
- **File Mapping**: Use `main.dataset_record` to map subjects to VCF file IDs
- **MRD Analysis**: Use `main.mrd_site_based_features` view (pre-computed)

