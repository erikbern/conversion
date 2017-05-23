import datetime, lifelines, seaborn
from matplotlib import pyplot

data = []
T, E = [], []
for line in open('data_twitter.tsv'):
    created_at, now, count = [float(x) for x in line.strip('\n').split('\t')]
    created_at, now = (datetime.datetime.utcfromtimestamp(x) for x in (created_at, now))
    if count > 0:
        t, e = 
                 datetime.datetime.utcfromtimestamp(now),
                 count > 0))

# Compute Kaplan-Meier
for created, defaulted, ended in data:
    if defaulted:
        t, e = (defaulted - created).total_seconds(), True
    elif ended:
        t, e = float('inf'), True
    else:
        t, e = (now - created).total_seconds(), False
    T.append(t / (365 * 24 * 60 * 60))
    E.append(e)

print('fitting')
kmf = lifelines.KaplanMeierFitter()
kmf.fit(T, event_observed=E)
t = kmf.survival_function_.index.values
p = 1.0 - kmf.survival_function_['KM_estimate'].values
p_hi = 1.0 - kmf.confidence_interval_['KM_estimate_lower_0.95'].values
p_lo = 1.0 - kmf.confidence_interval_['KM_estimate_upper_0.95'].values
color = 'red'
pyplot.plot(t, 100. * p, color=color) #, label=label)
pyplot.fill_between(t, 100. * p_lo, 100. * p_hi, color=color, alpha=0.2)
pyplot.show()
