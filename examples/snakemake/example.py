# Example file calling snakemake scheduler from Python
# Documentation is implicit, at https://github.com/snakemake/snakemake/blob/04ec2c0262b2cb96cbcd7edbbb2596979c1703ae/snakemake/cli.py#L1767

from pathlib import Path
from snakemake.api import SnakemakeApi, _get_executor_plugin_registry
from snakemake.settings import ConfigSettings, DAGSettings, ResourceSettings

# In a real situation, we can choose a snakefile to suit the analysis
snakefile = Path("example.smk")

# Define arguments to pass to the snakefile
# config_args = {"outdir": "script_results"}

# Define a subset of target files to generate
target_files = ["script_results/genome_2_vs_genome_3.delta",
                "script_results/genome_4_vs_genome_3.delta"]

# Use the defined workflow from the Python API
with SnakemakeApi() as snakemake_api:
    workflow_api = snakemake_api.workflow(snakefile=snakefile,
                                          resource_settings=ResourceSettings(cores=8),
                                          config_settings=ConfigSettings(
                                              config=config_args,
                                              )
                                          )
    dag_api = workflow_api.dag(
        dag_settings = DAGSettings(
            targets=target_files,  
        )
    )
    dag_api.execute_workflow()
