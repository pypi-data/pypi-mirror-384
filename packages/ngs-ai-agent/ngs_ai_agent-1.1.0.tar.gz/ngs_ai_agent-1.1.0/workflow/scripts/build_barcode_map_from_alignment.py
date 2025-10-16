#!/usr/bin/env python3
"""
Build barcode→variant mapping from Bowtie2-aligned reads using GenBank annotations
"""

import os
import pandas as pd
import pysam
import logging
from pathlib import Path
from Bio import SeqIO
from Bio.SeqFeature import SeqFeature
from collections import defaultdict, Counter
import re
import multiprocessing as mp
from functools import partial

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _manual_fasta_parse(reference_file):
    """
    Manually parse FASTA file, skipping comment lines
    """
    sequence_lines = []
    all_lines = []
    
    with open(reference_file, 'r') as f:
        in_sequence = False
        for line_num, line in enumerate(f, 1):
            original_line = line
            line = line.strip()
            all_lines.append(f"Line {line_num}: {repr(original_line[:100])}")  # For debugging
            
            if not line:
                continue
            if line.startswith('>'):
                in_sequence = True
                logger.info(f"Found FASTA header at line {line_num}: {line}")
                continue
            elif line.startswith(('#', ';', '!')):
                # Skip comment lines
                logger.debug(f"Skipping comment line {line_num}: {line}")
                continue
            elif in_sequence:
                # Check if line looks like DNA sequence
                if all(c.upper() in 'ATCGRYSWKMBDHVN-' for c in line):
                    sequence_lines.append(line)
                else:
                    logger.warning(f"Line {line_num} doesn't look like DNA sequence: {line}")
            else:
                # We haven't found a header yet, but this might be sequence data
                if all(c.upper() in 'ATCGRYSWKMBDHVN-' for c in line):
                    logger.info(f"Found sequence data without header at line {line_num}")
                    sequence_lines.append(line)
                    in_sequence = True
    
    # Debug output
    logger.info(f"File analysis: {len(all_lines)} total lines")
    if len(all_lines) <= 20:
        for debug_line in all_lines:
            logger.debug(debug_line)
    else:
        logger.debug("First 10 lines:")
        for debug_line in all_lines[:10]:
            logger.debug(debug_line)
        logger.debug("Last 10 lines:")
        for debug_line in all_lines[-10:]:
            logger.debug(debug_line)
    
    if not sequence_lines:
        logger.error("No sequence found in FASTA file")
        logger.error(f"Analyzed {len(all_lines)} lines, found no valid sequence data")
        raise ValueError("No sequence found in FASTA file")
    
    sequence = ''.join(sequence_lines)
    logger.info(f"Successfully parsed {len(sequence_lines)} sequence lines, total length: {len(sequence)} bp")
    return sequence

def parse_genbank_annotations(reference_file):
    """
    Parse GenBank file to extract barcode and gene region coordinates
    
    Args:
        reference_file: GenBank (.gb) or FASTA file
        
    Returns:
        Dict with region coordinates and reference sequence
    """
    
    regions = {
        'barcode': None,
        'gene': None,
        'reference_seq': None
    }
    
    logger.info(f"Attempting to parse reference file: {reference_file}")
    
    # Check if file exists and show first few lines for debugging
    if not os.path.exists(reference_file):
        raise FileNotFoundError(f"Reference file not found: {reference_file}")
    
    # Show first few lines for debugging
    with open(reference_file, 'r') as f:
        first_lines = [f.readline().strip() for _ in range(3)]
        logger.info(f"First 3 lines of reference file: {first_lines}")
    
    try:
        # Try to parse as GenBank first - check file extension AND content
        is_genbank = (reference_file.endswith('.gb') or reference_file.endswith('.gbk') or 
                     first_lines[0].startswith('LOCUS'))
        
        if is_genbank:
            logger.info("Detected GenBank format, parsing annotations...")
            record = next(SeqIO.parse(reference_file, "genbank"))
            regions['reference_seq'] = str(record.seq)
            logger.info(f"Loaded GenBank sequence: {len(regions['reference_seq'])} bp")
            
            # Extract feature coordinates
            logger.info(f"Processing {len(record.features)} features from GenBank file")
            for i, feature in enumerate(record.features):
                logger.info(f"Feature {i}: type={feature.type}, location={feature.location}")
                logger.info(f"  Qualifiers: {feature.qualifiers}")
                
                # Check for barcode region - look in feature type/name or qualifiers
                qualifier_str = str(feature.qualifiers).lower()
                feature_name = feature.type.lower()
                
                logger.info(f"  Checking barcode: feature_name='{feature_name}', qualifier_str='{qualifier_str}'")
                
                if (feature_name in ['barcode', 'tag', 'identifier', 'primer', 'adapter'] or
                    any(keyword in qualifier_str for keyword in ['barcode', 'tag', 'identifier', 'primer', 'adapter'])):
                    if not regions['barcode']:  # Only take the first one found
                        # Convert from 0-based (BioPython) to 1-based (GenBank) coordinates
                        regions['barcode'] = {
                            'start': int(feature.location.start) + 1,  # Convert to 1-based
                            'end': int(feature.location.end),  # End is already 1-based
                            'strand': feature.location.strand
                        }
                        logger.info(f"Found barcode region: {feature.type} at {feature.location} with qualifiers: {feature.qualifiers}")
                        logger.info(f"Converted to 1-based coordinates: {regions['barcode']}")
                    else:
                        logger.info(f"Barcode region already found, skipping: {feature.type} at {feature.location}")
                else:
                    logger.info(f"  No barcode match for feature: {feature.type}")
                
                # Check for gene region - look in CDS, gene, or any feature with gene-related qualifiers
                if (feature.type in ["CDS", "gene", "mRNA"] or 
                      any(keyword in qualifier_str for keyword in ['gene', 'product', 'protein', 'orf'])):
                    if not regions['gene']:  # Only take the first one found
                        # Convert from 0-based (BioPython) to 1-based (GenBank) coordinates
                        regions['gene'] = {
                            'start': int(feature.location.start) + 1,  # Convert to 1-based
                            'end': int(feature.location.end),  # End is already 1-based
                            'strand': feature.location.strand
                        }
                        logger.info(f"Found gene region: {feature.type} at {feature.location} with qualifiers: {feature.qualifiers}")
                        logger.info(f"Converted to 1-based coordinates: {regions['gene']}")
                
                # Log any interesting features
                if any(keyword in qualifier_str for keyword in ['barcode', 'tag', 'identifier', 'primer', 'adapter', 'gene', 'product', 'protein']):
                    logger.info(f"Found relevant feature: {feature.type} at {feature.location} with qualifiers: {feature.qualifiers}")
        
        else:
            # Parse as FASTA and use default regions
            logger.info("Detected FASTA format, parsing sequence...")
            try:
                # Try standard FASTA first
                record = next(SeqIO.parse(reference_file, "fasta"))
                regions['reference_seq'] = str(record.seq)
                logger.info(f"Loaded FASTA sequence: {len(regions['reference_seq'])} bp")
            except StopIteration:
                logger.warning("Standard FASTA parsing failed, trying alternative formats...")
                # If that fails, try FASTA with comments (fasta-pearson format)
                try:
                    record = next(SeqIO.parse(reference_file, "fasta-pearson"))
                    regions['reference_seq'] = str(record.seq)
                    logger.info(f"Parsed FASTA file with comments using fasta-pearson format: {len(regions['reference_seq'])} bp")
                except StopIteration:
                    logger.warning("BioPython FASTA parsing failed, trying manual parsing...")
                    # If still fails, try reading the file manually
                    regions['reference_seq'] = _manual_fasta_parse(reference_file)
                    logger.info(f"Parsed FASTA file manually, skipping comment lines: {len(regions['reference_seq'])} bp")
            
            logger.warning("FASTA file provided - using default region coordinates")
            
    except Exception as e:
        logger.error(f"Error parsing reference file: {e}")
        raise
    
    # Set default regions if not found in annotations
    ref_len = len(regions['reference_seq'])
    if not regions['barcode']:
        # Use first 30 bp as barcode region (more reasonable default)
        barcode_len = min(30, ref_len // 10)  # 10% of sequence or 30bp, whichever is smaller
        regions['barcode'] = {'start': 0, 'end': barcode_len, 'strand': 1}
        logger.warning(f"No barcode region found, using default: 0-{barcode_len}")
    
    if not regions['gene']:
        # Use most of the sequence as gene region, starting after barcode
        gene_start = regions['barcode']['end'] + 10  # 10bp gap after barcode
        gene_end = ref_len - 10  # Leave 10bp at the end
        regions['gene'] = {'start': gene_start, 'end': gene_end, 'strand': 1}
        logger.warning(f"No gene region found, using default: {gene_start}-{gene_end}")
    
    logger.info(f"Final regions - Barcode: {regions['barcode']}, Gene: {regions['gene']}")
    
    return regions

def extract_barcode_and_variant_from_alignment(bam_file, regions):
    """
    Extract barcode and variant sequences from aligned reads
    
    Args:
        bam_file: BAM file with aligned reads
        regions: Dictionary with barcode and gene region coordinates
        
    Returns:
        Dictionary mapping read_id to barcode and variant sequences
    """
    
    read_data = {}
    processed_reads = 0
    valid_alignments = 0
    
    logger.info(f"Processing alignments from {bam_file}")
    
    # Get BAM file statistics
    try:
        with pysam.AlignmentFile(bam_file, "rb") as bamfile:
            # Check if BAM has index
            try:
                total_reads = bamfile.count()
                mapped_reads = bamfile.mapped
                unmapped_reads = bamfile.unmapped
                logger.info(f"BAM file statistics: {total_reads} total, {mapped_reads} mapped, {unmapped_reads} unmapped")
            except Exception as e:
                logger.warning(f"Could not get BAM statistics (might need indexing): {e}")
                
            # Check reference information
            if bamfile.references:
                logger.info(f"BAM references: {list(bamfile.references)}")
                logger.info(f"BAM reference lengths: {list(bamfile.lengths)}")
            else:
                logger.warning("No reference information in BAM header")
    except Exception as e:
        logger.error(f"Error opening BAM file: {e}")
        return {}
    
    with pysam.AlignmentFile(bam_file, "rb") as bamfile:
        unmapped_count = 0
        secondary_count = 0
        no_sequence_count = 0
        no_position_count = 0
        barcode_coverage_count = 0
        gene_coverage_count = 0
        both_coverage_count = 0
        coverage_issues = 0
        
        for read in bamfile:
            processed_reads += 1
            
            if read.is_unmapped:
                unmapped_count += 1
                continue
            if read.is_secondary:
                secondary_count += 1
                continue
            if read.is_supplementary:
                continue
                
            # Get aligned sequence
            aligned_seq = read.query_sequence
            if not aligned_seq:
                no_sequence_count += 1
                continue
                
            # Get reference position mapping
            ref_start = read.reference_start
            ref_end = read.reference_end
            
            # Debug position data issues
            if ref_start is None or ref_end is None:
                no_position_count += 1
                if no_position_count <= 10:  # Log first 10 examples
                    logger.info(f"Read {processed_reads} has no position data:")
                    logger.info(f"  Query name: {read.query_name}")
                    logger.info(f"  Reference start: {ref_start}")
                    logger.info(f"  Reference end: {ref_end}")
                    logger.info(f"  Is unmapped: {read.is_unmapped}")
                    logger.info(f"  Is secondary: {read.is_secondary}")
                    logger.info(f"  Is supplementary: {read.is_supplementary}")
                    logger.info(f"  Mapping quality: {read.mapping_quality}")
                    logger.info(f"  Reference ID: {read.reference_id}")
                    logger.info(f"  CIGAR: {read.cigarstring}")
                continue
            
            # Debug successful reads (first few)
            if processed_reads <= 5:
                logger.info(f"Read {processed_reads} has position data:")
                logger.info(f"  Query name: {read.query_name}")
                logger.info(f"  Reference start: {ref_start}")
                logger.info(f"  Reference end: {ref_end}")
                logger.info(f"  Read length: {len(aligned_seq)}")
                logger.info(f"  Mapping quality: {read.mapping_quality}")
                logger.info(f"  CIGAR: {read.cigarstring}")
                
            # Extract barcode region
            barcode_region = regions['barcode']
            barcode_seq = None
            
            # Debug: Check if read covers barcode region
            # Convert 1-based region coordinates back to 0-based for BAM comparison
            barcode_start_0based = barcode_region['start'] - 1  # Convert back to 0-based
            barcode_end_0based = barcode_region['end']  # End is already correct for 0-based
            
            barcode_coverage = (ref_start <= barcode_start_0based and ref_end >= barcode_end_0based)
            if barcode_coverage:
                barcode_coverage_count += 1
                # Calculate positions in read coordinates using 0-based coordinates
                barcode_read_start = barcode_start_0based - ref_start
                barcode_read_end = barcode_end_0based - ref_start
                
                if 0 <= barcode_read_start < len(aligned_seq) and 0 <= barcode_read_end <= len(aligned_seq):
                    barcode_seq = aligned_seq[barcode_read_start:barcode_read_end]
            
            # Extract gene/variant region
            gene_region = regions['gene']
            variant_seq = None
            
            # Convert 1-based region coordinates back to 0-based for BAM comparison
            gene_start_0based = gene_region['start'] - 1  # Convert back to 0-based
            gene_end_0based = gene_region['end']  # End is already correct for 0-based
            
            gene_coverage = (ref_start <= gene_start_0based and ref_end >= gene_end_0based)
            if gene_coverage:
                gene_coverage_count += 1
                # Calculate positions in read coordinates using 0-based coordinates
                gene_read_start = gene_start_0based - ref_start
                gene_read_end = gene_end_0based - ref_start
                
                if 0 <= gene_read_start < len(aligned_seq) and 0 <= gene_read_end <= len(aligned_seq):
                    variant_seq = aligned_seq[gene_read_start:gene_read_end]
            
            # Track both region coverage
            if barcode_coverage and gene_coverage:
                both_coverage_count += 1
            else:
                coverage_issues += 1
                if coverage_issues <= 10:  # Log first few examples
                    logger.info(f"Read {processed_reads} coverage issue:")
                    logger.info(f"  Read span: {ref_start}-{ref_end} (length: {ref_end-ref_start})")
                    logger.info(f"  Barcode region (0-based): {barcode_start_0based}-{barcode_end_0based} covered: {barcode_coverage}")
                    logger.info(f"  Gene region (0-based): {gene_start_0based}-{gene_end_0based} covered: {gene_coverage}")
                    logger.info(f"  Required span: {gene_start_0based} to {barcode_end_0based} = {barcode_end_0based - gene_start_0based}bp")
            
            # Store read data if both regions were extracted
            if barcode_seq and variant_seq:
                read_data[read.query_name] = {
                    'barcode': barcode_seq,
                    'variant': variant_seq,
                    'mapping_quality': read.mapping_quality,
                    'reference_start': ref_start,
                    'reference_end': ref_end
                }
                valid_alignments += 1
            
            if processed_reads % 10000 == 0:
                logger.info(f"Processed {processed_reads} reads, {valid_alignments} valid alignments")
    
    # Debug summary
    logger.info(f"Alignment processing complete: {processed_reads} reads, {valid_alignments} valid alignments")
    logger.info(f"Debug summary:")
    logger.info(f"  - Unmapped reads: {unmapped_count}")
    logger.info(f"  - Secondary alignments: {secondary_count}")
    logger.info(f"  - No sequence data: {no_sequence_count}")
    logger.info(f"  - No position data: {no_position_count}")
    logger.info(f"  - Barcode region coverage: {barcode_coverage_count}/{processed_reads - unmapped_count - secondary_count - no_sequence_count - no_position_count} ({100*barcode_coverage_count/max(1,processed_reads - unmapped_count - secondary_count - no_sequence_count - no_position_count):.1f}%)")
    logger.info(f"  - Gene region coverage: {gene_coverage_count}/{processed_reads - unmapped_count - secondary_count - no_sequence_count - no_position_count} ({100*gene_coverage_count/max(1,processed_reads - unmapped_count - secondary_count - no_sequence_count - no_position_count):.1f}%)")
    logger.info(f"  - Both regions coverage: {both_coverage_count}/{processed_reads - unmapped_count - secondary_count - no_sequence_count - no_position_count} ({100*both_coverage_count/max(1,processed_reads - unmapped_count - secondary_count - no_sequence_count - no_position_count):.1f}%)")
    logger.info(f"  - Coverage issues (don't cover both regions): {coverage_issues}")
    logger.info(f"  - Barcode region (1-based): {regions['barcode']}")
    logger.info(f"  - Gene region (1-based): {regions['gene']}")
    # Calculate required span for summary
    if regions and regions['barcode'] and regions['gene']:
        barcode_start_summary = regions['barcode']['start'] - 1  # Convert to 0-based
        barcode_end_summary = regions['barcode']['end']
        gene_start_summary = regions['gene']['start'] - 1  # Convert to 0-based
        gene_end_summary = regions['gene']['end']
        required_span = barcode_end_summary - gene_start_summary
        logger.info(f"  - Required read span for both regions: {gene_start_summary} to {barcode_end_summary} = {required_span}bp")
    
    return read_data

def identify_mutations_from_alignment(variant_seq, reference_seq, gene_region):
    """
    Identify mutations by comparing variant sequence to reference gene region
    
    Args:
        variant_seq: Variant sequence from read
        reference_seq: Full reference sequence
        gene_region: Gene region coordinates
        
    Returns:
        String representation of mutations
    """
    
    # Extract reference gene sequence (convert 1-based coordinates to 0-based)
    gene_start_0based = gene_region['start'] - 1  # Convert to 0-based
    gene_end_0based = gene_region['end']  # End is already correct for 0-based slicing
    ref_gene_seq = reference_seq[gene_start_0based:gene_end_0based]
    
    mutations = []
    min_len = min(len(variant_seq), len(ref_gene_seq))
    
    # Debug: Log sequence lengths and first few bases
    logger.debug(f"Gene region (1-based): {gene_region['start']}-{gene_region['end']}")
    logger.debug(f"Gene region (0-based for slicing): {gene_start_0based}-{gene_end_0based}")
    logger.debug(f"Reference gene seq length: {len(ref_gene_seq)}, variant seq length: {len(variant_seq)}")
    if len(ref_gene_seq) > 0 and len(variant_seq) > 0:
        logger.debug(f"Reference gene seq start: {ref_gene_seq[:10]}...")
        logger.debug(f"Variant seq start: {variant_seq[:10]}...")
    
    # Compare sequences position by position
    codon_mutations = {}
    
    for pos in range(min_len):
        if variant_seq[pos] != ref_gene_seq[pos]:
            # Convert to codon position
            codon_pos = pos // 3
            codon_offset = pos % 3
            
            if codon_pos not in codon_mutations:
                codon_mutations[codon_pos] = {
                    'ref_codon': ref_gene_seq[codon_pos*3:(codon_pos+1)*3],
                    'var_codon': list(ref_gene_seq[codon_pos*3:(codon_pos+1)*3])
                }
            
            # Update variant codon
            if codon_offset < len(codon_mutations[codon_pos]['var_codon']):
                codon_mutations[codon_pos]['var_codon'][codon_offset] = variant_seq[pos]
    
    # Convert codon mutations to amino acid mutations
    for codon_pos, codon_data in codon_mutations.items():
        ref_codon = codon_data['ref_codon']
        var_codon = ''.join(codon_data['var_codon'])
        
        if len(ref_codon) == 3 and len(var_codon) == 3:
            try:
                from Bio.Seq import Seq
                ref_aa = str(Seq(ref_codon).translate())
                var_aa = str(Seq(var_codon).translate())
                
                if ref_aa != var_aa:
                    mutation = f"{ref_aa}{codon_pos+1}{var_aa}"
                    mutations.append(mutation)
            except:
                # Handle translation errors
                mutation = f"N{codon_pos+1}X"
                mutations.append(mutation)
    
    # Return mutation string
    if mutations:
        mutation_string = "_".join(mutations)
        logger.debug(f"Found mutations: {mutation_string}")
        return mutation_string
    else:
        logger.debug("No mutations found, returning WT")
        return "WT"

def identify_mutations_from_alignment_optimized(variant_seq, ref_gene_seq, gene_region):
    """
    Optimized version of identify_mutations_from_alignment
    Uses pre-extracted reference sequence to avoid repeated slicing
    
    Args:
        variant_seq: Variant sequence from read
        ref_gene_seq: Pre-extracted reference gene sequence
        gene_region: Gene region coordinates (for debugging)
        
    Returns:
        String representation of mutations
    """
    
    mutations = []
    min_len = min(len(variant_seq), len(ref_gene_seq))
    
    # Early return for identical sequences
    if variant_seq == ref_gene_seq:
        return "WT"
    
    # Compare sequences position by position
    codon_mutations = {}
    
    for pos in range(min_len):
        if variant_seq[pos] != ref_gene_seq[pos]:
            # Convert to codon position
            codon_pos = pos // 3
            codon_offset = pos % 3
            
            if codon_pos not in codon_mutations:
                codon_mutations[codon_pos] = {
                    'ref_codon': ref_gene_seq[codon_pos*3:(codon_pos+1)*3],
                    'var_codon': list(ref_gene_seq[codon_pos*3:(codon_pos+1)*3])
                }
            
            # Update variant codon
            if codon_offset < len(codon_mutations[codon_pos]['var_codon']):
                codon_mutations[codon_pos]['var_codon'][codon_offset] = variant_seq[pos]
    
    # Convert codon mutations to amino acid mutations
    for codon_pos, codon_data in codon_mutations.items():
        ref_codon = codon_data['ref_codon']
        var_codon = ''.join(codon_data['var_codon'])
        
        if len(ref_codon) == 3 and len(var_codon) == 3:
            try:
                from Bio.Seq import Seq
                ref_aa = str(Seq(ref_codon).translate())
                var_aa = str(Seq(var_codon).translate())
                
                if ref_aa != var_aa:
                    mutation = f"{ref_aa}{codon_pos+1}{var_aa}"
                    mutations.append(mutation)
            except:
                # Handle translation errors
                mutation = f"N{codon_pos+1}X"
                mutations.append(mutation)
    
    # Return mutation string
    if mutations:
        return "_".join(mutations)
    else:
        return "WT"

def process_mutation_chunk_worker(chunk_data, ref_gene_seq, gene_region):
    """
    Worker function to process a chunk of reads for mutation calling
    """
    chunk_results = []
    
    for read_id, data in chunk_data:
        barcode = data['barcode']
        variant_seq = data['variant']
        
        # Identify mutations with pre-extracted reference
        mutations = identify_mutations_from_alignment_optimized(
            variant_seq, ref_gene_seq, gene_region
        )
        
        chunk_results.append({
            'barcode': barcode,
            'mutation': mutations,
            'read_id': read_id,
            'mapping_quality': data['mapping_quality']
        })
    
    return chunk_results

def process_bam_file_worker(bam_file, regions):
    """
    Worker function to process a single BAM file
    Returns read data and statistics
    """
    try:
        logger.info(f"Processing {bam_file} (worker)")
        read_data = extract_barcode_and_variant_from_alignment(bam_file, regions)
        return {
            'bam_file': bam_file,
            'read_data': read_data,
            'success': True
        }
    except Exception as e:
        logger.error(f"Error processing {bam_file}: {e}")
        return {
            'bam_file': bam_file,
            'read_data': {},
            'success': False,
            'error': str(e)
        }

def build_barcode_variant_mapping(bam_files, reference_file, regions, min_coverage=5, max_workers=None):
    """
    Build barcode→variant mapping from multiple BAM files
    
    Args:
        bam_files: List of BAM files
        reference_file: Reference genome file
        regions: Region coordinates from GenBank
        min_coverage: Minimum coverage for barcode inclusion
        max_workers: Maximum number of worker processes (None = auto-detect)
        
    Returns:
        DataFrame with barcode→variant mapping
    """
    
    # Set up multiprocessing
    if max_workers is None:
        max_workers = min(len(bam_files), mp.cpu_count())
    
    logger.info(f"Processing {len(bam_files)} BAM files using {max_workers} workers")
    
    all_read_data = {}
    
    # Process BAM files in parallel
    if len(bam_files) == 1 or max_workers == 1:
        # Single file or single worker - process sequentially
        for bam_file in bam_files:
            logger.info(f"Processing {bam_file}")
            read_data = extract_barcode_and_variant_from_alignment(bam_file, regions)
            all_read_data.update(read_data)
    else:
        # Multiple files - process in parallel
        with mp.Pool(processes=max_workers) as pool:
            # Create partial function with regions fixed
            worker_func = partial(process_bam_file_worker, regions=regions)
            
            # Process BAM files in parallel
            results = pool.map(worker_func, bam_files)
            
            # Collect results
            successful_files = 0
            failed_files = 0
            
            for result in results:
                if result['success']:
                    all_read_data.update(result['read_data'])
                    successful_files += 1
                else:
                    failed_files += 1
                    logger.error(f"Failed to process {result['bam_file']}: {result.get('error', 'Unknown error')}")
            
            logger.info(f"Processing complete: {successful_files} successful, {failed_files} failed")
    
    logger.info(f"Total reads with barcode and variant data: {len(all_read_data)}")
    
    # Pre-extract reference gene sequence to avoid repeated slicing
    gene_region = regions['gene']
    gene_start_0based = gene_region['start'] - 1
    gene_end_0based = gene_region['end']
    ref_gene_seq = regions['reference_seq'][gene_start_0based:gene_end_0based]
    
    logger.info(f"Pre-extracted reference gene sequence: {len(ref_gene_seq)}bp")
    
    # Build barcode→variant mapping with optimized mutation calling
    logger.info("Starting mutation calling for all reads...")
    
    # Convert to list for easier processing
    read_items = list(all_read_data.items())
    total_reads = len(read_items)
    
    # Process in chunks to avoid memory issues and provide progress updates
    chunk_size = 10000
    barcode_variant_pairs = []
    
    # Check if we should use parallel processing for mutation calling
    mutation_workers = min(max_workers or 1, 16)  # Limit to 16 workers for mutation calling
    
    if total_reads > 50000 and mutation_workers > 1:
        # Use parallel processing for large datasets
        logger.info(f"Using parallel mutation calling with {mutation_workers} workers")
        
        # Create chunks
        chunks = [read_items[i:i+chunk_size] for i in range(0, total_reads, chunk_size)]
        
        with mp.Pool(processes=mutation_workers) as pool:
            # Create partial function with fixed parameters
            worker_func = partial(process_mutation_chunk_worker, 
                                ref_gene_seq=ref_gene_seq, 
                                gene_region=gene_region)
            
            # Process chunks in parallel
            chunk_results = pool.map(worker_func, chunks)
            
            # Flatten results
            for chunk_result in chunk_results:
                barcode_variant_pairs.extend(chunk_result)
    else:
        # Use sequential processing for smaller datasets
        logger.info("Using sequential mutation calling")
        
        for i in range(0, total_reads, chunk_size):
            chunk = read_items[i:i+chunk_size]
            logger.info(f"Processing mutation calling chunk {i//chunk_size + 1}/{(total_reads-1)//chunk_size + 1} ({len(chunk)} reads)")
            
            for read_id, data in chunk:
                barcode = data['barcode']
                variant_seq = data['variant']
                
                # Identify mutations with pre-extracted reference
                mutations = identify_mutations_from_alignment_optimized(
                    variant_seq, ref_gene_seq, gene_region
                )
                
                barcode_variant_pairs.append({
                    'barcode': barcode,
                    'mutation': mutations,
                    'read_id': read_id,
                    'mapping_quality': data['mapping_quality']
                })
    
    logger.info(f"Completed mutation calling for {total_reads} reads")
    
    # Create DataFrame and aggregate
    df = pd.DataFrame(barcode_variant_pairs)
    
    if df.empty:
        logger.warning("No barcode-variant pairs found!")
        return pd.DataFrame(columns=['barcode', 'mutation', 'count'])
    
    # Count occurrences of each barcode-mutation pair
    barcode_counts = df.groupby(['barcode', 'mutation']).size().reset_index(name='count')
    
    # Filter by minimum coverage
    barcode_counts = barcode_counts[barcode_counts['count'] >= min_coverage]
    
    # For each barcode, keep the most frequent mutation
    barcode_mapping = barcode_counts.loc[barcode_counts.groupby('barcode')['count'].idxmax()]
    
    logger.info(f"Final barcode mapping contains {len(barcode_mapping)} unique barcodes")
    
    return barcode_mapping

def generate_mapping_statistics(barcode_mapping, all_read_data):
    """Generate statistics about the barcode mapping"""
    
    stats = []
    stats.append("=== Barcode-Variant Mapping Statistics ===")
    stats.append("")
    stats.append(f"Total reads processed: {len(all_read_data)}")
    stats.append(f"Total unique barcodes: {len(barcode_mapping)}")
    stats.append(f"Total unique mutations: {barcode_mapping['mutation'].nunique()}")
    
    # Mutation type breakdown
    wt_count = len(barcode_mapping[barcode_mapping['mutation'] == 'WT'])
    mut_count = len(barcode_mapping[barcode_mapping['mutation'] != 'WT'])
    stats.append(f"Wild-type barcodes: {wt_count}")
    stats.append(f"Mutant barcodes: {mut_count}")
    
    # Coverage statistics
    stats.append(f"Mean coverage per barcode: {barcode_mapping['count'].mean():.1f}")
    stats.append(f"Median coverage per barcode: {barcode_mapping['count'].median():.1f}")
    
    return "\n".join(stats)

if __name__ == "__main__":
    # Get parameters from Snakemake
    bam_files = snakemake.input.aligned_bams
    reference_file = snakemake.input.reference
    
    # Handle both old and new parameter names for backward compatibility
    if hasattr(snakemake.input, 'cleaned_reference'):
        cleaned_reference = snakemake.input.cleaned_reference
    elif hasattr(snakemake.input, 'index_dependency'):
        cleaned_reference = snakemake.input.index_dependency
    else:
        raise AttributeError("Neither 'cleaned_reference' nor 'index_dependency' found in snakemake.input")
    
    logger.info(f"Using cleaned reference: {cleaned_reference}")
    
    # Debug: Show available input parameters
    logger.info(f"Available snakemake.input attributes: {dir(snakemake.input)}")
    logger.info(f"snakemake.input.aligned_bams: {snakemake.input.aligned_bams}")
    logger.info(f"snakemake.input.reference: {snakemake.input.reference}")
    
    output_map = snakemake.output.barcode_map
    output_stats = snakemake.output.mapping_stats
    
    min_coverage = snakemake.params.min_coverage
    max_workers = snakemake.params.get('max_workers', None)
    
    # Create output directories
    Path(output_map).parent.mkdir(parents=True, exist_ok=True)
    Path(output_stats).parent.mkdir(parents=True, exist_ok=True)
    
    # Parse GenBank annotations - try original file first, then cleaned
    logger.info("Parsing GenBank annotations...")
    try:
        regions = parse_genbank_annotations(reference_file)
        logger.info(f"Successfully parsed reference file: {reference_file}")
    except Exception as e:
        logger.warning(f"Failed to parse original reference ({e}), trying cleaned reference...")
        try:
            regions = parse_genbank_annotations(cleaned_reference)
            logger.info(f"Successfully parsed cleaned reference: {cleaned_reference}")
        except Exception as e2:
            logger.error(f"Failed to parse both original and cleaned references.")
            logger.error(f"Original error: {e}")
            logger.error(f"Cleaned reference error: {e2}")
            
            # Last resort: check if files exist and show their content
            for file_path, name in [(reference_file, "original"), (cleaned_reference, "cleaned")]:
                logger.error(f"\nChecking {name} reference file: {file_path}")
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as f:
                            content = f.read(500)  # First 500 chars
                        logger.error(f"{name} file exists, first 500 chars: {repr(content)}")
                    else:
                        logger.error(f"{name} file does not exist!")
                except Exception as read_error:
                    logger.error(f"Cannot read {name} file: {read_error}")
            
            raise RuntimeError(f"Cannot parse any reference file. Original: {e}, Cleaned: {e2}")
    
    # Build barcode mapping
    logger.info("Building barcode→variant mapping...")
    # Use the reference that was successfully parsed for sequence data
    sequence_reference = cleaned_reference if 'reference_seq' in regions else reference_file
    barcode_mapping = build_barcode_variant_mapping(
        bam_files, sequence_reference, regions, min_coverage, max_workers
    )
    
    # Save mapping
    barcode_mapping.to_csv(output_map, index=False)
    logger.info(f"Barcode mapping saved to {output_map}")
    
    # Generate and save statistics
    stats = generate_mapping_statistics(barcode_mapping, {})
    with open(output_stats, 'w') as f:
        f.write(stats)
    logger.info(f"Mapping statistics saved to {output_stats}")
    
    logger.info("Barcode mapping complete!")
