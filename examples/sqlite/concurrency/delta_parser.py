#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) The University of Strathclyde 2024
# Author: Leighton Pritchard
#
# Contact:
# leighton.pritchard@strath.ac.uk
#
# Leighton Pritchard,
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
"""Module for parsing MUMmer .delta files"""

import logging

from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple

import click
import intervaltree  # type: ignore

from rich.logging import RichHandler

# Set up logging format
FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)


# Parse NUCmer delta file to get total alignment length and total sim_errors
def parse_deltafile(filename: Path) -> Tuple[int, int, int, int]:
    """Return (query alignment length, reference alignment length,
    total alignment length, similarity errors) tuple from passed .delta file.

    :param filename:  Path, path to the input .delta file

    Extracts the query and reference alignment legnths, and number of similarity errors for each matched region, and returns the cumulative total for
    each as a tuple, along with a total alignment length.

    Similarity errors are defined in the .delta file spec (see below) as
    non-positive match scores. For NUCmer output, this is identical to the
    number of errors (the sum of non-identities and indels).

    Delta file format has seven numbers in the lines of interest:
    see http://mummer.sourceforge.net/manual/ for specification

    - start on query
    - end on query
    - start on target
    - end on target
    - error count (non-identical, plus indels)
    - similarity errors (non-positive match scores)
        [NOTE: with PROmer this is equal to error count]
    - stop codons (always zero for nucmer)

    To calculate alignment length, we take the length of the aligned region of
    the reference (no gaps), and process the delta information. This takes the
    form of one value per line, following the header sequence. Positive values
    indicate an insertion in the reference; negative values a deletion in the
    reference (i.e. an insertion in the query). The total length of the alignment
    is then:

    reference_length + insertions - deletions

    For example:

    A = ABCDACBDCAC$
    B = BCCDACDCAC$
    Delta = (1, -3, 4, 0)
    A = ABC.DACBDCAC$
    B = .BCCDAC.DCAC$

    A is the reference and has length 11. There are two insertions (positive delta),
    and one deletion (negative delta). Alignment length is then 11 + 1 = 12.
    """
    logger = logging.getLogger()

    in_aln, qaln_length, raln_length, tot_aln_length, sim_errors = False, 0, 0, 0, 0

    with filename.open("r") as ifh:
        for line in [_.strip().split() for _ in ifh.readlines()]:
            # Skip headers
            if line[0] == "NUCMER" or line[0].startswith(">"):
                continue

            # Lines with seven columns are alignment region headers:
            if len(line) == 7:
                in_aln = True  # we're currently processing an alignment
                logger.debug("Match data: %s" % line)

                # Set query, reference alignment lengths, sim_errors
                qaln_length += abs(int(line[1]) - int(line[0])) + 1
                raln_length += abs(int(line[3]) - int(line[2])) + 1
                sim_errors += int(line[4])  # count of non-identities and indels

                # Total alignment length starts as query alignment length
                tot_aln_length += abs(int(line[1]) - int(line[0])) + 1

            # Lines with a single column (following a header) report numbers of
            # symbols until next insertion (+ve) or deletion (-ve) in the reference;
            # one line per insertion/deletion; the alignment always ends with 0
            if in_aln and line[0].startswith("0"):  # alignment stop
                in_aln = False
            elif in_aln and int(line[0]) < 0:
                # Add one to the total alignment length for each query sequence
                # insertion (negative integer)
                # NOTE: This should agree with an approach where the reference
                #       sequence length is used to start tot_aln_length, and we
                #       increment for each query sequence insertion
                tot_aln_length += 1

    return qaln_length, raln_length, tot_aln_length, sim_errors


def intervalparse_deltafile(filename: Path) -> Tuple[int, int, int]:
    """Return (alignment length, similarity errors) tuple from passed .delta.

    :param filename:  Path, path to the input .delta file

    Extracts the query and reference alignment legnths, and number of similarity errors for each matched region, and returns the cumulative total for
    each as a tuple.

    Similarity errors are defined in the .delta file spec (see below) as
    non-positive match scores. For NUCmer output, this is identical to the
    number of errors (non-identities and indels).

    Delta file format has seven numbers in the lines of interest:
    see http://mummer.sourceforge.net/manual/ for specification

    - start on query
    - end on query
    - start on target
    - end on target
    - error count (non-identical, plus indels)
    - similarity errors (non-positive match scores)
        [NOTE: with PROmer this is equal to error count]
    - stop codons (always zero for nucmer)

    To calculate alignment length, we maintain a dictionary of aligned region lengths for both the reference and query sequences.
    """
    logger = logging.getLogger()

    current_ref, current_qry, tot_aln_length, sim_errors, in_aln = (
        None,
        None,
        0,
        0,
        False,
    )

    # Define dictionaries to hold query/reference interval regions
    regions_ref = defaultdict(list)
    regions_qry = defaultdict(list)

    for line in [_.strip().split() for _ in filename.open("r").readlines()]:
        # Skip headers
        if line[0] == "NUCMER":
            continue

        # Lines starting with ">" indicate which sequences are aligned
        # Capture the reference and query names
        if line[0].startswith(">"):
            current_ref = line[0].strip(">")
            current_qry = line[1]

        # Lines with seven columns are alignment region headers.
        # Use the query and reference start/end information to create the
        # corresponding interval and populate the corresponding dictionary with them
        if len(line) == 7:
            in_aln = True
            regions_ref[current_ref].append(
                tuple(sorted([int(line[0]), int(line[1])]))
            )  # aligned regions reference
            regions_qry[current_qry].append(
                tuple(sorted([int(line[2]), int(line[3])]))
            )  # aligned regions qry

            # Total alignment length starts as query alignment length
            tot_aln_length += abs(int(line[1]) - int(line[0])) + 1
            sim_errors += int(line[4])  # count of non-identities and indels

        # Lines with a single column (following a header) report numbers of
        # symbols until next insertion (+ve) or deletion (-ve) in the reference;
        # one line per insertion/deletion; the alignment always ends with 0
        if in_aln and line[0].startswith("0"):  # alignment stop
            in_aln = False
        elif in_aln and int(line[0]) < 0:
            # Add one to the total alignment length for each query sequence
            # insertion (negative integer)
            # NOTE: This should agree with an approach where the reference
            #       sequence length is used to start tot_aln_length, and we
            #       increment for each query sequence insertion
            tot_aln_length += 1

    return (
        get_merged_interval_length(regions_qry),
        get_merged_interval_length(regions_ref),
        tot_aln_length,
        sim_errors,
    )


def get_merged_interval_length(intervaldict: Dict) -> int:
    """Return total length of merged intervals"""
    logger = logging.getLogger()

    tot_length = 0

    for key, regions in intervaldict.items():
        logger.debug("Key: %s, len(regions): %d" % (key, len(regions)))
        tree = intervaltree.IntervalTree.from_tuples(regions)
        tree.merge_overlaps(strict=False)
        for interval in tree:
            tot_length += interval.end - interval.begin + 1

    return tot_length


@click.command()
@click.argument("path")
@click.option(
    "--intervals", default=False, is_flag=True, help="Use IntervalTree parser"
)
def parse_delta(path: str, intervals: bool):
    """Parse a .delta file and report a summary"""
    logger = logging.getLogger()

    deltapath = Path(path)
    logger.info("Attempting to parse .delta file: %s" % deltapath)

    if intervals:
        func = intervalparse_deltafile
    else:
        func = parse_deltafile
    logger.info("Using parser function: %s" % func)
    logger.info("Parser output: %s" % str(func(deltapath)))


# Make .delta file parsing available at CLI
if __name__ == "__main__":
    parse_delta()
