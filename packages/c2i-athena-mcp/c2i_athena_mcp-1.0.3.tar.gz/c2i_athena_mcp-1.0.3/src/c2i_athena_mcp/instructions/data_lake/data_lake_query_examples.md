# Data Lake Query Examples (Athena)

## Dataset Discovery Queries


### List Samples in Dataset
```sql
-- Get all samples for a specific dataset
SELECT DISTINCT dataset, subject, sample, sample_type
FROM main.histograms_snv
WHERE dataset = 'YOUR_DATASET'
ORDER BY subject, sample;
```

## Histogram Analytics Examples

### Basic Histogram Query
```sql
-- Query histogram data for specific sample
SELECT chrom, pos, ref, alt, cov, alt_tot_count, 
       a, t, g, c, sample, sample_type
FROM main.histograms_snv
WHERE dataset = 'YOUR_DATASET'
  AND subject = 'YOUR_SUBJECT'
  AND sample = 'YOUR_SAMPLE'
  AND run_name = 'YOUR_RUN_NAME'
  AND algo_version = 'YOUR_ALGO_VERSION'
ORDER BY chrom, pos
LIMIT 100;
```

### Check Available Partitions
```sql
-- Check available partitions
SHOW PARTITIONS main.histograms_snv;
```


## VCF Variant Queries

### Query Mutect Variants
```sql
-- Query Mutect variant calls
SELECT chrom, pos, ref, alt, qual, filter, 
       info_tlod, info_mq, info_mpos
FROM main.mutect
WHERE org_dataset = 'YOUR_DATASET'
  AND subject = 'YOUR_SUBJECT'
  AND file_id = 'YOUR_FILE_ID'
ORDER BY chrom, CAST(pos AS INTEGER)
LIMIT 100;
```

### Find Available Datasets and Subjects and VCF 
```sql
-- Map subjects to their VCF files
SELECT 
    dataset, subject, normal, tumor,
    snv_vcf_file_id, strelka_vcf_file_id, mutect_vcf_file_id
FROM main.dataset_record
WHERE dataset = 'YOUR_DATASET'
ORDER BY subject;
```

## MRD Analysis Queries

### Using MRD Features View
```sql
-- Query MRD features with filtering indicators
SELECT dataset, subject, sample, chrom, pos, ref, alt,
       refcount, nrefcount, cov,
       pass_ffpe_filter, bad_map_ind, gnomad_ac3_ind, 
       phase_exc_ind, centromere_ind, in_normal
FROM main.mrd_site_based_features
WHERE dataset = 'YOUR_DATASET'
  AND subject = 'YOUR_SUBJECT'
  AND sample = 'YOUR_SAMPLE'
  AND pass_ffpe_filter = 1
  AND bad_map_ind = 0
  AND phase_exc_ind = 0
  AND in_normal = 0
ORDER BY chrom, pos
LIMIT 100;
```

**Important Notes:**
- **Primary Database**: Use `main` for all analytics queries
- **Ignore `raw_main`**: Contains raw/unprocessed data - not for analytics
- **Partition Strategy**: Always include `dataset`, `subject`, `run_name`, `algo_version`, `rp_file_id` in WHERE clauses
- **MRD Analysis**: Use `main.mrd_site_based_features` view for pre-computed features
- **File Mapping**: Use `main.dataset_record` to link subjects to VCF files

**Histogram-VCF Connection:**
- **VCF Files** → Generated from tumor and normal tissue samples
- **Histograms** → Generated from VCF variants + plasma sample 
- **Connection**: Same `subject` and `dataset`
- **Mapping**: Use `main.dataset_record` table to join histograms and VCF data