import os
import asyncio


async def _run_subprocess(cmd):
    c_proc = await asyncio.create_subprocess_shell(cmd)
    await c_proc.communicate()
    return True


async def decode(srcpath, dstpath=None, errpath=None):
    """
    Reads a KMP file and decodes it into a human-readable text file.

    :param srcpath: location of target .szs or .kmp file
    :param dstpath: location of output text file, defaults to [srcdir]/[srcname].txt
    :param errpath: optional, location of text file where error output is piped
    """
    if not os.path.isfile(srcpath):
        raise FileNotFoundError('wkmpt decode failed: source file does not exist')
    if dstpath is not None and not os.path.isdir(os.path.dirname(dstpath)):
        raise NotADirectoryError('wkmpt decode failed: destination path does not exist')
    if errpath is not None and not os.path.isdir(os.path.dirname(errpath)):
        raise NotADirectoryError('wkmpt decode failed: error output path does not exist')

    cmd = f'wkmpt decode \"{srcpath}\" -o --export' + \
          (f' --dest \"{dstpath}\"' if dstpath is not None else '') + \
          (f' > \"{errpath}\"' if errpath is not None else '') + \
          f' 2>nul'
    return await _run_subprocess(cmd)


async def encode(srcpath, dstpath=None):
    """
    Reads an input file (can be SZS or text-form KMP) and produces a binary KMP file.

    :param srcpath: location of target .szs or text file
    :param dstpath: location of output .kmp file, defaults to [srcdir]/[srcname].kmp
    """
    if not os.path.isfile(srcpath):
        raise FileNotFoundError('wkmpt encode failed: source file does not exist')
    if dstpath is not None and not os.path.isdir(os.path.dirname(dstpath)):
        raise NotADirectoryError('wkmpt decode failed: destination path does not exist')

    cmd = f'wkmpt encode \"{srcpath}\" -o' + \
          (f' --dest \"{dstpath}\"' if dstpath is not None else '') + \
          f' >nul'
    return await _run_subprocess(cmd)


async def draw(srcpath, dstpath=None):
    """
    Reads a KMP or SZS file and generates an image of the checkpoint map.

    :param srcpath: location of target .szs or .kmp file
    :param dstpath: location of output .png file, defaults to [srcpath].png
    """
    if not os.path.isfile(srcpath):
        raise FileNotFoundError('wkmpt draw failed: source file does not exist')
    if dstpath is not None and not os.path.isdir(os.path.dirname(dstpath)):
        raise NotADirectoryError('wkmpt draw failed: destination path does not exist')

    cmd = f'wkmpt draw \"{srcpath}\" -o --draw=ckpt,kcl,roadobjects,black --png 100a0' + \
          (f' --dest \"{dstpath}\"' if dstpath is not None else '') + \
          f' >nul'
    return await _run_subprocess(cmd)
