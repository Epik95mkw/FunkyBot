import asyncio
import os


async def _run_subprocess(cmd):
    c_proc = await asyncio.create_subprocess_shell(cmd)
    await c_proc.communicate()
    return True


async def wkmpt_decode(srcpath, dstpath=None, errpath=None):
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


async def wkmpt_encode(srcpath, dstpath=None):
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


async def wkclt_flags(srcpath, dstpath=None):
    """
    Reads a KCL file and prints KCL flag statistics to stdout.

    :param srcpath: location of target .szs or .kcl file
    :param dstpath: optional, location of text file where output is piped
    """
    if not os.path.isfile(srcpath):
        raise FileNotFoundError('wkmpt encode failed: source file does not exist')
    if dstpath is not None and not os.path.isdir(os.path.dirname(dstpath)):
        raise NotADirectoryError('wkmpt decode failed: destination path does not exist')

    cmd = f'wkclt flags \"{srcpath}\"' + \
          (f' > \"{dstpath}\"' if dstpath is not None else '') + \
          f' 2>nul'
    return await _run_subprocess(cmd)


async def wkclt_encode(srcpath, dstpath=None):
    """
    Reads a SZS or OBJ file and produces a binary KCL file.

    :param srcpath: location of target .szs or .obj file
    :param dstpath: location of output .kcl file, defaults to [srcdir]/[srcname].kcl
    """
    if not os.path.isfile(srcpath):
        raise FileNotFoundError('wkmpt encode failed: source file does not exist')
    if dstpath is not None and not os.path.isdir(os.path.dirname(dstpath)):
        raise NotADirectoryError('wkmpt decode failed: destination path does not exist')

    cmd = f'wkclt encode \"{srcpath}\"' + \
          (f' --dest \"{dstpath}\"' if dstpath is not None else '') + \
          f' >nul'
    return await _run_subprocess(cmd)


# TODO: Refactor functions below to match above

async def kmp_draw(path, filename='course.kmp'):
    if filename in os.listdir(path):
        cmd = f'wkmpt draw \"{path}\"{filename} --dest \"{path}\" --draw=ckpt,kcl,roadobjects,black --png 100a0 >nul'
        print('Generating png...')
        c_proc = await asyncio.create_subprocess_shell(cmd)
        await c_proc.communicate()
        print('KMP draw succeeded')
        return True
    else:
        print(f'KMP draw failed: file {filename} not found')
        return False


async def kcl_clean(srcpath, dstpath, filename='course.kcl'):
    if filename in os.listdir(srcpath):
        cmd = f'wkclt COPY \"{srcpath}\"{filename} \"{dstpath}\" --kcl DROP'
        c_proc = await asyncio.create_subprocess_shell(cmd)
        await c_proc.communicate()
        print('KCL clean succeeded')
        return True
    else:
        print(f'KCL clean failed: file {filename} not found')
        return False


async def kcl_search(path, tl, string):
    for t in tl:
        path = f'{path}{t.replace(":", "")}/'
        if 'kcl.txt' not in os.listdir(path):
            await wkclt_flags(path)
        with open(path + 'kcl.txt', 'r') as f:
            if string in f.read():
                print(t)


async def kmp_search(path, tl, string):
    for t in tl:
        path = f'{path}{t.replace(":", "")}/'
        if 'kmperr.txt' not in os.listdir(path):
            await wkmpt_decode(path)
        with open(path + 'kmperr.txt', 'r') as f:
            if string in f.read():
                print(t)


async def szs_hash(path: str, filename: str):
    pathlist = os.listdir(path)
    if filename in pathlist:
        cmd = f'wszst sha1 \"{path}/{filename}\"'
        c_proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE)
        stdout, _ = await c_proc.communicate()
        return stdout.decode()
    else:
        print(f'SZS hash failed: file {filename} not found')
        return None


async def szs_encode(path, filename, destname=''):
    if not destname:
        destname = filename[0:-4]
    if filename in os.listdir(path):
        cmd = f'wszst normalize \"{path}/{filename}\" --dest \"{path}/{destname}.szs\" ' \
              f'--szs --overwrite --rm-src >nul'
        c_proc = await asyncio.create_subprocess_shell(cmd)
        await c_proc.communicate()
        return True
    else:
        print(f'SZS encode failed: file {filename} not found')
        return False


async def szs_cmp(path1, path2):
    cmd = f'wszst diff \"{path1}\" \"{path2}\"'
    c_proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await c_proc.communicate()
    return True if b'Content identical' in stdout else False


def test():
    thing = os.path.dirname('a/path/to/a/file.txt')
    print(thing)


if __name__ == '__main__':
    test()
