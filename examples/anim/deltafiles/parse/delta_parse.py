#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) The University of Strathclyde 2024
# Author: Angelika B Kiepas
#
# Contact:
# angelika.kiepas@strath.ac.uk
#
# Angelika Kiepas,
# Strathclyde Institute of Pharmacy and Biomedical Sciences
# University of Strathclyde
# 161 Cathedral Street
# Glasgow
# Scotland,
# G4 0RE
# UK
#
# The MIT License
#
# Copyright (c) 2024 The University of Strathclyde
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


""" This script was written to sketch out a Python function that will
take a .delta file, and calculate the total number of aligned bases and 
%ID for a given pairwise comparision. 
"""

#Set Up
from pathlib import Path
from collections import defaultdict
import intervaltree
from typing import Tuple


def parse_delta(filename: Path) -> Tuple[int, int, float]:

    """Return (reference alignment length, query alignment length, average identity)

    :param filename: Path to the input .delta file

    Calculates the aligned lengths for reference and query and average nucleotide
    identity, and returns the cumulative total for each as a tuple.

    The delta file format contains seven numbers in the lines of interest:
    see http://mummer.sourceforge.net/manual/ for specification

    - start on query
    - end on query
    - start on target
    - end on target
    - error count (non-identical, plus indels)
    - similarity errors (non-positive match scores)
        [NOTE: with PROmer this is equal to error count]
    - stop codons (always zero for nucmer)

    We report ANIm identity by finding an average across all alignments using 
    the following formula:

    sum of weighted identical bases / sum of aligned bases from each fragment

    For example:

    reference.fasta query.fasta
    NUCMER
    >ref_seq_A ref_seq_B 40 40
    1 10 1 11 5 5 0
    -1
    0
    15 20 25 30 0 0 0

    The delta file tells us there are two alignments. The first alignment runs from base 1 
    to base 10 in the reference sequence, and from base 1 to 11 in the query sequence
    with a similarity error of 5. The second alignment runs from base 15 to 20 in
    the reference, and base 25 to 30 in the query with 0 similarity errors. To calculate
    the %ID, we can:

    - Find the number of all aligned bases from each sequence:
    aligned reference bases region 1 = 10 - 1 + 1 = 10
    aligned query bases region 1 = 11 - 1 + 1 = 11
    aligned reference bases region 2 = 20 - 15 + 1 = 6
    aligned query bases region 2 = 30 - 25 + 1 = 6

    - Find weighted identical bases
    alignment 1 identity weighted = (10 + 11) - (2 * 5) = 11
    alignment 2 identity weighted = (6 + 6) - (2 * 0) = 12

    - Calculate %ID
    (11 + 12) / (10 + 11 + 6 + 6) = 0.696969696969697

    To calculate alignment lengths, we extract the regions of each alignment 
    (either for query or reference) provided in the .delta file and merge the overlapping 
    regions with IntervalTree. Then, we calculate the total sum of all aligned regions.
    """




    current_ref, current_qry, raln_length, qaln_length, avrg_ID = None, None, 0, 0, 0.0

    regions_ref = defaultdict(list)  # Hold a dictionary for query regions
    regions_qry = defaultdict(list)  # Hold a dictionary for query regions

    aligned_bases = [] # Hold a list for aligned bases for each sequence
    weighted_identical_bases = [] # Hold a list for weighted identical bases



    for line in [_.strip().split() for _ in filename.open("r").readlines()]:
        if line[0] == "NUCMER":  # Skip headers
            continue
        # Lines starting with ">" indicate which sequences are aligned
        if line[0].startswith(">"):
            current_ref = line[0].strip(">")
            current_qry = line[1]
        # Lines with seven columns are alignment region headers:
        if len(line) == 7:
            # Obtaining aligned regions needed to check for overlaps
            regions_ref[current_ref].append(
                tuple(sorted(list([int(line[0]), int(line[1])])))
            )  # aligned regions reference
            regions_qry[current_qry].append(
                tuple(sorted(list([int(line[2]), int(line[3])])))
            )  # aligned regions qry

            # Calculate aligned bases for each sequence
            ref_aln_lengths = int(line[1])  - int(line[0]) + 1
            qry_aln_lengths = int(line[3])  - int(line[2]) + 1
            aligned_bases.append(ref_aln_lengths)
            aligned_bases.append(qry_aln_lengths)

            # Calculate weighted identical bases
            weighted_identical_bases.append((ref_aln_lengths+qry_aln_lengths)-(2*int(line[4])))



    #Calculate average %ID
    avrg_ID = sum(weighted_identical_bases)/sum(aligned_bases)


    #Calculate total aligned bases (no overlaps)
    for seq_id in regions_qry:
        qry_tree = intervaltree.IntervalTree.from_tuples(regions_qry[seq_id])
        qry_tree.merge_overlaps(strict=False)
        for interval in qry_tree:
            qaln_length += interval.end - interval.begin + 1

    for seq_id in regions_ref:
        ref_tree = intervaltree.IntervalTree.from_tuples(regions_ref[seq_id])
        ref_tree.merge_overlaps(strict=False)
        for interval in ref_tree:
            raln_length += interval.end - interval.begin + 1


    return (raln_length, qaln_length, avrg_ID)

                


print(parse_delta(Path("../tests/fixtures/high_align_cov/out.mdelta")))