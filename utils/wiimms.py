import asyncio
import os


async def kmp_decode(path, filename='course.kmp'):
    pathlist = os.listdir(path)
    if f'{filename[0:-4]}.txt' in pathlist or 'kmperr.txt' in pathlist:
        return True
    elif filename in pathlist:
        cmd = f'wkmpt decode \"{path}{filename}\" --dest \"{path}\" --export > \"{path}kmperr.txt\" 2>nul'
        c_proc = await asyncio.create_subprocess_shell(cmd)
        await c_proc.communicate()
        return True
    else:
        print(f'KMP decode failed: file {filename} not found')
        return False


async def kmp_encode(path, filename='course.txt', destname=''):
    pathlist = os.listdir(path)
    if 'course.kmp' in pathlist:
        return True
    elif filename in pathlist:
        cmd = f'wkmpt encode \"{path}{filename}\" --dest \"{path}{destname}\" >nul'
        c_proc = await asyncio.create_subprocess_shell(cmd)
        await c_proc.communicate()
        return True
    else:
        print(f'KMP encode failed: file {filename} not found')
        return False


async def kcl_flags(path, filename='course.kcl'):
    pathlist = os.listdir(path)
    if 'kcl.txt' in pathlist:
        return True
    elif filename in pathlist:
        cmd = f'wkclt flags \"{path}{filename}\" > \"{path}kcl.txt\" 2>nul'
        c_proc = await asyncio.create_subprocess_shell(cmd)
        await c_proc.communicate()
        return True
    else:
        print(f'KCL decode failed: file {filename} not found')
        return False


async def kcl_encode(path, filename, destname=''):
    pathlist = os.listdir(path)
    if 'course.kcl' in pathlist:
        return True
    elif filename in pathlist:
        cmd = f'wkclt encode \"{path}{filename}\" --dest \"{path}{destname}\" >nul'
        c_proc = await asyncio.create_subprocess_shell(cmd)
        await c_proc.communicate()
        return True
    else:
        print(f'KCL encode failed: file {filename} not found')
        return False


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


def calculate_cpinfo(kmpobj, trackname='track', silent=False):
    if not silent:
        print(f'Calculating values for {trackname}...')
    ckpt: list[dict] = kmpobj['CKPT']['entries']     # [c['type'] for c in kmp['CKPT']['entries']]
    ckph: list[dict] = kmpobj['CKPH']['entries']
    values = [len(ckph), len(ckpt)]

    # Map each checkpoint to its group
    group = {}
    for g in ckph:
        for i in range(g['start'], g['start'] + g['len']):
            group[i] = g

    # Find important checkpoints
    cp0count:       int = 0
    kcpcount:       int = 0
    total_layers:   int = 0
    kcp0:           int = 0
    cp1s:           list[int] = []
    lastcps:        list[int] = []
    maxkcps:        list[int] = [0]
    for cp in ckpt:
        if cp['type'] < 255:
            kcpcount += 1

            if cp['type'] == 0:     # Find kcp0 and checkpoint(s) immediately following
                kcp0 = cp['idx']
                cp0count += 1
                if cp['next'] == 255:
                    for i in [j for j in group[kcp0]['next'] if j < 255]:
                        cp1s += [ckph[i]['start']]
                else:
                    cp1s = [cp['next']]

                for i in [j for j in group[kcp0]['prev'] if j < 255]:       # Find cp behind kcp0
                    lastcps += [ckph[i]['start'] + ckph[i]['len'] - 1]
                    if total_layers < ckph[i]['layer']:
                        total_layers = ckph[i]['layer']

            kcp = ckpt[maxkcps[0]]
            if kcp['type'] < cp['type'] < 100:   # Find max key checkpoint(s)
                maxkcps = [cp['idx']]
            elif kcp['type'] == cp['type']:
                maxkcps += [cp['idx']]

    values.append(kcpcount)
    values.append(maxkcps[0])

    if cp0count != 1:
        return values + [-1, -1, -1, -1]

    # Calculate lap completion for each checkpoint
    completion = {}
    for i in range(len(ckpt)):
        group_c = (i - group[i]['start']) / group[i]['len']
        overall_c = (group_c + group[i]['layer'] - 1) / total_layers
        completion[i] = overall_c

    cp1: int = cp1s[0]
    for cp in cp1s:
        if completion[cp1] < completion[cp]:
            cp1 = cp

    lastcp: int = lastcps[0]

    maxkcp: int = maxkcps[0]
    for kcp in maxkcps:
        if completion[maxkcp] > completion[kcp]:
            maxkcp = kcp

    # Calculate maximum indices that avoid 95% from cp0 and cp1
    ifrom0 = 0
    ifrom1 = 0
    for i in range(lastcp, 0, -1):
        interval = 1 / (group[i]['len'] * total_layers)

        if ifrom1 == 0 and completion[i] <= 0.95 + completion[cp1]:
            ifrom1 = i + ((0.95 + completion[cp1] - completion[i]) / interval)

        if ifrom0 == 0 and completion[i] <= 0.95 + completion[kcp0]:
            ifrom0 = i + ((0.95 + completion[kcp0] - completion[i]) / interval)
            break

    values.append(float('{:.2f}'.format(min(ifrom0, lastcp))))
    values.append(float('{:.2f}'.format(min(ifrom1, lastcp))))
    values.append(float('{:.4f}'.format(completion[maxkcp])))
    values.append(float('{:.4f}'.format(min(0.95 + completion[cp1], completion[lastcp]))))

    return values


async def kcl_search(path, tl, string):
    for t in tl:
        path = f'{path}{t.replace(":", "")}/'
        if 'kcl.txt' not in os.listdir(path):
            await kcl_flags(path)
        with open(path + 'kcl.txt', 'r') as f:
            if string in f.read():
                print(t)


async def kmp_search(path, tl, string):
    for t in tl:
        path = f'{path}{t.replace(":", "")}/'
        if 'kmperr.txt' not in os.listdir(path):
            await kmp_decode(path)
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
