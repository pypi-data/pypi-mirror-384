#!/usr/bin/env python3
"""
Variant Caller V4 - Fragment-Based Processing with Mate Merging
Features:
1. Fragment-based mutation calling (paired-end aware)
2. Mate merging with quality-based base selection for overlaps
3. VCF + mutation count table (CSV) output
4. Multi-worker processing
5. Handles name-sorted BAMs for efficient mate processing
"""

import pysam
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from Bio import SeqIO, Seq
import argparse
import logging
import os
import subprocess
from typing import Dict, List, Tuple, Set, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
from dataclasses import dataclass
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Amino acid codon table
CODON_TABLE = {
    'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
    'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
    'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
    'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
    'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
    'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
    'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
    'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
    'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
    'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
    'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
    'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
    'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
    'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
    'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
    'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G'
}

@dataclass
class MergedFragment:
    """Represents a merged paired-end fragment"""
    name: str
    sequence: str
    qualities: List[int]
    start_pos: int
    end_pos: int
    mutations: List[Tuple[int, str, str]]  # (pos, ref, alt)
    haplotype: str

class FragmentVariantCallerV4:
    """Fragment-based variant caller with mate merging"""
    
    def __init__(self, min_coverage=20, min_frequency=0.001, quality_threshold=25, 
                 max_workers=None, overlap_min_qual=30):
        self.min_coverage = min_coverage
        self.min_frequency = min_frequency
        self.quality_threshold = quality_threshold
        self.overlap_min_qual = overlap_min_qual
        
        # Performance optimization
        self.max_workers = max_workers or min(multiprocessing.cpu_count(), 16)
        
        # Data structures
        self.fragment_counts = defaultdict(int)  # haplotype -> count
        self.position_coverage = defaultdict(int)  # pos -> coverage
        self.mutation_counts = defaultdict(int)  # mutation -> count
        self.position_mutations = defaultdict(lambda: defaultdict(int))  # pos -> {(ref, alt): count}
        self.haplotype_mapping = {}  # aa_haplotype -> nucleotide_haplotype
        
        # Statistics
        self.stats = {
            'total_fragments': 0,
            'merged_fragments': 0,
            'single_end_fragments': 0,
            'overlapping_pairs': 0,
            'non_overlapping_pairs': 0
        }
        
        # Amino acid position cache
        self._aa_cache = {}
    
    def call_variants(self, bam_file: str, reference_file: str, output_prefix: str):
        """
        Main function to call variants from fragment-based processing
        
        Args:
            bam_file: Input BAM file (should be name-sorted)
            reference_file: Reference FASTA file
            output_prefix: Output file prefix (will create .vcf and .csv)
        """
        logger.info(f"Starting fragment-based variant calling from {bam_file}")
        
        # Load reference
        reference_seq = self._load_reference(reference_file)
        self.reference_seq = reference_seq  # Store for amino acid translation
        logger.info(f"Loaded reference: {len(reference_seq)} bp")
        
        # Sort and index BAM if needed
        sorted_bam = self._prepare_bam(bam_file)
        
        # Process fragments
        self._process_fragments(sorted_bam, reference_seq)
        
        # Generate outputs
        vcf_file = f"{output_prefix}.vcf"
        csv_file = f"{output_prefix}_counts.csv"
        
        self._write_vcf_output(vcf_file, reference_seq)
        self._write_mutation_counts_csv(csv_file)
        
        # Print summary
        self._print_summary()
        
        logger.info(f"Variant calling completed. Outputs: {vcf_file}, {csv_file}")
    
    def _load_reference(self, reference_file: str) -> str:
        """Load reference sequence from FASTA"""
        try:
            record = next(SeqIO.parse(reference_file, "fasta"))
            return str(record.seq).upper()
        except Exception as e:
            logger.error(f"Error loading reference: {e}")
            raise
    
    def _prepare_bam(self, bam_file: str) -> str:
        """Sort BAM by read name if not already sorted"""
        # Check if BAM is name-sorted
        try:
            with pysam.AlignmentFile(bam_file, "rb") as bam:
                header = bam.header
                if header.get('HD', {}).get('SO') == 'queryname':
                    logger.info("BAM is already name-sorted")
                    return bam_file
        except Exception as e:
            logger.warning(f"Could not check BAM sort order: {e}")
        
        # Sort BAM by name
        sorted_bam = bam_file.replace('.bam', '_namesorted.bam')
        logger.info(f"Sorting BAM by read name: {bam_file} -> {sorted_bam}")
        
        try:
            subprocess.run([
                'samtools', 'sort', '-n', '-@', str(self.max_workers),
                '-o', sorted_bam, bam_file
            ], check=True, capture_output=True, text=True)
            logger.info("BAM sorting completed")
            return sorted_bam
        except subprocess.CalledProcessError as e:
            logger.error(f"Error sorting BAM: {e.stderr}")
            logger.warning("Proceeding with original BAM file")
            return bam_file
    
    def _process_fragments(self, bam_file: str, reference_seq: str):
        """Process all fragments with multi-worker support"""
        logger.info("Processing fragments with mate merging...")
        
        # Collect read pairs
        read_pairs = self._collect_read_pairs(bam_file)
        logger.info(f"Collected {len(read_pairs)} read pairs/fragments")
        
        if len(read_pairs) == 0:
            logger.warning("No read pairs collected! Check BAM file and filtering criteria.")
            return
        
        # Process read pairs sequentially for now (simpler and more reliable)
        logger.info("Processing read pairs sequentially...")
        
        processed_count = 0
        for read_pair in read_pairs:
            try:
                fragment = self._merge_read_pair(read_pair, reference_seq)
                if fragment:
                    self._process_fragment_direct(fragment, reference_seq)
                    
                processed_count += 1
                if processed_count % 10000 == 0:
                    logger.info(f"Processed {processed_count:,}/{len(read_pairs):,} read pairs")
                    
            except Exception as e:
                logger.warning(f"Error processing read pair: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"Fragment processing completed. Total fragments: {self.stats['total_fragments']:,}")
        logger.info(f"Total mutations: {len(self.mutation_counts):,}")
        logger.info(f"Total haplotypes: {len(self.fragment_counts):,}")
    
    def _collect_read_pairs(self, bam_file: str) -> List[Tuple]:
        """Collect read pairs from name-sorted BAM"""
        read_pairs = []
        current_pair = []
        last_name = None
        total_reads = 0
        unmapped_reads = 0
        
        with pysam.AlignmentFile(bam_file, "rb") as bamfile:
            # Use bamfile directly without fetch() for name-sorted BAMs
            # fetch() requires an index, but name-sorted BAMs don't need indexing
            for read in bamfile:
                total_reads += 1
                
                if read.is_unmapped:
                    unmapped_reads += 1
                    continue
                
                # Group reads by name
                if read.query_name != last_name:
                    if current_pair:
                        read_pairs.append(tuple(current_pair))
                    current_pair = [read]
                    last_name = read.query_name
                else:
                    current_pair.append(read)
            
            # Add last pair
            if current_pair:
                read_pairs.append(tuple(current_pair))
        
        logger.info(f"BAM statistics: {total_reads:,} total reads, {unmapped_reads:,} unmapped, {total_reads - unmapped_reads:,} mapped")
        logger.info(f"Collected {len(read_pairs):,} read pairs/fragments from mapped reads")
        
        return read_pairs
    
    def _process_chunk(self, chunk: List[Tuple], reference_seq: str) -> Dict:
        """Process a chunk of read pairs"""
        chunk_results = {
            'fragment_counts': defaultdict(int),
            'position_coverage': defaultdict(int),
            'mutation_counts': defaultdict(int),
            'stats': {
                'total_fragments': 0,
                'merged_fragments': 0,
                'single_end_fragments': 0,
                'overlapping_pairs': 0,
                'non_overlapping_pairs': 0
            }
        }
        
        for read_pair in chunk:
            try:
                fragment = self._merge_read_pair(read_pair, reference_seq)
                if fragment:
                    self._process_fragment(fragment, chunk_results, reference_seq)
            except Exception as e:
                logger.warning(f"Error processing read pair: {e}")
        
        return chunk_results
    
    def _merge_read_pair(self, read_pair: Tuple, reference_seq: str) -> Optional[MergedFragment]:
        """Merge a read pair into a single fragment"""
        if len(read_pair) == 1:
            # Single-end read
            read = read_pair[0]
            return self._process_single_read(read, reference_seq)
        
        elif len(read_pair) == 2:
            # Paired-end reads
            read1, read2 = read_pair
            return self._merge_paired_reads(read1, read2, reference_seq)
        
        else:
            logger.warning(f"Unexpected number of reads in pair: {len(read_pair)}")
            return None
    
    def _process_single_read(self, read, reference_seq: str) -> Optional[MergedFragment]:
        """Process a single-end read"""
        if not read.query_sequence or not read.query_qualities:
            return None
        
        # Get mutations from single read
        mutations = self._get_mutations_from_read(read, reference_seq)
        haplotype = self._mutations_to_haplotype(mutations)
        
        return MergedFragment(
            name=read.query_name,
            sequence=read.query_sequence,
            qualities=read.query_qualities,
            start_pos=read.reference_start,
            end_pos=read.reference_end,
            mutations=mutations,
            haplotype=haplotype
        )
    
    def _merge_paired_reads(self, read1, read2, reference_seq: str) -> Optional[MergedFragment]:
        """Merge paired-end reads with quality-based overlap resolution"""
        if not (read1.query_sequence and read2.query_sequence and 
                read1.query_qualities and read2.query_qualities):
            return None
        
        # Check for overlap
        overlap_start = max(read1.reference_start, read2.reference_start)
        overlap_end = min(read1.reference_end, read2.reference_end)
        
        if overlap_start < overlap_end:
            # Overlapping reads - merge with quality-based selection
            return self._merge_overlapping_reads(read1, read2, reference_seq)
        else:
            # Non-overlapping reads - concatenate
            return self._merge_non_overlapping_reads(read1, read2, reference_seq)
    
    def _merge_overlapping_reads(self, read1, read2, reference_seq: str) -> Optional[MergedFragment]:
        """Merge overlapping paired reads using quality-based base selection"""
        try:
            # Get mutations from both reads
            mutations1 = self._get_mutations_from_read(read1, reference_seq)
            mutations2 = self._get_mutations_from_read(read2, reference_seq)
            
            # Merge mutations, preferring higher quality bases in overlap
            merged_mutations = self._merge_mutations_by_quality(
                read1, read2, mutations1, mutations2, reference_seq
            )
            
            haplotype = self._mutations_to_haplotype(merged_mutations)
            
            return MergedFragment(
                name=read1.query_name,
                sequence=f"{read1.query_sequence}+{read2.query_sequence}",  # Placeholder
                qualities=[],  # Simplified for now
                start_pos=min(read1.reference_start, read2.reference_start),
                end_pos=max(read1.reference_end, read2.reference_end),
                mutations=merged_mutations,
                haplotype=haplotype
            )
            
        except Exception as e:
            logger.warning(f"Error merging overlapping reads: {e}")
            return None
    
    def _merge_non_overlapping_reads(self, read1, read2, reference_seq: str) -> Optional[MergedFragment]:
        """Merge non-overlapping paired reads"""
        try:
            # Get mutations from both reads
            mutations1 = self._get_mutations_from_read(read1, reference_seq)
            mutations2 = self._get_mutations_from_read(read2, reference_seq)
            
            # Combine mutations
            all_mutations = mutations1 + mutations2
            all_mutations.sort(key=lambda x: x[0])  # Sort by position
            
            haplotype = self._mutations_to_haplotype(all_mutations)
            
            return MergedFragment(
                name=read1.query_name,
                sequence=f"{read1.query_sequence}+{read2.query_sequence}",  # Placeholder
                qualities=[],  # Simplified for now
                start_pos=min(read1.reference_start, read2.reference_start),
                end_pos=max(read1.reference_end, read2.reference_end),
                mutations=all_mutations,
                haplotype=haplotype
            )
            
        except Exception as e:
            logger.warning(f"Error merging non-overlapping reads: {e}")
            return None
    
    def _get_mutations_from_read(self, read, reference_seq: str) -> List[Tuple[int, str, str]]:
        """Extract mutations from a single read using CIGAR"""
        mutations = []
        
        if not read.cigartuples:
            return mutations
        
        read_pos = 0
        ref_pos = read.reference_start
        
        if ref_pos is None:
            return mutations
        
        for op, length in read.cigartuples:
            if op == 0:  # M (match/mismatch)
                for i in range(length):
                    if (ref_pos + i < len(reference_seq) and 
                        read_pos + i < len(read.query_sequence) and 
                        read_pos + i < len(read.query_qualities)):
                        
                        ref_base = reference_seq[ref_pos + i]
                        read_base = read.query_sequence[read_pos + i].upper()
                        read_qual = read.query_qualities[read_pos + i]
                        
                        # Check quality and detect mutations
                        if read_qual >= self.quality_threshold and read_base != ref_base:
                            mutations.append((ref_pos + i + 1, ref_base, read_base))  # 1-based
                
                read_pos += length
                ref_pos += length
                
            elif op == 1:  # I (insertion)
                read_pos += length
                
            elif op == 2:  # D (deletion)
                # Handle deletions
                for i in range(length):
                    if ref_pos + i < len(reference_seq):
                        ref_base = reference_seq[ref_pos + i]
                        mutations.append((ref_pos + i + 1, ref_base, 'DEL'))
                ref_pos += length
                
            elif op == 4:  # S (soft clipping)
                read_pos += length
        
        return mutations
    
    def _merge_mutations_by_quality(self, read1, read2, mutations1: List, mutations2: List, 
                                   reference_seq: str) -> List[Tuple[int, str, str]]:
        """Merge mutations from overlapping reads using quality scores"""
        merged = {}
        
        # Add mutations from read1
        for pos, ref, alt in mutations1:
            merged[pos] = (ref, alt, self._get_quality_at_position(read1, pos, reference_seq))
        
        # Add mutations from read2, preferring higher quality
        for pos, ref, alt in mutations2:
            if pos in merged:
                # Position overlap - choose higher quality
                _, _, qual1 = merged[pos]
                qual2 = self._get_quality_at_position(read2, pos, reference_seq)
                
                if qual2 > qual1:
                    merged[pos] = (ref, alt, qual2)
            else:
                merged[pos] = (ref, alt, self._get_quality_at_position(read2, pos, reference_seq))
        
        # Convert back to list format
        return [(pos, ref, alt) for pos, (ref, alt, qual) in merged.items()]
    
    def _get_quality_at_position(self, read, ref_pos: int, reference_seq: str) -> int:
        """Get quality score at a specific reference position"""
        if not read.cigartuples:
            return 0
        
        read_pos = 0
        current_ref_pos = read.reference_start
        
        for op, length in read.cigartuples:
            if op == 0:  # M (match/mismatch)
                if current_ref_pos <= ref_pos - 1 < current_ref_pos + length:
                    offset = (ref_pos - 1) - current_ref_pos
                    if read_pos + offset < len(read.query_qualities):
                        return read.query_qualities[read_pos + offset]
                read_pos += length
                current_ref_pos += length
            elif op == 1:  # I (insertion)
                read_pos += length
            elif op == 2:  # D (deletion)
                current_ref_pos += length
            elif op == 4:  # S (soft clipping)
                read_pos += length
        
        return 0
    
    def _mutations_to_haplotype(self, mutations: List[Tuple[int, str, str]]) -> str:
        """Convert mutations to haplotype string with codon-aware processing"""
        if not mutations:
            self.haplotype_mapping["WT"] = "WT"
            return "WT"
        
        # Create nucleotide haplotype
        nucleotide_mutations = []
        for pos, ref, alt in mutations:
            nuc_mutation = f"{ref}{pos}{alt}"
            nucleotide_mutations.append(nuc_mutation)
        nucleotide_mutations.sort()
        nucleotide_haplotype = "_".join(nucleotide_mutations)
        
        # Process amino acid mutations with codon awareness
        aa_mutations = self._get_codon_aware_mutations(mutations)
        
        if not aa_mutations:
            aa_haplotype = "WT"
        else:
            aa_mutations.sort()
            aa_haplotype = "_".join(aa_mutations)
        
        # Store mapping
        self.haplotype_mapping[aa_haplotype] = nucleotide_haplotype
        
        return aa_haplotype
    
    def _get_codon_aware_mutations(self, mutations: List[Tuple[int, str, str]]) -> List[str]:
        """Process mutations with codon awareness - multiple nucleotide changes in same codon = single AA change"""
        if not hasattr(self, 'reference_seq') or not self.reference_seq:
            # Fallback to individual processing if no reference
            aa_mutations = []
            for pos, ref, alt in mutations:
                aa_mutation = self._get_aa_mutation(pos, ref, alt, None)
                if aa_mutation and aa_mutation not in ["WT", "UNKNOWN"]:
                    aa_mutations.append(aa_mutation)
            return aa_mutations
        
        # Group mutations by codon
        codon_mutations = {}  # codon_start -> [(pos, ref, alt), ...]
        aa_mutations = []  # Initialize here for indels
        
        for pos, ref, alt in mutations:
            if alt in ['DEL', 'INS']:
                # Handle indels separately for now
                aa_pos = self._get_cached_aa_position(pos)
                if alt == 'DEL':
                    aa_mutations.append(f"DEL{aa_pos}")
                else:
                    aa_mutations.append(f"INS{aa_pos}")
                continue
                
            codon_start = ((pos - 1) // 3) * 3  # 0-based codon start
            if codon_start not in codon_mutations:
                codon_mutations[codon_start] = []
            codon_mutations[codon_start].append((pos, ref, alt))
        
        # Process each codon (add to existing aa_mutations list)
        for codon_start, codon_muts in codon_mutations.items():
            aa_mutation = self._process_codon_mutations(codon_start, codon_muts)
            if aa_mutation and aa_mutation not in ["WT", "UNKNOWN"]:
                aa_mutations.append(aa_mutation)
        
        return aa_mutations
    
    def _process_codon_mutations(self, codon_start: int, mutations: List[Tuple[int, str, str]]) -> str:
        """Process all mutations within a single codon"""
        try:
            # Get reference codon
            if codon_start + 3 > len(self.reference_seq):
                return "UNKNOWN"
            
            ref_codon = self.reference_seq[codon_start:codon_start + 3].upper()
            alt_codon = list(ref_codon)
            
            # Apply all mutations to this codon
            for pos, ref, alt in mutations:
                codon_pos = (pos - 1) % 3  # Position within codon (0, 1, or 2)
                alt_codon[codon_pos] = alt.upper()
            
            alt_codon_str = ''.join(alt_codon)
            
            # Translate both codons
            ref_aa = CODON_TABLE.get(ref_codon, 'X')
            alt_aa = CODON_TABLE.get(alt_codon_str, 'X')
            
            # Get amino acid position
            aa_pos = (codon_start // 3) + 1
            
            if ref_aa != alt_aa:
                return f"{ref_aa}{aa_pos}{alt_aa}"
            else:
                return f"{ref_aa}{aa_pos}="  # Synonymous
                
        except Exception as e:
            logger.debug(f"Error processing codon mutations at {codon_start}: {e}")
            return "UNKNOWN"
    
    def _get_aa_mutation(self, position: int, ref_base: str, alt_base: str, reference_seq: str = None) -> str:
        """Get amino acid mutation annotation"""
        try:
            # Get cached amino acid position
            aa_pos = self._get_cached_aa_position(position)
            
            if alt_base == 'DEL':
                return f"DEL{aa_pos}"
            elif alt_base == 'INS':
                return f"INS{aa_pos}"
            
            # For substitutions, try to get amino acid change
            if reference_seq and hasattr(self, 'reference_seq'):
                ref_aa, alt_aa = self._translate_mutation(position, ref_base, alt_base, reference_seq)
                if ref_aa and alt_aa and ref_aa != alt_aa:
                    return f"{ref_aa}{aa_pos}{alt_aa}"
                elif ref_aa == alt_aa:
                    return f"{ref_aa}{aa_pos}="  # Synonymous mutation
            
            # Fallback to nucleotide level if translation fails
            return f"{ref_base}{position}{alt_base}"
            
        except Exception as e:
            return "UNKNOWN"
    
    def _translate_mutation(self, position: int, ref_base: str, alt_base: str, reference_seq: str) -> tuple:
        """Translate a nucleotide mutation to amino acid change"""
        try:
            # Find the codon boundaries
            codon_start = ((position - 1) // 3) * 3  # 0-based codon start
            codon_pos = (position - 1) % 3  # Position within codon (0, 1, or 2)
            
            # Extract reference codon
            if codon_start + 3 <= len(reference_seq):
                ref_codon = reference_seq[codon_start:codon_start + 3].upper()
                
                # Create mutant codon
                alt_codon = list(ref_codon)
                alt_codon[codon_pos] = alt_base.upper()
                alt_codon = ''.join(alt_codon)
                
                # Translate both codons
                ref_aa = CODON_TABLE.get(ref_codon, 'X')
                alt_aa = CODON_TABLE.get(alt_codon, 'X')
                
                return ref_aa, alt_aa
            
            return None, None
            
        except Exception as e:
            logger.debug(f"Error translating mutation {ref_base}{position}{alt_base}: {e}")
            return None, None
    
    def _get_cached_aa_position(self, position: int) -> int:
        """Get amino acid position with caching"""
        if position not in self._aa_cache:
            aa_pos = (position - 1) // 3 + 1
            self._aa_cache[position] = aa_pos
        return self._aa_cache[position]
    
    def _process_fragment_direct(self, fragment: MergedFragment, reference_seq: str):
        """Process a merged fragment and update counts directly"""
        # Update fragment counts
        self.fragment_counts[fragment.haplotype] += 1
        
        # Update individual mutation counts and position-specific mutations
        if fragment.mutations:
            for pos, ref, alt in fragment.mutations:
                aa_mutation = self._get_aa_mutation(pos, ref, alt, reference_seq)
                if aa_mutation and aa_mutation != "UNKNOWN":
                    self.mutation_counts[aa_mutation] += 1
                
                # Track position-specific mutations for VCF
                self.position_mutations[pos][(ref, alt)] += 1
        else:
            # No mutations = WT
            self.mutation_counts['WT'] += 1
        
        # Update position coverage
        if fragment.start_pos is not None and fragment.end_pos is not None:
            for pos in range(fragment.start_pos + 1, fragment.end_pos + 1):
                self.position_coverage[pos] += 1
        
        # Update statistics
        self.stats['total_fragments'] += 1
    
    def _process_fragment(self, fragment: MergedFragment, chunk_results: Dict, reference_seq: str):
        """Process a merged fragment and update counts (for multiprocessing)"""
        # Update fragment counts
        chunk_results['fragment_counts'][fragment.haplotype] += 1
        
        # Update individual mutation counts
        for pos, ref, alt in fragment.mutations:
            aa_mutation = self._get_aa_mutation(pos, ref, alt)
            if aa_mutation:
                chunk_results['mutation_counts'][aa_mutation] += 1
        
        # Update position coverage
        if fragment.start_pos is not None and fragment.end_pos is not None:
            for pos in range(fragment.start_pos + 1, fragment.end_pos + 1):
                chunk_results['position_coverage'][pos] += 1
        
        # Update statistics
        chunk_results['stats']['total_fragments'] += 1
    
    def _merge_chunk_results(self, chunk_results: Dict):
        """Merge results from a processed chunk"""
        # Merge fragment counts
        for haplotype, count in chunk_results['fragment_counts'].items():
            self.fragment_counts[haplotype] += count
        
        # Merge mutation counts
        for mutation, count in chunk_results['mutation_counts'].items():
            self.mutation_counts[mutation] += count
        
        # Merge position coverage
        for pos, coverage in chunk_results['position_coverage'].items():
            self.position_coverage[pos] += coverage
        
        # Merge statistics
        for stat, value in chunk_results['stats'].items():
            self.stats[stat] += value
    
    def _write_vcf_output(self, vcf_file: str, reference_seq: str):
        """Write VCF output with proper position-specific variants"""
        logger.info(f"Writing VCF output to {vcf_file}")
        
        with open(vcf_file, 'w') as f:
            # Write VCF header
            f.write("##fileformat=VCFv4.2\n")
            f.write("##source=FragmentVariantCallerV4\n")
            f.write("##INFO=<ID=DP,Number=1,Type=Integer,Description=\"Total Depth\">\n")
            f.write("##INFO=<ID=AF,Number=1,Type=Float,Description=\"Allele Frequency\">\n")
            f.write("##INFO=<ID=AC,Number=1,Type=Integer,Description=\"Allele Count\">\n")
            f.write("##INFO=<ID=MUT,Number=1,Type=String,Description=\"Amino Acid Mutation\">\n")
            f.write("##INFO=<ID=NUCMUT,Number=1,Type=String,Description=\"Nucleotide Mutation\">\n")
            f.write("##INFO=<ID=AAPOS,Number=1,Type=Integer,Description=\"Amino Acid Position\">\n")
            f.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n")
            
            # Write position-specific mutations
            variants_written = 0
            for position in sorted(self.position_mutations.keys()):
                position_coverage = self.position_coverage.get(position, 0)
                
                if position_coverage >= self.min_coverage:
                    for (ref_base, alt_base), count in self.position_mutations[position].items():
                        frequency = count / position_coverage if position_coverage > 0 else 0
                        
                        if frequency >= self.min_frequency and alt_base != ref_base:
                            # Get amino acid annotation
                            aa_pos = self._get_cached_aa_position(position)
                            aa_mutation = self._get_aa_mutation(position, ref_base, alt_base, reference_seq)
                            nucleotide_mutation = f"{ref_base}{position}{alt_base}"
                            
                            # Handle special cases for VCF format
                            if alt_base == 'DEL':
                                # For deletions, use the reference base
                                vcf_ref = ref_base
                                vcf_alt = ref_base  # Placeholder - proper deletion format would be more complex
                            else:
                                vcf_ref = ref_base
                                vcf_alt = alt_base
                            
                            # Create INFO field with both AA and nucleotide mutations
                            info = f"DP={position_coverage};AF={frequency:.6f};AC={count};MUT={aa_mutation};NUCMUT={nucleotide_mutation};AAPOS={aa_pos}"
                            
                            # Write VCF line
                            line = f"chr1\t{position}\t.\t{vcf_ref}\t{vcf_alt}\t.\tPASS\t{info}\n"
                            f.write(line)
                            variants_written += 1
        
        logger.info(f"VCF output completed: {variants_written} variants written")
    
    def _write_mutation_counts_csv(self, csv_file: str):
        """Write mutation counts to CSV - fragment-based counting (no double counting)"""
        logger.info(f"Writing mutation counts to {csv_file}")
        
        # Use fragment_counts only - this gives the true count of each haplotype/variant
        # Each fragment is counted exactly once
        csv_data = []
        
        # Add all haplotypes/variants from fragment_counts
        for haplotype, count in self.fragment_counts.items():
            if '_' in haplotype:
                # Multi-mutation haplotype
                variant_type = 'multi_mutation_haplotype'
            elif haplotype == 'WT':
                # Wild type
                variant_type = 'wild_type'
            else:
                # Single mutation
                variant_type = 'single_mutation'
            
            # Get nucleotide level annotation from stored mapping
            nucleotide_variant = self.haplotype_mapping.get(haplotype, haplotype)
            
            csv_data.append({
                'variant': haplotype,  # Amino acid level (e.g., P71T)
                'nucleotide_variant': nucleotide_variant,  # Nucleotide level (e.g., C211A)
                'count': count,
                'type': variant_type
            })
        
        # Create DataFrame and sort
        df = pd.DataFrame(csv_data)
        if not df.empty:
            df = df.sort_values(['count'], ascending=False)
        
        # Write CSV
        df.to_csv(csv_file, index=False)
        
        # Calculate totals for verification
        total_fragments = sum(df['count'])
        single_mutations = len(df[df['type'] == 'single_mutation'])
        multi_mutations = len(df[df['type'] == 'multi_mutation_haplotype'])
        wt_count = df[df['type'] == 'wild_type']['count'].sum()
        
        logger.info(f"Mutation counts written: {len(df)} entries")
        logger.info(f"  - {single_mutations} single mutations")
        logger.info(f"  - {multi_mutations} multi-mutation haplotypes") 
        logger.info(f"  - {wt_count:,} wild-type fragments")
        logger.info(f"  - {total_fragments:,} total fragments (should match processed fragments)")
    
    def _print_summary(self):
        """Print summary of variant calling results"""
        print("\n" + "="*60)
        print("FRAGMENT-BASED VARIANT CALLING SUMMARY (V4)")
        print("="*60)
        print(f"Processing method: Fragment-based with mate merging")
        print(f"Max workers: {self.max_workers}")
        print(f"Total fragments processed: {self.stats['total_fragments']:,}")
        print(f"Merged fragments: {self.stats['merged_fragments']:,}")
        print(f"Single-end fragments: {self.stats['single_end_fragments']:,}")
        print(f"Overlapping pairs: {self.stats['overlapping_pairs']:,}")
        print(f"Non-overlapping pairs: {self.stats['non_overlapping_pairs']:,}")
        print(f"Unique haplotypes: {len(self.fragment_counts):,}")
        print(f"Individual mutations: {len(self.mutation_counts):,}")
        
        # Top haplotypes
        if self.fragment_counts:
            print(f"\nTop 10 haplotypes:")
            sorted_haplotypes = sorted(self.fragment_counts.items(), key=lambda x: x[1], reverse=True)
            for haplotype, count in sorted_haplotypes[:10]:
                print(f"  {haplotype}: {count:,}")
        
        print("="*60)

def main():
    """Main function for both command line and Snakemake usage"""
    # Check if we're running in Snakemake mode
    snakemake_mode = False
    try:
        # Check if snakemake variables are available
        if hasattr(snakemake, 'input') and hasattr(snakemake, 'output'):
            snakemake_mode = True
            logger.info("Detected Snakemake mode")
        else:
            snakemake_mode = False
            logger.info("Snakemake module found but variables not available - using command line mode")
    except NameError:
        # snakemake is not imported
        snakemake_mode = False
        logger.info("Snakemake not detected - using command line mode")
    
    if snakemake_mode:
        # Snakemake mode
        try:
            bam_file = snakemake.input.bam
            reference_file = snakemake.input.reference
            output_vcf = snakemake.output.vcf
            
            # Get parameters from snakemake
            min_coverage = snakemake.params.get('min_coverage', 20)
            min_frequency = snakemake.params.get('min_frequency', 0.001)
            quality_threshold = snakemake.params.get('quality_threshold', 25)
            max_workers = snakemake.params.get('max_workers', None)
            overlap_min_qual = snakemake.params.get('overlap_min_qual', 30)
            
            # Create output prefix from VCF path
            output_prefix = output_vcf.replace('.vcf', '')
            
            logger.info(f"Running in Snakemake mode")
            logger.info(f"BAM: {bam_file}")
            logger.info(f"Reference: {reference_file}")
            logger.info(f"Output VCF: {output_vcf}")
            
        except AttributeError as e:
            logger.error(f"Error accessing Snakemake variables: {e}")
            logger.info("Falling back to command line mode")
            snakemake_mode = False
    
    if not snakemake_mode:
        # Command line mode
        parser = argparse.ArgumentParser(description='Fragment-Based Variant Caller V4')
        parser.add_argument('bam_file', help='Input BAM file')
        parser.add_argument('reference_file', help='Reference FASTA file')
        parser.add_argument('output_prefix', help='Output file prefix')
        parser.add_argument('--min-coverage', type=int, default=20, help='Minimum coverage (default: 20)')
        parser.add_argument('--min-frequency', type=float, default=0.001, help='Minimum frequency (default: 0.001)')
        parser.add_argument('--quality-threshold', type=int, default=25, help='Quality threshold (default: 25)')
        parser.add_argument('--max-workers', type=int, default=None, help='Max workers (default: auto)')
        parser.add_argument('--overlap-min-qual', type=int, default=30, help='Min quality for overlap resolution (default: 30)')
        
        args = parser.parse_args()
        
        bam_file = args.bam_file
        reference_file = args.reference_file
        output_prefix = args.output_prefix
        min_coverage = args.min_coverage
        min_frequency = args.min_frequency
        quality_threshold = args.quality_threshold
        max_workers = args.max_workers
        overlap_min_qual = args.overlap_min_qual
        
        logger.info(f"Running in command line mode")
    
    # Create variant caller with parameters
    caller = FragmentVariantCallerV4(
        min_coverage=min_coverage,
        min_frequency=min_frequency,
        quality_threshold=quality_threshold,
        max_workers=max_workers,
        overlap_min_qual=overlap_min_qual
    )
    
    # Call variants
    caller.call_variants(bam_file, reference_file, output_prefix)
    
    # In Snakemake mode, ensure files exist
    if snakemake_mode:
        vcf_file = f"{output_prefix}.vcf"
        csv_file = f"{output_prefix}_counts.csv"
        
        for output_file in [vcf_file, csv_file]:
            if not os.path.exists(output_file):
                raise FileNotFoundError(f"Output file not created: {output_file}")
        
        logger.info(f"Output files created successfully: {vcf_file}, {csv_file}")

if __name__ == "__main__":
    main()
