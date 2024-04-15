# Example snakemake file performing pairwise comparisons
from itertools import permutations

# Pick up genome filestems
(GENOMES,) = glob_wildcards("data/{genome}.fna")
CMPS = list(permutations(GENOMES, 2))  # all pairwise comparisons fwd and reverse

# Rule `all` defines all A vs B comparisons, the `nucmer` rule runs a
# single pairwise comparison at a time
# The `zip` argument to `expand()` prevents this function generating the
# product of every member of each list. Instead we have extracted each
# participant in all pairwise comparisons into separate lists
rule all:
    input:
        expand(
            "results/{genomeA}_vs_{genomeB}.delta",
            zip,
            genomeA=[_[0] for _ in CMPS],
            genomeB=[_[1] for _ in CMPS],
            # outdir=OUTDIR,
        ),


# The nucmer rule runs nucmer in the forward direction only
rule nucmer:
    output:
        "{outdir}/{genomeA}_vs_{genomeB}.delta",
    run:
        shell(
            "nucmer data/{wildcards.genomeA}.fna data/{wildcards.genomeB}.fna -p {wildcards.outdir}/{wildcards.genomeA}_vs_{wildcards.genomeB} --maxmatch"
        )
