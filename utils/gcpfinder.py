import numpy
from scipy.optimize import linprog

RED = '#c74440'
BLUE = '#2d70b3'
GREEN = '#388c46'
PURPLE = '#6042a6'
ORANGE = '#fa7e19'

TEMPLATE = \
    '''
    <!DOCTYPE html>
    <script src="https://www.desmos.com/api/v1.7/calculator.js?apiKey=dcb31709b452b1cf9dc26972add0fda6"></script>
    <div id="calculator" style="width: 100%; height: 50vw;"></div>
    <script>
        var elt = document.getElementById('calculator');
        var calculator = Desmos.GraphingCalculator(elt, 
            { expressions: false, showGrid: false, showXAxis: false, showYAxis: false });
        calculator.setMathBounds({ left: -200000, right: 200000, bottom: -100000, top: 100000 });
        calculator.setExpressions(Array(
            <!-- insert here -->
        ));
      </script>
    '''


def graph(kmp, gcplist: list, splitpaths=False, bounds=(None, None)):
    if gcplist is None:
        gcplist = ['']
    ckpt = kmp['CKPT']['entries']
    ckph = kmp['CKPH']['entries']
    numcps = len(ckpt)
    group = 0
    script = []

    a_ = []
    b_ = []
    c_ = []
    d_ = []
    s1 = []
    s0 = []
    vneg = []

    for i in range(numcps):
        a_.append(f'a_{{{i}}}')
        b_.append(f'b_{{{i}}}')
        c_.append(f'c_{{{i}}}')
        d_.append(f'd_{{{i}}}')
        s1.append(f'\\\\frac{{({a_[i]}-{c_[i]})}}{{(({a_[i]}-{c_[i]})^{{2}}\\\\ '
                  f'+\\\\ ({d_[i]}-{b_[i]})^{{2}})^{{0.5}}}}')
        s0.append(f'\\\\frac{{({d_[i]}-{b_[i]})}}{{(({a_[i]}-{c_[i]})^{{2}}\\\\ '
                  f'+\\\\ ({d_[i]}-{b_[i]})^{{2}})^{{0.5}}}}')
        vneg.append(f'{s0[i]}(x-{c_[i]})+{s1[i]}(y-{d_[i]})')

    def to_script(latex: str, color_='', label=''):
        string = f'{{ latex: \'{latex}\''
        if color_:
            string += f', color: \'{color_}\''
        if label:
            string += f', label: \'{label}\', pointSize: 5, pointOpacity: 0.5, dragMode: Desmos.DragModes.NONE'
        string += ' }'
        script.append(string)

    for i in range(numcps):
        if ckpt[i]['prev'] == 255:
            prevs = [ckph[j]['start'] + ckph[j]['len'] - 1 for j in ckph[group]['prev'] if j != 255]
        else:
            prevs = [i - 1]

        if ckpt[i]['next'] == 255:
            nexts = [ckph[j]['start'] for j in ckph[group]['next'] if j != 255]
            group += 1
        else:
            nexts = [i + 1]

        if i in gcplist:
            color = RED
        elif ckpt[i]['type'] == 255:
            color = BLUE
        elif ckpt[i]['type'] == 0:
            color = GREEN
        else:
            color = PURPLE

        # Coordinates
        to_script(f'{a_[i]}={ckpt[i]["p1"][0]}')
        to_script(f'{b_[i]}={ckpt[i]["p1"][1] * -1}')
        to_script(f'{c_[i]}={ckpt[i]["p2"][0]}')
        to_script(f'{d_[i]}={ckpt[i]["p2"][1] * -1}')

        # Points
        to_script(f'({a_[i]}, {b_[i]})', color)
        to_script(f'({c_[i]}, {d_[i]})', color)
        to_script(f'(0.5({a_[i]}+{c_[i]}),0.5({b_[i]}+{d_[i]}))', color, label=str(i))

        # Checkpoint line
        to_script(f'((1-t){a_[i]}+t{c_[i]},(1-t){b_[i]}+t{d_[i]})', color)

        if ckpt[i]['type'] == 255:
            color = BLUE
        elif ckpt[i]['type'] == 0:
            color = GREEN
        else:
            color = PURPLE

        for nexti in nexts:
            vborder1 = f'-({b_[nexti]}-{b_[i]})(x-{a_[nexti]})+({a_[nexti]}-{a_[i]})(y-{b_[nexti]})'
            vborder2 = f'(({d_[nexti]}-{d_[i]})(x-{c_[i]})-({c_[nexti]}-{c_[i]})(y-{d_[i]}))'

            # Quadrilateral shading
            to_script(f'B_{{{i}t{nexti}}}=({vborder1}) * {vborder2} + \\\\left|{vborder1}\\\\right| * -{vborder2}')
            to_script(f'F_{{{i}t{nexti}}}=\\\\frac{{{vneg[i]}}}{{{vneg[i]} - '
                      f'({s0[nexti]}(x-{a_[nexti]})+{s1[nexti]}(y-{b_[nexti]}))}}')
            to_script(f'B_{{{i}t{nexti}}} > 0 \\\\left\\\\{{R_{{{nexti}t{i}}} > 0'
                      f'\\\\right\\\\}} \\\\left\\\\{{F_{{{i}t{nexti}}} > 0\\\\right\\\\}}', color)

            # Split path GCPs (end of split path)
            if splitpaths and len(nexts) > 1 and ckpt[i]['type'] == 255:
                to_script(f'B_{{{i}t{nexti}}} > 0 \\\\left\\\\{{B_{{{nexti}t{nexti + 1}}} > 0\\\\right\\\\}} '
                          f'\\\\left\\\\{{{vneg[i]} > 0\\\\right\\\\}}', ORANGE)

        for previ in prevs:
            to_script(f'R_{{{i}t{previ}}}=\\\\frac{{{vneg[i]}}}{{{vneg[i]} - '
                      f'({s0[previ]}(x-{a_[previ]})+{s1[previ]}(y-{b_[previ]}))}}')

            # Split path GCPs (beginning of split path)
            if splitpaths and len(prevs) > 1 and ckpt[i]['type'] == 255:
                to_script(f'B_{{{previ}t{i}}} > 0 \\\\left\\\\{{B_{{{i}t{i + 1}}} > 0\\\\right\\\\}} '
                          f'\\\\left\\\\{{{vneg[i]} < 0\\\\right\\\\}}', ORANGE)

        # Normal GCPs
        for previ in prevs:
            for nexti in nexts:
                gcp_area = f'B_{{{previ}t{i}}} > 0 \\\\left\\\\{{B_{{{i}t{nexti}}} > 0\\\\right\\\\}}\\\\left\\\\' \
                           f'{{R_{{{i}t{previ}}} < 0\\\\right\\\\}} \\\\left\\\\{{F_{{{i}t{nexti}}} < 0\\\\right\\\\}}'
                if bounds[0] is not None:
                    gcp_area += f'\\\\left\\\\{{{bounds[0]}<x<{bounds[1]}\\\\right\\\\}}' \
                              f'\\\\left\\\\{{{bounds[0]}<y<{bounds[1]}\\\\right\\\\}}'
                to_script(gcp_area, RED)

    text = TEMPLATE
    index = text.index('<!-- insert here -->')
    text1 = text[0:index]
    text2 = text[index + 20:]
    return text1 + ',\n'.join(script) + text2


# noinspection PyDeprecation
def find(kmp, bounds=(None, None), verbose=False):
    ckpt = kmp['CKPT']['entries']
    ckph = kmp['CKPH']['entries']
    numcps = len(ckpt)
    grp = 0
    gcplist = []

    a_ = []
    b_ = []
    c_ = []
    d_ = []
    s1 = []
    s0 = []
    prevs = []
    nexts = []
    cpline = []

    for i in range(numcps):
        a_.append(ckpt[i]["p1"][0])
        b_.append(ckpt[i]["p1"][1] * -1)
        c_.append(ckpt[i]["p2"][0])
        d_.append(ckpt[i]["p2"][1] * -1)
        s1.append((a_[i] - c_[i]) / ((a_[i] - c_[i]) ** 2 + (d_[i] - b_[i]) ** 2) ** 0.5)
        s0.append((d_[i] - b_[i]) / ((a_[i] - c_[i]) ** 2 + (d_[i] - b_[i]) ** 2) ** 0.5)
        cpline.append([s0[i], s1[i], (s0[i] * -c_[i]) + (s1[i] * -d_[i])])

        if ckpt[i]['prev'] == 255:
            prevs += [[ckph[j]['start'] + ckph[j]['len'] - 1 for j in ckph[grp]['prev'] if j != 255]]
        else:
            prevs += [[i - 1]]

        if ckpt[i]['next'] == 255:
            nexts += [[ckph[j]['start'] for j in ckph[grp]['next'] if j != 255]]
            grp += 1
        else:
            nexts += [[i + 1]]

    for i in range(numcps):
        fbdr1 = []
        fbdr2 = []
        rbdr1 = []
        rbdr2 = []
        vfor = []
        vback = []

        for nexti in nexts[i]:
            v1 = -(b_[nexti] - b_[i])
            v2 = (a_[nexti] - a_[i])
            fbdr1 += [[v1, v2, -a_[nexti] * v1 - b_[nexti] * v2]]

            v1 = (d_[nexti] - d_[i])
            v2 = -(c_[nexti] - c_[i])
            fbdr2 += [[v1, v2, -c_[i] * v1 - d_[i] * v2]]

            vf = [s0[nexti], s1[nexti], (s0[nexti] * -a_[nexti]) + (s1[nexti] * -b_[nexti])]
            vfor += [[cpline[i][j] - vf[j] for j in range(3)]]

        for previ in prevs[i]:
            v1 = -(b_[i] - b_[previ])
            v2 = (a_[i] - a_[previ])
            rbdr1 += [[v1, v2, -a_[i] * v1 - b_[i] * v2]]

            v1 = (d_[i] - d_[previ])
            v2 = -(c_[i] - c_[previ])
            rbdr2 += [[v1, v2, -c_[i] * v1 - d_[i] * v2]]

            vr = [s0[previ], s1[previ], (s0[previ] * -a_[previ]) + (s1[previ] * -b_[previ])]
            vback += [[cpline[i][j] - vr[j] for j in range(3)]]

        for j in range(len(nexts[i])):
            for k in range(len(prevs[i])):
                target = numpy.array([0, 0])
                mat1 = numpy.array([
                    [fbdr1[j][0],   fbdr1[j][1]],
                    [rbdr1[k][0], rbdr1[k][1]],
                    [fbdr2[j][0],   fbdr2[j][1]],
                    [rbdr2[k][0], rbdr2[k][1]],
                    [-cpline[i][0],     -cpline[i][1]],
                    [vfor[j][0],  vfor[j][1]],
                    [vback[k][0], vback[k][1]]
                ])
                const1 = numpy.array([
                    -fbdr1[j][2],
                    -rbdr1[k][2],
                    -fbdr2[j][2],
                    -rbdr2[k][2],
                    cpline[i][2],
                    -vfor[j][2],
                    -vback[k][2]
                ])

                mat2 = numpy.array([
                    [fbdr1[j][0], fbdr1[j][1]],
                    [rbdr1[k][0], rbdr1[k][1]],
                    [fbdr2[j][0], fbdr2[j][1]],
                    [rbdr2[k][0], rbdr2[k][1]],
                    [cpline[i][0], cpline[i][1]],
                    [-vfor[j][0], -vfor[j][1]],
                    [-vback[k][0], -vback[k][1]]
                ])
                const2 = numpy.array([
                    -fbdr1[j][2],
                    -rbdr1[k][2],
                    -fbdr2[j][2],
                    -rbdr2[k][2],
                    -cpline[i][2],
                    vfor[j][2],
                    vback[k][2]
                ])

                res1 = linprog(target, A_ub=mat1, b_ub=const1, bounds=bounds, method='highs')
                res2 = linprog(target, A_ub=mat2, b_ub=const2, bounds=bounds, method='highs')

                if res1.success:
                    if verbose:
                        gcplist += [(i, res1.x)]
                    else:
                        gcplist += [i]
                elif res2.success:
                    if verbose:
                        gcplist += [(i, res2.x)]
                    else:
                        gcplist += [i]

    return gcplist
