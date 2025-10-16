import re
import subprocess
from pathlib import Path


def submit_job(
    command: str, log_dir: Path, time: str = "240:00:00", mem_per_cpu: str = "2000"
) -> str | None:
    if log_dir.exists():
        print(f"Log directory {log_dir} already exists. Skipping.")
        return
    cmd = " ".join(
        [
            "sbatch",
            f"-J {log_dir}",
            f"-o {log_dir / 'output.out'}",
            f"-e {log_dir / 'error.err'}",
            f"--time {time}",
            f"--mem-per-cpu={mem_per_cpu}",
            f"--wrap='{command}'",
        ]
    )
    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    job_id = re.search(r"Submitted batch job (\d+)", output.stdout)
    if job_id is None:
        raise RuntimeError(
            f"Failed to submit job.\n"
            f"Command: {cmd}\n"
            f"Output: {output.stdout}\n"
            f"Error: {output.stderr}"
        )
    return job_id.group(1)


def get_job_metadata(job_id: str):
    output = subprocess.run(
        f"myjobs -j {job_id}", shell=True, capture_output=True, text=True
    ).stdout

    status = re.search(r"Status\s+:\s+(\w+)", output)
    if status is None:
        raise ValueError(f"Failed to get job status for job {job_id}")
    status = status.group(1)

    wall_clock = re.search(r"Wall-clock\s+:\s+([\d\-:]+)", output)
    if wall_clock is None:
        raise ValueError(f"Failed to get wall-clock time for job {job_id}")
    wall_clock = wall_clock.group(1)

    if "-" in wall_clock:
        days, wall_clock = wall_clock.split("-")
        days = int(days)
    else:
        days = 0
    hours, minutes, seconds = map(int, wall_clock.split(":"))
    total_hours = days * 24 + hours + minutes / 60 + seconds / 3600

    return {"status": status, "total_hours": total_hours}
