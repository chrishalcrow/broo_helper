from datetime import datetime, timezone
from pathlib import Path
import subprocess


def format_hours(total_hours):
    days = int(total_hours // 24)
    remaining_hours = int(total_hours % 24)
    minutes = round((total_hours * 60) % 60)

    # Handle overflow if minutes round up to 60
    if minutes == 60:
        minutes = 0
        remaining_hours += 1
        if remaining_hours == 24:
            remaining_hours = 0
            days += 1

    return f"{days}-{remaining_hours:02d}:{minutes:02d}"


def make_and_run_python_script(
    job_name,
    script_path,
    cores=1,
    mem=8,
    gpu=False,
    gpu_queue=False,
    hours=1,
    email="c.halcrow@ucl.ac.uk",
    run=True,
):

    current_datetime = datetime.now(timezone.utc)
    datetime_string = f"{current_datetime:%Y%m%dT%H%M%SZ}"

    if gpu:
        gpu_string="#SBATCH --gres=gpu:1\n"
    else:
        gpu_string=""

    cpu_or_gpu = "gpu" if (gpu_queue or gpu) else "cpu"

    time_string = format_hours(hours)

    current_dir = Path.cwd()
    (current_dir / "logs").mkdir(exist_ok=True)
    (current_dir / "hpc_scripts").mkdir(exist_ok=True)

    script_text = f"""#!/bin/bash \n
#SBATCH -J {job_name}
#SBATCH -p {cpu_or_gpu}
{gpu_string}#SBATCH -N 1
#SBATCH --mem {mem}G
#SBATCH --mail-user {email}
#SBATCH --mail-type END,FAIL
#SBATCH -n {cores}
#SBATCH -t {time_string}
#SBATCH -o logs/{job_name}_{datetime_string}.out
#SBATCH -e logs/{job_name}_{datetime_string}.err \n
module load uv

ulimit -n 4096

cd {current_dir!s}
uv run {script_path}"""

    script_filename = f"hpc_scripts/{job_name}_{datetime_string}.sh"

    # 'w' mode creates a new file or overwrites an existing file
    with open(script_filename, "w", encoding="utf-8") as file:
        file.write(script_text)

    if run:
        command_to_run = ["sbatch", script_filename]
        subprocess.run(command_to_run, check=True)
