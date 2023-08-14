from attr import dataclass


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
