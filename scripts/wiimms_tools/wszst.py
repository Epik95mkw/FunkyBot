import os
import asyncio


async def sha1(srcpath) -> str:
    """
    Calculates the SHA1 hash of a SZS file.

    :param srcpath: location of target .szs file
    :returns: SHA1 of target .szs file
    """
    if not os.path.isfile(srcpath):
        raise FileNotFoundError('wszst sha1 failed: source file does not exist')

    cmd = f'wszst sha1 \"{srcpath}\"'
    c_proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await c_proc.communicate()
    return stdout.decode()


async def encode(srcpath, dstpath=None):
    """
    Reads a source file and encodes it into a new SZS file.

    *Note: auto-add library is required to encode WBZ to SZS*

    :param srcpath: location of target file
    :param dstpath: location of output .szs file, defaults to [srcdir]/[srcname].szs
    """
    if not os.path.isfile(srcpath):
        raise FileNotFoundError('wszst normalize failed: source file does not exist')
    if dstpath is not None and not os.path.isdir(os.path.dirname(dstpath)):
        raise NotADirectoryError('wszst normalize failed: destination path does not exist')

    cmd = f'wszst normalize \"{srcpath}\" -o --szs' + \
          (f' --dest \"{dstpath}\"' if dstpath is not None else '') + \
          f' >nul'
    c_proc = await asyncio.create_subprocess_shell(cmd)
    await c_proc.communicate()
    return True


async def compare(path1, path2) -> bool:
    """
    Compares two SZS files.

    :param path1: location of first file to compare
    :param path2: location of second file to compare
    :returns: True if files are identical, else False
    """
    if not os.path.isfile(path1) or not os.path.isfile(path2):
        raise FileNotFoundError('wszst diff failed: source file does not exist')

    cmd = f'wszst diff \"{path1}\" \"{path2}\"'
    c_proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await c_proc.communicate()
    return True if b'Content identical' in stdout else False
