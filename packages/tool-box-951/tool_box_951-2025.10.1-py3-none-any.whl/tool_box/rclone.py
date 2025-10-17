# coding:utf-8
import os
import re
import json
import shlex
import subprocess
from loguru import logger


def parse_time_to_seconds(s: str) -> int:
    """
    将类似 '1h', '30min', '1d', '45s', '2w' 转换为秒数
    支持单位: s, sec, m, min, h, hour, d, day, w, week
    """
    if not s:
        raise ValueError("Empty time string")
    s = s.strip().lower()
    if s.isnumeric():
        return int(s)
    units = {
        "s": 1,
        "sec": 1,
        "secs": 1,
        "second": 1,
        "seconds": 1,
        "m": 60,
        "min": 60,
        "mins": 60,
        "minute": 60,
        "minutes": 60,
        "h": 3600,
        "hr": 3600,
        "hour": 3600,
        "hours": 3600,
        "d": 86400,
        "day": 86400,
        "days": 86400,
        "w": 604800,
        "week": 604800,
        "weeks": 604800,
    }
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*([a-z]+)?\s*$", s)
    if not m:
        raise ValueError(f"Invalid time format: {s}")
    value = float(m.group(1))
    unit = m.group(2) or "s"  # 默认秒
    if unit not in units:
        raise ValueError(f"Unknown unit: {unit}")

    return int(value * units[unit])


def rclone_flag_to_rsync(flag):
    if "=" not in flag:
        if flag == "--copy-links":
            return flag
        raise Exception(f"not support flag: `{flag}`")
    opt, val = flag.split("=")
    if opt == "--filter":
        if "+ " in val:
            val = shlex.split(val.replace("+ ", ""))[0]
            return f"--include='{val}'"
        else:
            val = shlex.split(val.replace("- ", ""))[0]
            return f"--exclude='{val}'"
    if opt == "--bwlimit":
        val = shlex.split(val)[0]
        try:
            v = int(val)

        except Exception as e:
            raise e
        return f"--bwlimit={v}"
    if opt == "--exclude":
        val = shlex.split(val)[0]
        return f"--exclude='{val}'"
    if opt == "--transfers":
        return ""
    if opt == "--min-age":
        val = parse_time_to_seconds(val)
        return f"--min-age={val}"
    raise ValueError(f"not support flag: `{flag}`")


def rclone_to_rsync(rclone_cmd):
    rsync_cmd = []
    for i in rclone_cmd:
        if i == "rclone":
            rsync_cmd.append("rsync")
            rsync_cmd.append("-a")
            continue
        if i in ["copy", "move"]:
            continue
        if i.startswith("--"):
            rsync_cmd.append(rclone_flag_to_rsync(i))
        else:
            rsync_cmd.append(i)
    return [i for i in rsync_cmd if i.strip()]


def _rclone_transfer_operation(
    cmd, source_path, target_path=None, flags=None, verbose=False, engine="rclone"
):
    command = cmd.copy()
    command.append(source_path)
    if target_path is not None:
        command.append(target_path)
    if flags is not None:
        command += flags
    if engine == "rsync":
        command = rclone_to_rsync(command)
    if verbose:
        logger.info("run {}", command)
    result = subprocess.run(
        " ".join(command),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
        shell=True,
        executable="/bin/bash",
        env=os.environ,  # 继承完整环境变量
        cwd=os.getcwd(),
    )
    if verbose and result.returncode != 0:
        logger.error(
            "run {} fail, code:{} reason:{}",
            " ".join(command),
            result.returncode,
            result.stderr.decode("utf-8"),
        )

    return result.returncode


def get_servers():
    command = ["rclone", "config", "dump"]
    result = subprocess.run(
        " ".join(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=os.environ,
        cwd=os.getcwd(),
        executable="/bin/bash",
        shell=True,
    )
    if result.returncode == 0:
        output = json.loads(result.stdout.decode("utf-8"))
        return list(output.keys())
    reason = result.stderr.decode("utf-8")
    logger.error("{}", reason)
    return None


def ls(source_path):
    command = ["rclone", "lsf", source_path]

    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if result.returncode == 0:
        return sorted(result.stdout.decode("utf-8").splitlines())
    reason = result.stderr.decode("utf-8")
    if "directory not found" in reason:
        return []
    logger.error("{}", result.stderr.decode("utf-8"))
    return []


def lsd(source_path):
    """列出目录下的文件夹"""
    command = ["rclone", "lsd", source_path]

    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if result.returncode == 0:
        ll = result.stdout.decode("utf-8").splitlines()
        ll[:] = [i.split()[-1] for i in ll]
        return sorted(ll)
    reason = result.stderr.decode("utf-8")
    if "directory not found" in reason:
        return []
    logger.error("{}", result.stderr.decode("utf-8"))
    return []


def move(source_path, target_path, flags=None, verbose=False):
    return _rclone_transfer_operation(
        ["rclone", "move"],
        source_path,
        target_path,
        flags,
        verbose=verbose,
    )


def copy(source_path, target_path, flags=None, verbose=False, engine="rclone"):
    return _rclone_transfer_operation(
        ["rclone", "copy"],
        source_path,
        target_path,
        flags,
        verbose=verbose,
        engine=engine,
    )


def sync(source_path, target_path, flags=None, verbose=False):
    """
    rclone sync source_path target_path
    """
    if os.path.isfile(source_path):
        logger.error("source_path must be directory, but input is {}", source_path)
        return None
    return _rclone_transfer_operation(
        ["rclone", "sync"], source_path, target_path, flags, verbose=verbose
    )
