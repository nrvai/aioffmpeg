import asyncio


__all__ = (
    "close",
    "open"
)


async def open(args: list[str]) -> asyncio.subprocess.Process:
    command = [
        "ffmpeg",
        *args
    ]

    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

    return process


async def close(process: asyncio.subprocess.Process) -> int:
    assert process.stdin is not None
    assert process.stdout is not None

    process.stdin.write(b'q')
    await process.stdin.drain()

    while True:
        data = await process.stdout.read()

        if not data:
            break

    code = await process.wait()

    return code
