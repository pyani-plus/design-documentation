# Example file calling snakemake scheduler from Python
# from snakemake.workflow import Workflow
from pathlib import Path
# from snakemake.api import SnakemakeApi
# from snakemake import settings
# from snakemake.workflow import Workflow
# import snakemake
from snakemake.cli import main as snakemake_main

# In a real situation, we can choose a snakefile to suit the analysis
snakefile = "example.smk"

# Define arguments to pass to the snakefile
config_args = {"outdir": "script_results"}

# Instantiate and execute the workflow
args = ["--snakefile", snakefile]
snakemake_main(args)

# workflow.execute()

# with SnakemakeApi() as snakemake_api:
#     workflow_api = snakemake_api.workflow(snakefile=snakefile,
#                                           resource_settings=settings.ResourceSettings())
#     workflow_api.execute()