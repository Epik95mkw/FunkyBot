import os
import asyncio


async def _run_subprocess(cmd):
    c_proc = await asyncio.create_subprocess_shell(cmd)
    await c_proc.communicate()
    return True


async def flags(srcpath, dstpath=None):
    """
    Reads a KCL file and prints KCL flag statistics to stdout.

    :param srcpath: location of target .szs or .kcl file
    :param dstpath: optional, location of text file where output is piped
    """
    if not os.path.isfile(srcpath):
        raise FileNotFoundError('wkclt flags failed: source file does not exist')
    if dstpath is not None and not os.path.isdir(os.path.dirname(dstpath)):
        raise NotADirectoryError('wkclt flags failed: destination path does not exist')

    cmd = f'wkclt flags \"{srcpath}\"' + \
          (f' > \"{dstpath}\"' if dstpath is not None else '') + \
          f' 2>nul'
    return await _run_subprocess(cmd)


async def encode(srcpath, dstpath=None):
    """
    Reads a SZS or OBJ file and produces a binary KCL file.

    :param srcpath: location of target .szs or .obj file
    :param dstpath: location of output .kcl file, defaults to [srcdir]/[srcname].kcl
    """
    if not os.path.isfile(srcpath):
        raise FileNotFoundError('wkclt encode failed: source file does not exist')
    if dstpath is not None and not os.path.isdir(os.path.dirname(dstpath)):
        raise NotADirectoryError('wkclt encode failed: destination path does not exist')

    cmd = f'wkclt encode \"{srcpath}\" -o' + \
          (f' --dest \"{dstpath}\"' if dstpath is not None else '') + \
          f' >nul'
    return await _run_subprocess(cmd)


async def clean(srcpath, dstpath):
    """
    Creates a copy of a binary KCL file with invalid triangles removed.

    :param srcpath: location of target .szs or .kcl file
    :param dstpath: location of output .kcl file
    """
    if not os.path.isfile(srcpath):
        raise FileNotFoundError('wkclt copy failed: source file does not exist')
    if not os.path.isdir(os.path.dirname(dstpath)):
        raise NotADirectoryError('wkclt copy failed: destination path does not exist')

    cmd = f'wkclt copy \"{srcpath}\" \"{dstpath}\" --kcl DROP'
    return await _run_subprocess(cmd)

