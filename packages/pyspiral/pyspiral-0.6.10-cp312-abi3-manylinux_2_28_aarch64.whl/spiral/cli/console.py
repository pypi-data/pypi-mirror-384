import os
import subprocess

from spiral import Spiral
from spiral.adbc import ADBCFlightServer, SpiralADBCServer
from spiral.server import wait_for_port


def command():
    """Launch a SQL console to query Spiral tables."""

    # To avoid taking a dependency on Harlequin, we install it on-demand using
    # either uvx or pipx.
    harlequin_args = _uvx()
    if harlequin_args is None:
        harlequin_args = _pipx()
    if harlequin_args is None:
        raise ValueError("Please install pipx to continue\n\tSee https://github.com/pypa/pipx")

    # Set up a pipe to send the server port to the child process.
    r, w = os.pipe()

    pid = os.fork()
    if pid == 0:  # In the child
        os.close(w)
        port = int.from_bytes(os.read(r, 4), "big")

        # Wait for the server to be up.
        wait_for_port(port)

        os.execv(
            harlequin_args[0],
            harlequin_args
            + [
                "-a",
                "adbc",
                "--driver-type",
                "flightsql",
                f"grpc://localhost:{port}",
            ],
        )
    else:
        os.close(r)

        # I can't get the Flight server to stop writing to stdout. So we need to spawn a new process I think and
        # then hope we can kill it?
        fd = os.open("/dev/null", os.O_WRONLY)
        os.dup2(fd, 1)
        os.dup2(fd, 2)

        # In the parent, we launch the Flight SQL server and send the port to the child
        server = ADBCFlightServer(SpiralADBCServer(Spiral()))
        os.write(w, server.port.to_bytes(4, "big"))

        # Then wait for the console app to exit
        os.waitpid(pid, 0)


def _pipx() -> list[str] | None:
    """Run harlequin via pipx."""
    res = subprocess.run(["which", "pipx"], stdout=subprocess.PIPE)
    if res.returncode != 0:
        return None
        # raise ValueError("Please install pipx to continue\n\tSee https://github.com/pypa/pipx")
    pipx = res.stdout.strip()

    return [
        pipx,
        "run",
        "--pip-args",
        "adbc_driver_flightsql",
        "--pip-args",
        # for now, we pin rich
        "rich<=13.9.1",
        "harlequin[adbc]",
    ]


def _uvx() -> list[str] | None:
    """Run harlequin via uvx."""
    res = subprocess.run(["which", "uvx"], stdout=subprocess.PIPE)
    if res.returncode != 0:
        return None
    uvx = res.stdout.strip()

    return [
        uvx,
        "--with",
        "adbc_driver_flightsql",
        "--with",
        "rich<=13.9.1",
        "--from",
        "harlequin[adbc]",
        "harlequin",
    ]
