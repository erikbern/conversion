import datetime, numpy, seaborn
from matplotlib import pyplot

def parse(date):
    if date:
        return datetime.date(*(int(p) for p in date.split('-')))
    else:
        return None

data = []
for line in open('freddie_data.tsv'):
    line = line.strip('\n').split('\t')
    data.append(tuple(parse(item) for item in line))

now = max(c for c, d, e in data)
events = []
YEAR = 365.25 * 24 * 60 * 60
for created, defaulted, prepaid in data:
    if defaulted:
        events.append(((defaulted - created).total_seconds() / YEAR, True))
    elif prepaid:
        events.append(((prepaid - created).total_seconds() / YEAR, False))
    else:
        events.append(((now - created).total_seconds() / YEAR, None))

# Compute a cohort plot by just averaging
events.sort()

n_act, n_def, n_pre = len(events), 0, 0
ns_act, ns_def, ns_pre = [n_act], [n_def], [n_pre]

for t, event in events:
    if event == True:
        n_def += 1
    elif event == False:
        n_pre += 1
    n_act -= 1
    if n_act == 0:
        break
    ns_act.append(n_act)
    ns_def.append(n_def)
    ns_pre.append(n_pre)

ns_act, ns_def, ns_pre = [numpy.array(x) for x in (ns_act, ns_def, ns_pre)]
ns_sum = ns_act + ns_def + ns_pre
ts = [t for t, _ in events]

c_def, c_act, c_pre = seaborn.color_palette('hls', 3)
pyplot.fill_between(ts, 0. * ns_def / ns_sum, 100. * ns_def / ns_sum, color=c_def, label='Defaulted')
pyplot.fill_between(ts, 100. * ns_def / ns_sum, 100. * (ns_def + ns_pre) / ns_sum, color=c_pre, label='Prepaid')
pyplot.fill_between(ts, 100. * (ns_def + ns_pre) / ns_sum, 100. * ns_sum / ns_sum, color=c_act, label='Still active')
pyplot.legend(loc='upper left')
pyplot.show()
