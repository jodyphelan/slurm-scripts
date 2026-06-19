"""
Code to generate and monitor slurm scripts.
"""

__version__ = "0.1.0"


import json
import logging
from uuid import uuid4

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)


def generate_teams_message_card(content: str):
    teams_message_card_template = json.load(open("card-template.json"))
    teams_message_card_template['body'][0]['items'][0]['text'] = content
    return teams_message_card_template

def get_slack_pings_file() -> str:
    import os
    slack_pings_file = os.path.expanduser("~/.slack-pings")
    if os.path.exists(slack_pings_file):
        return slack_pings_file
    return None

def command_to_bash_script(command: str, bash_script: str = None) -> str:
    """
    Create an executable bash script that runs the given command.
    """
    import os
    import stat

    uuid = uuid4()
    if bash_script is None:
        # write to ~/.slurm-scripts/{uuid}.sh
        bash_script = os.path.expanduser(f"~/.slurm-scripts/{uuid}.sh")
        os.makedirs(os.path.dirname(bash_script), exist_ok=True)

    with open(bash_script, "w", encoding="utf-8") as f:
        f.write("#! /bin/bash\n")
        f.write(f"{command}\n")
        slack_pings_file = get_slack_pings_file()
        if slack_pings_file is not None:
            f.write(f"ping-slack '{command} ({uuid})'\n")

    current_mode = os.stat(bash_script).st_mode
    os.chmod(
        bash_script,
        current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
    )
    return bash_script


def script_file(filename: str) -> bool:
    """
    Check if a file exists.
    """
    import os
    
    checks_pass = True
    if not os.path.exists(filename):
        # print red circle emoji and error message
        logging.error(f"🔴 File {filename} does not exist")
        checks_pass = False
    else:
        logging.info(f"🟢 File {filename} exists")

    with open(filename, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()
    if first_line not in ("#!/bin/bash", "#! /bin/bash"):
        logging.error(f"🔴 File {filename} does not start with '#!/bin/bash' or '#! /bin/bash'")
        checks_pass = False
    else:
        logging.info(f"🟢 File {filename} has a valid bash shebang")

    # if the file is not executable, raise an error    if not os.access(filename, os.X_OK):
    if not os.access(filename, os.X_OK):
        logging.error(f"🔴 File {filename} is not executable")
        checks_pass = False
    else:
        logging.info(f"🟢 File {filename} is executable")

    if checks_pass:
        return filename
    else:
        logging.error(f"One or more checks failed for file {filename}. Please fix the issues and try again.")
        quit(1)

def generate_slurm_script(
    bash_script: str,
    job_name: str = None,
    time: str = "01:00:00",
    partition: str = "project",
    output_file: str = None,
    error_file: str = None,
    cpus_per_task: int = 4,
    max_ram: str = "15G",
    logs_dir: str = "logs",
) -> str:
    """
    Generate a slurm script for the given bash script.
    """
    import os

    slurm_script = f"{os.path.splitext(bash_script)[0]}.slurm"
    os.makedirs(logs_dir, exist_ok=True)
    base_name = os.path.splitext(bash_script)[0]

    with open(slurm_script, "w") as f:
        f.write(f"#!/bin/bash\n")
        f.write(f"#SBATCH --job-name={job_name or base_name}\n")
        f.write(f"#SBATCH --output={output_file or os.path.join(logs_dir, f'{base_name}.out')}\n")
        f.write(f"#SBATCH --error={error_file or os.path.join(logs_dir, f'{base_name}.err')}\n")
        f.write(f"#SBATCH --time={time}\n")
        f.write(f"#SBATCH --partition={partition}\n")
        if cpus_per_task is not None:
            f.write(f"#SBATCH --cpus-per-task={cpus_per_task}\n")
        if max_ram is not None:
            f.write(f"#SBATCH --mem={max_ram}\n")
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
    logging.info(f"Submitted slurm script: {result.stdout.strip()}")


def generate_slurm_array_script(
    bash_script: str,
    array_argument_file: str,
    concurrent_jobs: int,
    job_name: str = None,
    time: str = "01:00:00",
    partition: str = "project",
    cpus_per_task: int = 4,
    max_ram: str = "15G",
    logs_dir: str = "logs",
) -> str:
    """
    Generate a slurm array script for the given bash script and array arguments.
    """
    import os

    slurm_script = f"{os.path.splitext(bash_script)[0]}_array.slurm"
    array_arguments = [l.strip() for l in open(array_argument_file, "r")]
    os.makedirs(logs_dir, exist_ok=True)
    base_name = os.path.splitext(bash_script)[0]

    with open(slurm_script, "w") as f:
        f.write(f"#!/bin/bash\n")
        f.write(f"#SBATCH --job-name={job_name or base_name}\n")
        f.write(f"#SBATCH --output={os.path.join(logs_dir, f'{job_name or base_name}_%A_%a.out')}\n")
        f.write(f"#SBATCH --error={os.path.join(logs_dir, f'{job_name or base_name}_%A_%a.err')}\n")
        f.write(f"#SBATCH --time={time}\n")
        f.write(f"#SBATCH --partition={partition}\n")
        if cpus_per_task is not None:
            f.write(f"#SBATCH --cpus-per-task={cpus_per_task}\n")
        if max_ram is not None:
            f.write(f"#SBATCH --mem={max_ram}\n")
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
    parser.add_argument(
        "--cpus-per-task",
        type=int,
        help="Maximum number of CPU cores per task.",
    )
    parser.add_argument(
        "--max-ram",
        type=str,
        help="Maximum RAM for the job, for example 16G or 8000M.",
    )
    parser.add_argument(
        "--logs-dir",
        type=str,
        default="logs",
        help="Directory to write stdout/stderr logs (default: logs).",
    )

    args = parser.parse_args()



    slurm_script_filename = generate_slurm_script(
        bash_script=args.bash_script,
        job_name=args.job_name,
        time=args.time,
        partition=args.partition,
        output_file=args.output_file,
        error_file=args.error_file,
        cpus_per_task=args.cpus_per_task,
        max_ram=args.max_ram,
        logs_dir=args.logs_dir,
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
    parser.add_argument(
        "--cpus-per-task",
        type=int,
        default=4,
        help="Maximum number of CPU cores per task (default: 4).",
    )
    parser.add_argument(
        "--max-ram",
        type=str,
        default="15G",
        help="Maximum RAM for the job, for example 16G or 8000M (default: 15G).",
    )
    parser.add_argument(
        "--logs-dir",
        type=str,
        default="logs",
        help="Directory to write stdout/stderr logs (default: logs).",
    )

    args = parser.parse_args()

    slurm_script_filename = generate_slurm_array_script(
        bash_script=args.bash_script,
        array_argument_file=args.array_argument_file,
        concurrent_jobs=args.concurrent_jobs,
        job_name=args.job_name,
        time=args.time,
        partition=args.partition,
        cpus_per_task=args.cpus_per_task,
        max_ram=args.max_ram,
        logs_dir=args.logs_dir,
    )

    run_slurm_script(slurm_script_filename)


def cli_run_command_to_slurm_job():
    """
    Command line interface to run a shell command as a slurm job.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Create a bash script from a command and submit it as a slurm job."
    )
    parser.add_argument(
        "command",
        type=str,
        help="The shell command to run.",
    )
    parser.add_argument(
        "--bash-script",
        type=str,
        help="Name of the generated bash script.",
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
    parser.add_argument(
        "--cpus-per-task",
        type=int,
        default=4,
        help="Maximum number of CPU cores per task (default: 4).",
    )
    parser.add_argument(
        "--max-ram",
        type=str,
        default="15G",
        help="Maximum RAM for the job, for example 16G or 8000M (default: 15G).",
    )
    parser.add_argument(
        "--logs-dir",
        type=str,
        default="logs",
        help="Directory to write stdout/stderr logs (default: logs).",
    )

    args = parser.parse_args()

    bash_script = command_to_bash_script(
        command=args.command,
        bash_script=args.bash_script,
    )
    logging.info(f"Generated bash script: {bash_script}")

    slurm_script_filename = generate_slurm_script(
        bash_script=bash_script,
        job_name=args.job_name,
        time=args.time,
        partition=args.partition,
        output_file=args.output_file,
        error_file=args.error_file,
        cpus_per_task=args.cpus_per_task,
        max_ram=args.max_ram,
        logs_dir=args.logs_dir,
    )
    logging.info(f"Generated slurm script: {slurm_script_filename}")
    run_slurm_script(slurm_script_filename)