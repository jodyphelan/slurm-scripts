"""
Code to generate and monitor slurm scripts.
"""

__version__ = "0.1.0"

def script_file(filename: str) -> bool:
    """
    Check if a file exists.
    """
    import os
    
    checks_pass = True
    if not os.path.exists(filename):
        # print red circle emoji and error message
        print(f"🔴 File {filename} does not exist")
        checks_pass = False
    else:
        print(f"🟢 File {filename} exists")

    # if the file is not executable, raise an error    if not os.access(filename, os.X_OK):
    if not os.access(filename, os.X_OK):
        print(f"🔴 File {filename} is not executable")
        checks_pass = False
    else:
        print(f"🟢 File {filename} is executable")

    if checks_pass:
        return filename
    else:
        print(f"One or more checks failed for file {filename}. Please fix the issues and try again.")
        quit(1)

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
        f.write(f"srun {bash_script}\n")
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


def generate_slurm_array_script(
    bash_script: str,
    array_argument_file: str,
    concurrent_jobs: int,
    job_name: str = None,
    time: str = "01:00:00",
    partition: str = "project",
) -> str:
    """
    Generate a slurm array script for the given bash script and array arguments.
    """
    import os

    slurm_script = f"{os.path.splitext(bash_script)[0]}_array.slurm"
    array_arguments = [l.strip() for l in open(array_argument_file, "r")]

    with open(slurm_script, "w") as f:
        f.write(f"#!/bin/bash\n")
        f.write(f"#SBATCH --job-name={job_name or os.path.splitext(bash_script)[0]}\n")
        f.write(f"#SBATCH --output={os.path.splitext(bash_script)[0]}_%A_%a.out\n")
        f.write(f"#SBATCH --error={os.path.splitext(bash_script)[0]}_%A_%a.err\n")
        f.write(f"#SBATCH --time={time}\n")
        f.write(f"#SBATCH --partition={partition}\n")
        f.write(f"#SBATCH --array=1-{len(array_arguments)}%{concurrent_jobs}\n")
        f.write(f"\n")
        f.write(f"set -euo pipefail\n")
        f.write(f"\n")
        f.write(f"ARGUMENT=$(sed -n \"${{SLURM_ARRAY_TASK_ID}}p\" {array_argument_file})\n")
        f.write(f"srun {bash_script} $ARGUMENT\n")
    return slurm_script



def cli_run_slurm_script():
    """
    Command line interface to generate a slurm script.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate a slurm script.")
    parser.add_argument(
        "bash_script",
        type=script_file,
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
        default="08:00:00",
        help="The time limit for the job (default: 08:00:00).",
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



def cli_run_slurm_array():
    """
    Command line interface to generate a slurm array script.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate a slurm array script.")
    parser.add_argument(
        "bash_script",
        type=script_file,
        help="The name of the bash script to generate a slurm array script for.",
    )
    parser.add_argument(
        "array_argument_file",
        type=str,
        help="The file containing the arguments for the array jobs, one line for each job in the array.",
    )
    parser.add_argument(
        "concurrent_jobs",
        type=int,
        help="The number of concurrent jobs to run in the array.",
    )

    parser.add_argument(
        "--job-name",
        type=str,
        help="The name of the job.",
    )
    parser.add_argument(
        "--time",
        type=str,
        default="08:00:00",
        help="The time limit for the job (default: 08:00:00).",
    )
    parser.add_argument(
        "--partition",
        type=str,
        default="project",
        help="The partition to submit the job to (default: project).",
    )

    args = parser.parse_args()

    with open(args.array_argument_file, "r") as f:
        array_arguments = [line.strip() for line in f if line.strip()]

    slurm_script_filename = generate_slurm_array_script(
        bash_script=args.bash_script,
        array_arguments=array_arguments,
        concurrent_jobs=args.concurrent_jobs,
        job_name=args.job_name,
        time=args.time,
        partition=args.partition,
    )

    # run_slurm_script(slurm_script_filename)