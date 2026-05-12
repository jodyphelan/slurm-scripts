"""
Code to generate and monitor slurm scripts.
"""

__version__ = "0.1.0"


def generate_slurm_script(
    bash_script: str,
    job_name: str = None,
    time: str = "01:00:00",
    partition: str = "project",
    output_file: str = None,
    error_file: str = None,
) -> str:
    """
    Generate a slurm script for the given bash script.
    """
    import os

    slurm_script = f"{os.path.splitext(bash_script)[0]}.slurm"
    with open(slurm_script, "w") as f:
        f.write(f"#!/bin/bash\n")
        f.write(f"#SBATCH --job-name={job_name or os.path.splitext(bash_script)[0]}\n")
        f.write(f"#SBATCH --output={output_file or f'{os.path.splitext(bash_script)[0]}.out'}\n")
        f.write(f"#SBATCH --error={error_file or f'{os.path.splitext(bash_script)[0]}.err'}\n")
        f.write(f"#SBATCH --time={time}\n")
        f.write(f"#SBATCH --partition={partition}\n")
        f.write(f"\n")
        f.write(f"set -euo pipefail\n")
        f.write(f"\n")
        f.write(f"{bash_script}\n")
    return slurm_script

def run_slurm_script(slurm_script: str):
    """
    Run a slurm script using sbatch.
    """
    import subprocess

    result = subprocess.run(["sbatch", slurm_script], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to submit slurm script: {result.stderr}")
    print(f"Submitted slurm script: {result.stdout.strip()}")

def run_slurm_script_cli():
    """
    Command line interface to generate a slurm script.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate a slurm script.")
    parser.add_argument(
        "bash_script",
        type=str,
        help="The name of the bash script to generate a slurm script for.",
    )
    parser.add_argument(
        "--job-name",
        type=str,
        help="The name of the job.",
    )
    parser.add_argument(
        "--time",
        type=str,
        default="01:00:00",
        help="The time limit for the job (default: 01:00:00).",
    )
    parser.add_argument(
        "--partition",
        type=str,
        default="project",
        help="The partition to submit the job to (default: project).",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="The file to write the stdout output to.",
    )
    parser.add_argument(
        "--error-file", 
        type=str,
        help="The file to write the stderr output to.",
    )

    args = parser.parse_args()



    slurm_script_filename = generate_slurm_script(
        bash_script=args.bash_script,
        job_name=args.job_name,
        time=args.time,
        partition=args.partition,
        output_file=args.output_file,
        error_file=args.error_file,
    )
    
    run_slurm_script(slurm_script_filename)