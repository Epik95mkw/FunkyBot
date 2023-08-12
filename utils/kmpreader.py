from attr import dataclass
from construct import *


def parse(f):
    kmpobj = kmp_format.parse(f.read())
    compute_ckph_layers(kmpobj, 0, 1)
    return dict(kmpobj)


def compute_ckph_layers(kmp, group: int, layer: int):
    ckph = kmp['CKPH']['entries']
    ckph[group]['layer'] = layer
    if len(ckph) > 1:
        for i in ckph[group]['next']:
            if i != 255 and ckph[i]['layer'] == -1:
                compute_ckph_layers(kmp, i, layer + 1)


ktpt_format = Struct(
        'name' / Const(b'KTPT'),
        'entrycount' / Short,
        'data' / Short,
        'entries' / Struct(
            'idx' / Index,
            'pos' / Single[3],
            'rot' / Single[3],
            'playerID' / Short,
            Padding(2)
        )[this.entrycount]
    )

enpt_format = Struct(
    'name' / Const(b'ENPT'),
    'entrycount' / Short,
    'data' / Short,
    'entries' / Struct(
        'idx' / Index,
        'pos' / Single[3],
        'variance' / Single,
        's1' / Short,
        's2' / Byte,
        's3' / Byte
    )[this.entrycount]
)

enph_format = Struct(
    'name' / Const(b'ENPH'),
    'entrycount' / Short,
    'data' / Short,
    'entries' / Struct(
        'gidx' / Index,
        'start' / Byte,
        'len' / Byte,
        'prev' / Byte[6],
        'next' / Byte[6],
        Padding(2)
    )[this.entrycount]
)

itpt_format = Struct(
    'name' / Const(b'ITPT'),
    'entrycount' / Short,
    'data' / Short,
    'entries' / Struct(
        'idx' / Index,
        'pos' / Single[3],
        'variance' / Single,
        's1' / Short,
        's2' / Short
    )[this.entrycount]
)

itph_format = Struct(
    'name' / Const(b'ITPH'),
    'entrycount' / Short,
    'data' / Short,
    'entries' / Struct(
        'gidx' / Index,
        'start' / Byte,
        'len' / Byte,
        'prev' / Byte[6],
        'next' / Byte[6],
        Padding(2)
    )[this.entrycount]
)

ckpt_format = Struct(
    'name' / Const(b'CKPT'),
    'entrycount' / Short,
    'data' / Short,
    'entries' / Struct(
        'idx' / Index,
        'p1' / Single[2],
        'p2' / Single[2],
        'res' / Byte,
        'type' / Byte,
        'prev' / Byte,
        'next' / Byte
    )[this.entrycount]
)

ckph_format = Struct(
    'name' / Const(b'CKPH'),
    'entrycount' / Short,
    'data' / Short,
    'entries' / Struct(
        'gidx' / Index,
        'start' / Byte,
        'len' / Byte,
        'prev' / Byte[6],
        'next' / Byte[6],
        'layer' / Computed(-1),
        Padding(2)
    )[this.entrycount]
)

gobj_format = Struct(
    'name' / Const(b'GOBJ'),
    'entrycount' / Short,
    'data' / Short,
    'entries' / Struct(
        'idx' / Index,
        'id' / Short,
        'xpf_id' / Short,
        'pos' / Single[3],
        'rot' / Single[3],
        'scale' / Single[3],
        'route' / Short,
        'settings' / Short[8],
        'presence' / Short
    )[this.entrycount]
)

poti_format = Struct(
    'name' / Const(b'POTI'),
    'entrycount' / Short,
    'data' / Short,
    'entries' / Struct(
        'idx' / Index,
        'len' / Short,
        'smooth' / Byte,
        'motion_type' / Byte,
        'points' / Struct(
            'idx' / Index,
            'pos' / Single[3],
            's1' / Short,
            's2' / Short
        )[this.len]
    )[this.entrycount]
)

area_format = Struct(
    'name' / Const(b'AREA'),
    'entrycount' / Short,
    'data' / Short,
    'entries' / Struct(
        'idx' / Index,
        'shape' / Byte,
        'type' / Byte,
        'camera' / Byte,
        'priority' / Byte,
        'pos' / Single[3],
        'rot' / Single[3],
        'scale' / Single[3],
        's1' / Short,
        's2' / Short,
        'route' / Byte,
        'enpt' / Byte,
        Padding(2)
    )[this.entrycount]
)

came_format = Struct(
    'name' / Const(b'CAME'),
    'entrycount' / Short,
    'data' / Short,
    'entries' / Struct(
        'idx' / Index,
        'type' / Byte,
        'next' / Byte,
        'shake' / Byte,
        'route' / Byte,
        'pointspd' / Short,
        'zoomspd' / Short,
        'viewspd' / Short,
        'start' / Byte,
        'movie' / Byte,
        'pos' / Single[3],
        'rot' / Single[3],
        'zoom_s' / Single,
        'zoom_f' / Single,
        'viewpos_s' / Single[3],
        'viewpos_f' / Single[3],
        'time' / Single
    )[this.entrycount]
)

jgpt_format = Struct(
    'name' / Const(b'JGPT'),
    'entrycount' / Short,
    'data' / Short,
    'entries' / Struct(
        'idx' / Index,
        'pos' / Single[3],
        'rot' / Single[3],
        'id' / Short,
        'range' / Short
    )[this.entrycount]
)

cnpt_format = Struct(
    'name' / Const(b'CNPT'),
    'entrycount' / Short,
    'data' / Short,
    'entries' / Struct(
        'idx' / Index,
        'pos' / Single[3],
        'rot' / Single[3],
        'id' / Short,
        'effect' / Short
    )[this.entrycount]
)

mspt_format = Struct(
    'name' / Const(b'MSPT'),
    'entrycount' / Short,
    'data' / Short,
    'entries' / Struct(
        'idx' / Index,
        'pos' / Single[3],
        'rot' / Single[3],
        'id' / Index,
        Padding(2)
    )[this.entrycount]
)

stgi_format = Struct(
    'name' / Const(b'STGI'),
    'entrycount' / Short,
    'data' / Short,
    'entries' / Struct(
        'idx' / Index,
        'laps' / Byte,
        'pole_pos' / Byte,
        'narrow' / Byte,
        'lensflare' / Byte,
        Padding(1),
        'flare_color' / Byte[4],
        Padding(1),
        'speedmod' / Half
    )[this.entrycount]
)

kmp_format = Struct(
    'magic' / Const(b'RKMD'),
    'len' / Int,
    'sectioncount' / Short,
    'headerlen' / Short,
    'ver' / Int,
    'KTPT_offset' / Int,
    'ENPT_offset' / Int,
    'ENPH_offset' / Int,
    'ITPT_offset' / Int,
    'ITPH_offset' / Int,
    'CKPT_offset' / Int,
    'CKPH_offset' / Int,
    'GOBJ_offset' / Int,
    'POTI_offset' / Int,
    'AREA_offset' / Int,
    'CAME_offset' / Int,
    'JGPT_offset' / Int,
    'CNPT_offset' / Int,
    'MSPT_offset' / Int,
    'STGI_offset' / Int,
    'KTPT' / Pointer(this.headerlen + this.KTPT_offset, ktpt_format),
    'ENPT' / Pointer(this.headerlen + this.ENPT_offset, enpt_format),
    'ENPH' / Pointer(this.headerlen + this.ENPH_offset, enph_format),
    'ITPT' / Pointer(this.headerlen + this.ITPT_offset, itpt_format),
    'ITPH' / Pointer(this.headerlen + this.ITPH_offset, itph_format),
    'CKPT' / Pointer(this.headerlen + this.CKPT_offset, ckpt_format),
    'CKPH' / Pointer(this.headerlen + this.CKPH_offset, ckph_format),
    'GOBJ' / Pointer(this.headerlen + this.GOBJ_offset, gobj_format),
    'POTI' / Pointer(this.headerlen + this.POTI_offset, poti_format),
    'AREA' / Pointer(this.headerlen + this.AREA_offset, area_format),
    'CAME' / Pointer(this.headerlen + this.CAME_offset, came_format),
    'JGPT' / Pointer(this.headerlen + this.JGPT_offset, jgpt_format),
    'CNPT' / Pointer(this.headerlen + this.CNPT_offset, cnpt_format),
    'MSPT' / Pointer(this.headerlen + this.MSPT_offset, mspt_format),
    'STGI' / Pointer(this.headerlen + this.STGI_offset, stgi_format)
)


@dataclass
class CheckpointData:
    group_count: int
    cp_count: int
    kcp_count: int
    last_kcp: int
    from_cp0: float
    from_cp1: float
    last_kcp_p: float
    max_ultra_p: float
    anomalies: str = None


def calculate_cpinfo(kmpobj, trackname='track', silent=False) -> CheckpointData:
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
        values += [-1, -1, -1, -1]
        return CheckpointData(*values)

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

    return CheckpointData(*values)
