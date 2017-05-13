import datetime, json, lifelines, numpy, os, scipy.stats, seaborn, time
from matplotlib import pyplot


def parse_date(d):
    return datetime.datetime.utcfromtimestamp(time.mktime(time.strptime(d, '%b %d, %Y')))

data = []
for fn in os.listdir('cache'):
    if fn.startswith('companies'):
        stages = json.load(open(os.path.join('cache', fn)))
        seeds = [stage for stage in stages if stage['stage'] == 'Seed']
        acquisitions = [stage for stage in stages if stage['stage'].startswith('Acquired')]
        if not len(seeds):
            continue
        try:
            seeded = min(parse_date(stage['date']) for stage in stages)
            if acquisitions:
                acquired = min(parse_date(stage['date']) for stage in acquisitions)
            else:
                acquired = None
            data.append((seeded, acquired))
        except OverflowError:
            continue
        except TypeError:
            continue


YEAR = 365.25 * 24 * 60 * 60
years = list(range(2008, 2016))

# Plot conversion by year
n_by_year, k_by_year = {}, {}
for seeded, acquired in data:
    n_by_year[seeded.year] = n_by_year.get(seeded.year, 0) + 1
    if acquired:
        k_by_year[seeded.year] = k_by_year.get(seeded.year, 0) + 1
ns = numpy.array([n_by_year.get(year, 0) for year in years])
ks = numpy.array([k_by_year.get(year, 0) for year in years])
pyplot.plot(years, 100.*ks/ns, '.-')
pyplot.fill_between(years,
                    100.*scipy.stats.beta.ppf(0.05, ks, ns), # TODO: verify math
                    100.*scipy.stats.beta.ppf(0.95, ks, ns),
                    alpha=0.2)
pyplot.show()

# Plot time to conversion
t_by_year = {}
for seeded, acquired in data:
    if acquired:
        t_by_year.setdefault(seeded.year, []).append((acquired - seeded).total_seconds()/YEAR)
ts = [t_by_year.get(year, []) for year in years]
pyplot.plot(years, [numpy.median(t) for t in ts])
pyplot.fill_between(years,
                    [numpy.percentile(t, 5) for t in ts],
                    [numpy.percentile(t, 95) for t in ts],
                    alpha=0.2)
pyplot.show()

# Plot Kaplan-Meier estimate
now = datetime.datetime.now()
TE_by_year = {}
for seeded, acquired in data:
    T, E = TE_by_year.setdefault(seeded.year, ([], []))
    if acquired:
        T.append((acquired - seeded).total_seconds()/YEAR)
        E.append(True)
    else:
        T.append((now - seeded).total_seconds()/YEAR)
        E.append(False)
for year in years:
    T, E = TE_by_year[year]
    kmf = lifelines.KaplanMeierFitter()
    kmf.fit(T, event_observed=E)
    t = kmf.survival_function_.index.values
    p = 1.0 - kmf.survival_function_['KM_estimate'].values
    p_hi = 1.0 - kmf.confidence_interval_['KM_estimate_lower_0.95'].values
    p_lo = 1.0 - kmf.confidence_interval_['KM_estimate_upper_0.95'].values
    pyplot.plot(t, 100. * p, label=year)
    # pyplot.fill_between(t, 100. * p_lo, 100. * p_hi, color=color, alpha=0.2)
pyplot.legend(loc='upper left')
pyplot.show()
