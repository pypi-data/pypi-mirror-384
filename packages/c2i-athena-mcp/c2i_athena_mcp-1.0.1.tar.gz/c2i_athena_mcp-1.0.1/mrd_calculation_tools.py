"""
MRD (Minimal Residual Disease) Calculation Tools Version 2 for Athena MCP Server
===============================================================================

This module implements MRD calculation tools
as specified in the MRD Detection Rate Calculation Instructions.

Core Formula: detection_rate = sites_with_alt / (sites_with_alt + total_ref_sites)
where sites_with_alt = SUM(LEAST(nrefcount, 1))

Author: C2i Genomics Data Science Team
Version: 2.0
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MRDCalculator:
    """
    MRD (Minimal Residual Disease) Calculator Version 2
    
    Implements filtering pipeline
    as specified in the MRD Detection Rate Calculation Instructions.
    
    Core Formula: detection_rate = sites_with_alt / (sites_with_alt + total_ref_sites)
    where sites_with_alt = SUM(LEAST(nrefcount, 1))
    """
    
    def __init__(self, athena_client):
        self.athena_client = athena_client
        
    def calculate_mrd_score_for_sample(
        self, 
        dataset: str, 
        run_name: Optional[str] = None, 
        algo_version: Optional[str] = None,
        subject: str = None,
        sample: str = None,
        database: str = "main"
    ) -> Dict[str, Any]:
        """
        Calculate MRD detection rate for a specific sample or subject.
        
        Args:
            dataset: Dataset name for partitioning
            run_name: Optional run name for partitioning  
            algo_version: Optional algorithm version for partitioning
            subject: Subject identifier
            sample: Sample identifier
            database: Database name (default: "main")
            
        Returns:
            Dict containing:
            - dataset, run_name, algo_version, subject, sample
            - sites_with_alt: Number of sites with alternative alleles
            - total_sites: Total number of sites after filtering
            - detection_rate: MRD detection rate (0-1)
            - status: Operation status
        """
        
        query = self._build_single_sample_query(dataset, run_name, algo_version, subject, sample)
        
        try:
            result = self.athena_client.execute_query_with_summary(query, database)
            
            if result["status"] == "SUCCEEDED":
                rows = result.get("rows", [])
                runtime_seconds = result.get("runtime_seconds", 0)
                data_scanned_mb = result.get("data_scanned_mb", 0)
                
                if not rows or len(rows) == 0:
                    return {
                        'dataset': dataset,
                        'run_name': run_name, 
                        'algo_version': algo_version,
                        'subject': subject,
                        'sample': sample,
                        'sites_with_alt': None,
                        'total_sites': None,
                        'detection_rate': None,
                        'status': 'no_data',
                        'query_execution_id': result["execution_id"]
                    }
                    
                row = rows[0]
                
                # Since rows are in CSV format (list of lists), use positional access
                # Expected columns: dataset, run_name, algo_version, subject, sample, sites_with_alt, total_sites, detection_rate
                try:
                    sites_with_alt = int(row[5]) if len(row) > 5 and row[5] is not None and str(row[5]).strip() else 0
                    total_sites = int(row[6]) if len(row) > 6 and row[6] is not None and str(row[6]).strip() else 0
                    detection_rate = float(row[7]) if len(row) > 7 and row[7] is not None and str(row[7]).strip() else 0.0
                except (ValueError, TypeError, IndexError):
                    # Fallback for non-numeric values - use None instead of 0
                    sites_with_alt = None
                    total_sites = None
                    detection_rate = None
                
                return {
                    'dataset': str(row[0]) if len(row) > 0 else dataset,
                    'run_name': str(row[1]) if len(row) > 1 else run_name,
                    'algo_version': str(row[2]) if len(row) > 2 else algo_version,
                    'subject': str(row[3]) if len(row) > 3 else subject,
                    'sample': str(row[4]) if len(row) > 4 else sample,
                    'sites_with_alt': sites_with_alt,
                    'total_sites': total_sites,
                    'detection_rate': f"{detection_rate:.15f}" if detection_rate is not None else None,
                    'status': 'success',
                    'query_execution_id': result["execution_id"],
                    'runtime_seconds': runtime_seconds,
                    'data_scanned_mb': data_scanned_mb
                }
            else:
                raise Exception(f"Query failed: {result.get('error_reason', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error calculating MRD for sample {sample}: {str(e)}")
            return {
                'dataset': dataset,
                'run_name': run_name,
                'algo_version': algo_version, 
                'subject': subject,
                'sample': sample,
                'sites_with_alt': None,
                'total_sites': None,
                'detection_rate': None,
                'status': 'error',
                'error': str(e)
            }
    
    def calculate_mrd_for_dataset(
        self,
        dataset: str,
        run_name: Optional[str] = None, 
        algo_version: Optional[str] = None,
        database: str = "main"
    ) -> List[Dict[str, Any]]:
        """
        Calculate MRD detection rates for all samples in a dataset.
        
        Args:
            dataset: Dataset name for partitioning
            run_name: Optional run name for partitioning
            algo_version: Optional algorithm version for partitioning
            database: Database name (default: "main")
            
        Returns:
            List of dicts, each containing:
            - dataset, run_name, algo_version, subject, sample
            - sites_with_alt: Number of sites with alternative alleles
            - total_sites: Total number of sites after filtering
            - detection_rate: MRD detection rate (0-1)
        """
        
        query = self._build_dataset_query(dataset, run_name, algo_version)
        try:
            result = self.athena_client.execute_query_with_summary(query, database)
            
            if result["status"] == "SUCCEEDED":
                formatted_results = []
                rows = result.get("rows", [])
                columns = result.get("columns", [])
                runtime_seconds = result.get("runtime_seconds", 0)
                data_scanned_mb = result.get("data_scanned_mb", 0)

                for row in rows:
                    # Since rows are in CSV format (list of lists), use positional access
                    # Expected columns: dataset, run_name, algo_version, subject, sample, sites_with_alt, total_sites, detection_rate
                    try:
                        sites_with_alt = int(row[5]) if len(row) > 5 and row[5] is not None and str(row[5]).strip() else 0
                        total_sites = int(row[6]) if len(row) > 6 and row[6] is not None and str(row[6]).strip() else 0
                        detection_rate = float(row[7]) if len(row) > 7 and row[7] is not None and str(row[7]).strip() else 0.0
                        
                    except (ValueError, TypeError, IndexError):
                        # Fallback for non-numeric values - use None instead of 0
                        sites_with_alt = None
                        total_sites = None
                        detection_rate = None
                        
                    formatted_results.append({
                        'dataset': str(row[0]) if len(row) > 0 else dataset,
                        'run_name': str(row[1]) if len(row) > 1 else run_name,
                        'algo_version': str(row[2]) if len(row) > 2 else algo_version,
                        'subject': str(row[3]) if len(row) > 3 else '',
                        'sample': str(row[4]) if len(row) > 4 else '',
                        'sites_with_alt': sites_with_alt,
                        'total_sites': total_sites,
                        'detection_rate': f"{detection_rate:.15f}" if detection_rate is not None else None,
                        'status': 'success',
                        'runtime_seconds': runtime_seconds,
                        'data_scanned_mb': data_scanned_mb
                    })
                        
                return formatted_results
            else:
                raise Exception(f"Query failed: {result.get('error_reason', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error calculating MRD for dataset {dataset}: {str(e)}")
            return [{
                'dataset': dataset,
                'run_name': run_name,
                'algo_version': algo_version,
                'status': 'error',
                'error': str(e)
            }]
    
    def _build_single_sample_query(
        self, 
        dataset: str, 
        run_name: Optional[str] = None, 
        algo_version: Optional[str] = None,
        subject: str = None,
        sample: str = None
    ) -> str:
        """Build SQL query for single sample MRD calculation following the 7-stage pipeline."""
        
        subject_filter = ""
        if subject:
            subject_filter += f" AND mf.subject = '{subject}'"
        if sample:
            subject_filter += f" AND mf.sample = '{sample}'"
        
        return self._build_base_query(dataset, run_name, algo_version, subject_filter)
    
    def _build_dataset_query(
        self,
        dataset: str,
        run_name: Optional[str] = None,
        algo_version: Optional[str] = None
    ) -> str:
        """Build SQL query for dataset-wide MRD calculation."""
        
        return self._build_base_query(dataset, run_name, algo_version)
    
    def _build_base_query(self, dataset: str, run_name: Optional[str] = None, algo_version: Optional[str] = None, subject_filter: str = "") -> str:
        """
        Build the SQL query for MRD detection rate calculation

        This method generates a query that:
        - Uses the pre-existing view logic from mrd_site_based_features (as described in documentation)
        - Applies static quality filters: pass_ffpe_filter, bad_map_ind, phase_exc_ind, in_normal
        - Computes per-sample statistics (median, MAD) only on filtered sites
        - Applies sample-specific anomaly filters: is_global_anomalous, is_unmatched
        - Calculates detection rates per sample using the formula:
            detection_rate = sites_with_alt / (sites_with_alt + total_ref_sites)
            where sites_with_alt = SUM(LEAST(nrefcount, 1))

        Args:
            dataset: Dataset name for partitioning
            run_name: Optional run name for partitioning
            algo_version: Optional algorithm version for partitioning
            subject_filter: Additional SQL filter for subject/sample

        Returns:
            str: SQL query string for MRD detection rate calculation
        """
        # Build optional filters
        run_name_filter = f" AND mf.run_name = '{run_name}'" if run_name else ""
        algo_version_filter = f" AND mf.algo_version = '{algo_version}'" if algo_version else ""
        
        return f"""
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
    WHERE dataset = '{dataset}'
        {run_name_filter}
        {algo_version_filter}
        {subject_filter}
        AND mf.pass_ffpe_filter = 1  
        AND mf.bad_map_ind = 0
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
"""