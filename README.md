# slurm-scripts

Small CLI tools to submit regular and array Slurm jobs from existing bash scripts.

## What this provides

This package installs two commands:

- `sh2sjob`: submit one bash script as a single Slurm job.
- `sh2sarray`: submit one bash script as a Slurm job array using one argument per line from an input file.

Both commands:

- validate that the target script exists and is executable
- generate a `.slurm` file next to your script
- submit it with `sbatch`

## Requirements

- Python 3.9+
- A working Slurm environment (`sbatch` and `srun` available in `PATH`)
- Your target shell script must be executable

Make a script executable with:

```bash
chmod +x my_script.sh
```

## Installation

Install from this repository:

```bash
pip install .
```

If you are developing locally:

```bash
pip install -e .
```

## Usage

### Submit a single job

```bash
sh2sjob my_script.sh
```

Optional arguments:

- `--job-name <name>`
- `--time <HH:MM:SS>` (default in CLI: `08:00:00`)
- `--partition <name>` (default: `project`)
- `--cpus-per-task <int>` (max CPU cores per task)
- `--output-file <path>`
- `--error-file <path>`

Example:

```bash
sh2sjob my_script.sh \
	--job-name preprocess \
	--time 02:00:00 \
	--cpus-per-task 8 \
	--partition short \
	--output-file logs/preprocess.out \
	--error-file logs/preprocess.err
```

### Submit an array job

Create an argument file where each line is one argument set for one task:

```text
sample_001
sample_002
sample_003
```

Run:

```bash
sh2sarray my_script.sh args.txt 10
```

Where:

- `my_script.sh` is the executable bash script
- `args.txt` contains one argument line per array task
- `10` is max concurrent array tasks

Optional arguments:

- `--job-name <name>`
- `--time <HH:MM:SS>` (default in CLI: `08:00:00`)
- `--partition <name>` (default: `project`)
- `--cpus-per-task <int>` (max CPU cores per task)

Example:

```bash
sh2sarray my_script.sh args.txt 20 \
	--job-name batch_eval \
	--time 04:00:00 \
	--cpus-per-task 4 \
	--partition compute
```

## Generated Slurm scripts

The tools generate Slurm files in the current directory:

- single job: `<script_basename>.slurm`
- array job: `<script_basename>_array.slurm`

The generated script includes:

- `#!/bin/bash`
- `set -euo pipefail`
- `#SBATCH` headers for job name, output/error, time, partition
- `#SBATCH --array=...` for array mode
- `srun ...` command to run your target script

## Notes

- `sh2sjob` defaults output/error files to `<script>.out` and `<script>.err` unless you override them.
- `sh2sarray` writes output/error as `<script>_%A_%a.out` and `<script>_%A_%a.err`.
- For array mode, each task reads its line from the argument file based on `SLURM_ARRAY_TASK_ID`.

## Troubleshooting

- If you see "file does not exist", check the path you passed to the command.
- If you see "file is not executable", run `chmod +x your_script.sh`.
- If submission fails, verify Slurm is available by running `sbatch --version`.
