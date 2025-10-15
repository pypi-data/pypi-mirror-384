from __future__ import annotations
import click
from typing import Optional, Tuple
from ..runner import run_pytest


@click.command(name="run")
@click.option("--marks", help="Override pytest -m expression for this run")
@click.option(
    "-n", "workers", type=int, help="Override number of xdist workers for this run"
)
@click.option("--reruns", type=int, help="Override number of reruns for this run")
@click.option(
    "--count",
    type=int,
    help="Number of times to repeat each test (requires pytest-repeat)",
)
@click.option(
    "--timeout",
    type=int,
    help="Per-test timeout in seconds (overrides config/default)",
)
@click.argument("extra", nargs=-1)
@click.pass_context
def run_cmd(
    ctx: click.Context,
    marks: Optional[str],
    workers: Optional[int],
    reruns: Optional[int],
    count: Optional[int],
    timeout: Optional[int],
    extra: Tuple[str, ...],
):
    """Run pytest with configured options.

    Example: codemie-test-harness run --marks "smoke and not ui" -n 8 --reruns 2 -k keyword
    Example with repeat: codemie-test-harness run --marks excel_generation --count 50 -n 10
    Example with timeout: codemie-test-harness run --marks slow --timeout 600 -n 4
    """
    resolved_marks = marks or ctx.obj.get("marks")
    resolved_workers = workers if workers is not None else ctx.obj.get("workers")
    resolved_reruns = reruns if reruns is not None else ctx.obj.get("reruns")
    resolved_count = count if count is not None else ctx.obj.get("count")
    resolved_timeout = timeout if timeout is not None else ctx.obj.get("timeout")

    run_pytest(
        int(resolved_workers),
        str(resolved_marks),
        int(resolved_reruns),
        resolved_count,
        resolved_timeout,
        extra,
    )
