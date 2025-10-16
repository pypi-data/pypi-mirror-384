#!/usr/bin/env python3
"""
Count barcodes in short-read sequencing data
"""

import os
import gzip
import pandas as pd
import logging
from pathlib import Path
from Bio import SeqIO
from collections import Counter, defaultdict
import multiprocessing as mp
from functools import partial

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_read_chunk_worker(read_chunk, barcode_length, min_quality):
    """
    Worker function to process a chunk of reads for barcode extraction
    
    Args:
        read_chunk: List of Bio.SeqIO records
        barcode_length: Expected length of barcode
        min_quality: Minimum average quality for barcode
        
    Returns:
        Counter object with barcode counts for this chunk
    """
    barcode_counts = Counter()
    valid_barcodes = 0
    
    for record in read_chunk:
        # Extract barcode from 5' end
        if len(record.seq) >= barcode_length:
            barcode_seq = str(record.seq[:barcode_length])
            barcode_quals = record.letter_annotations["phred_quality"][:barcode_length]
            
            # Check quality
            avg_quality = sum(barcode_quals) / len(barcode_quals)
            
            if avg_quality >= min_quality:
                barcode_counts[barcode_seq] += 1
                valid_barcodes += 1
    
    return barcode_counts, valid_barcodes

def extract_barcodes_from_short_reads(input_file, barcode_map_file, min_quality=20, max_workers=None):
    """
    Extract and count barcodes from short-read data - OPTIMIZED VERSION
    
    Args:
        input_file: Input FASTQ file
        barcode_map_file: CSV file with barcode→variant mapping (used to determine barcode length)
        min_quality: Minimum average quality for barcode
        max_workers: Maximum number of worker processes (None = auto-detect)
        
    Returns:
        Counter object with barcode counts
    """
    
    # Determine barcode length from the barcode mapping file
    logger.info(f"Determining barcode length from {barcode_map_file}")
    try:
        barcode_mapping = pd.read_csv(barcode_map_file)
        if 'barcode' in barcode_mapping.columns and len(barcode_mapping) > 0:
            # Check that all barcodes have the same length
            barcode_lengths = barcode_mapping['barcode'].str.len()
            unique_lengths = barcode_lengths.unique()
            
            if len(unique_lengths) == 1:
                barcode_length = unique_lengths[0]
                logger.info(f"Auto-detected barcode length: {barcode_length}bp (consistent across {len(barcode_mapping)} barcodes)")
            else:
                logger.warning(f"Inconsistent barcode lengths found: {unique_lengths}")
                logger.warning(f"Using most common length: {barcode_lengths.mode().iloc[0]}bp")
                barcode_length = barcode_lengths.mode().iloc[0]
        else:
            raise ValueError("No barcode column found in mapping file")
    except Exception as e:
        logger.warning(f"Could not determine barcode length from mapping file: {e}")
        logger.warning("Using default barcode length of 20bp")
        barcode_length = 20
    
    # Intelligent worker count limiting
    total_cores = mp.cpu_count()
    if max_workers is None:
        # Limit workers to prevent system overload
        max_workers = min(total_cores, 8)  # Cap at 8 workers max
    else:
        # Respect user setting but cap it
        max_workers = min(max_workers, total_cores, 16)  # Cap at 16 workers max
    
    logger.info(f"Processing {input_file}")
    logger.info(f"Barcode length: {barcode_length}, Min quality: {min_quality}")
    logger.info(f"Using {max_workers} workers (out of {total_cores} available cores)")
    
    # Check file size to decide on processing strategy
    file_size_mb = os.path.getsize(input_file) / (1024 * 1024)
    logger.info(f"Input file size: {file_size_mb:.1f} MB")
    
    # Choose processing strategy based on file size and worker count
    if file_size_mb > 500:  # Very large files - use streaming
        logger.info("Using streaming processing for very large file")
        return extract_barcodes_streaming_single(input_file, barcode_length, min_quality)
    elif max_workers <= 2:  # Small worker count - use in-memory
        logger.info("Using in-memory processing for small file with few workers")
        return extract_barcodes_in_memory(input_file, barcode_length, min_quality, max_workers)
    else:  # Medium files with many workers - use streaming to avoid memory issues
        logger.info("Using streaming processing to avoid memory issues with many workers")
        return extract_barcodes_streaming_single(input_file, barcode_length, min_quality)

def extract_barcodes_in_memory(input_file, barcode_length, min_quality, max_workers):
    """
    In-memory processing for small files with few workers
    """
    logger.info("Using in-memory processing for small file")
    
    # Read all records into memory
    if input_file.endswith('.gz'):
        file_handle = gzip.open(input_file, 'rt')
    else:
        file_handle = open(input_file, 'r')
    
    try:
        all_records = list(SeqIO.parse(file_handle, "fastq"))
        total_reads = len(all_records)
    finally:
        file_handle.close()
    
    logger.info(f"Loaded {total_reads} reads, starting processing...")
    
    # Process in chunks
    chunk_size = max(5000, total_reads // (max_workers * 2))  # 2 chunks per worker
    chunks = [all_records[i:i+chunk_size] for i in range(0, total_reads, chunk_size)]
    
    logger.info(f"Created {len(chunks)} chunks of ~{chunk_size} reads each")
    
    # Process chunks
    if len(chunks) == 1 or max_workers == 1:
        # Sequential processing
        barcode_counts = Counter()
        valid_barcodes = 0
        
        for record in all_records:
            if len(record.seq) >= barcode_length:
                barcode_seq = str(record.seq[:barcode_length])
                barcode_quals = record.letter_annotations["phred_quality"][:barcode_length]
                avg_quality = sum(barcode_quals) / len(barcode_quals)
                
                if avg_quality >= min_quality:
                    barcode_counts[barcode_seq] += 1
                    valid_barcodes += 1
    else:
        # Parallel processing
        with mp.Pool(processes=max_workers) as pool:
            worker_func = partial(process_read_chunk_worker, 
                                barcode_length=barcode_length, 
                                min_quality=min_quality)
            chunk_results = pool.map(worker_func, chunks)
            
            # Combine results efficiently
            barcode_counts = Counter()
            valid_barcodes = 0
            
            for chunk_barcode_counts, chunk_valid_barcodes in chunk_results:
                barcode_counts.update(chunk_barcode_counts)
                valid_barcodes += chunk_valid_barcodes
    
    logger.info(f"In-memory processing complete: {total_reads} reads, {valid_barcodes} valid barcodes")
    logger.info(f"Found {len(barcode_counts)} unique barcodes")
    
    return barcode_counts

def extract_barcodes_streaming_optimized(input_file, barcode_length, min_quality, max_workers):
    """
    Optimized streaming approach - FIXED VERSION
    """
    logger.info("Using optimized streaming processing")
    
    # For streaming, use single worker to avoid file seeking issues
    # Multi-worker streaming with file seeking is complex and error-prone
    logger.info("Using single-threaded streaming for reliability")
    return extract_barcodes_streaming_single(input_file, barcode_length, min_quality)


def extract_barcodes_streaming_single(input_file, barcode_length, min_quality):
    """
    Single-threaded streaming approach (fallback)
    """
    logger.info("Using single-threaded streaming processing")
    
    barcode_counts = Counter()
    total_reads = 0
    valid_barcodes = 0
    
    if input_file.endswith('.gz'):
        file_handle = gzip.open(input_file, 'rt')
    else:
        file_handle = open(input_file, 'r')
    
    try:
        for record in SeqIO.parse(file_handle, "fastq"):
            total_reads += 1
            
            if len(record.seq) >= barcode_length:
                barcode_seq = str(record.seq[:barcode_length])
                barcode_quals = record.letter_annotations["phred_quality"][:barcode_length]
                avg_quality = sum(barcode_quals) / len(barcode_quals)
                
                if avg_quality >= min_quality:
                    barcode_counts[barcode_seq] += 1
                    valid_barcodes += 1
            
            if total_reads % 100000 == 0:
                logger.info(f"Processed {total_reads} reads, found {valid_barcodes} valid barcodes")
    
    finally:
        file_handle.close()
    
    logger.info(f"Single-threaded streaming complete: {total_reads} reads, {valid_barcodes} valid barcodes")
    logger.info(f"Found {len(barcode_counts)} unique barcodes")
    
    return barcode_counts

def map_barcodes_to_variants(barcode_counts, barcode_map_file):
    """
    Map barcode counts to variants using the barcode mapping
    
    Args:
        barcode_counts: Counter with barcode counts
        barcode_map_file: CSV file with barcode→variant mapping
        
    Returns:
        DataFrame with barcode counts and variant annotations
    """
    
    # Load barcode mapping
    logger.info(f"Loading barcode mapping from {barcode_map_file}")
    barcode_mapping = pd.read_csv(barcode_map_file)
    
    # Create mapping dictionary
    barcode_to_mutation = dict(zip(barcode_mapping['barcode'], barcode_mapping['mutation']))
    
    # Map barcodes to variants
    results = []
    mapped_barcodes = 0
    unmapped_barcodes = 0
    
    for barcode, count in barcode_counts.items():
        if barcode in barcode_to_mutation:
            mutation = barcode_to_mutation[barcode]
            mapped_barcodes += 1
        else:
            mutation = "UNMAPPED"
            unmapped_barcodes += 1
        
        results.append({
            'barcode': barcode,
            'mutation': mutation,
            'count': count
        })
    
    logger.info(f"Mapped {mapped_barcodes} barcodes, {unmapped_barcodes} unmapped")
    
    return pd.DataFrame(results)

def aggregate_variant_counts(barcode_results):
    """
    Aggregate barcode counts by variant
    
    Args:
        barcode_results: DataFrame with barcode counts and mutations
        
    Returns:
        DataFrame with variant counts
    """
    
    # Sum counts by mutation
    variant_counts = barcode_results.groupby('mutation')['count'].sum().reset_index()
    variant_counts = variant_counts.sort_values('count', ascending=False)
    
    logger.info(f"Aggregated into {len(variant_counts)} unique variants")
    
    return variant_counts

if __name__ == "__main__":
    # Get parameters from Snakemake
    input_file = snakemake.input.reads
    barcode_map_file = snakemake.input.barcode_map
    output_file = snakemake.output.barcode_counts
    
    min_quality = snakemake.params.min_quality
    max_workers = snakemake.params.get('max_workers', None)
    
    # Create output directory
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Extract and count barcodes
    logger.info("Extracting barcodes from short reads...")
    barcode_counts = extract_barcodes_from_short_reads(
        input_file, barcode_map_file, min_quality, max_workers
    )
    
    # Map barcodes to variants
    logger.info("Mapping barcodes to variants...")
    barcode_results = map_barcodes_to_variants(barcode_counts, barcode_map_file)
    
    # Aggregate by variant
    logger.info("Aggregating variant counts...")
    variant_counts = aggregate_variant_counts(barcode_results)
    
    # Save results
    # Save both barcode-level and variant-level counts
    output_data = {
        'barcode_counts': barcode_results.to_dict('records'),
        'variant_counts': variant_counts.to_dict('records'),
        'summary': {
            'total_barcodes': len(barcode_results),
            'total_reads': barcode_results['count'].sum(),
            'unique_variants': len(variant_counts),
            'mapped_barcodes': len(barcode_results[barcode_results['mutation'] != 'UNMAPPED'])
        }
    }
    
    # Save variant counts in the same format as direct amplicon pipeline
    variant_counts.to_csv(output_file, index=False)
    
    logger.info(f"Barcode counting complete! Results saved to {output_file}")
    
    # Log summary
    total_reads = barcode_results['count'].sum()
    unique_variants = len(variant_counts)
    logger.info(f"Summary: {total_reads:,} total reads, {unique_variants} unique variants")
