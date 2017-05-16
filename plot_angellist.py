import bisect, contextlib, datetime, json, lifelines, numpy, os, scipy.stats, seaborn, time
from matplotlib import pyplot, ticker


def parse_date(d):
    return datetime.datetime.utcfromtimestamp(time.mktime(time.strptime(d, '%b %d, %Y')))

data = []
for fn in os.listdir('cache'):
    if fn.startswith('companies'):
        stages = json.load(open(os.path.join('cache', fn)))
        seeds = [stage for stage in stages if stage['stage'] == 'Seed' or stage['stage'].startswith('Series')]
        exits = [stage for stage in stages if stage['stage'] == 'IPO' or stage['stage'].startswith('Acquired')]
        if not len(seeds):
            continue
        try:
            seeded = min(parse_date(stage['date']) for stage in seeds)
            if exits:
                exited = min(parse_date(stage['date']) for stage in exits)
                if exited < seeded:
                    continue
            else:
                exited = None
            data.append((seeded, exited))
        except OverflowError:
            continue
        except TypeError:
            continue


YEAR = 365.25 * 24 * 60 * 60
years = list(range(2008, 2016))

@contextlib.contextmanager
def shared_plot_setup(y_fmt=None, x_label=None, y_label=None, title=None, legend_loc='upper right'):
    fig = pyplot.figure(1, (9, 6))
    ax = fig.add_subplot(1, 1, 1)
    yticks = ticker.FormatStrFormatter(y_fmt)
    ax.yaxis.set_major_formatter(yticks)
    yield
    pyplot.legend(loc=legend_loc)
    pyplot.xlabel(x_label)
    pyplot.ylabel(y_label)
    pyplot.title(title)
    pyplot.show()

# Plot conversion by year
with shared_plot_setup(y_fmt='%.0f%%',
                       x_label='Year company was started',
                       y_label='Fraction exited',
                       title='Fraction of companies exited by year started'):
    n_by_year, k_by_year = {}, {}
    for seeded, exited in data:
        n_by_year[seeded.year] = n_by_year.get(seeded.year, 0) + 1
        if exited:
            k_by_year[seeded.year] = k_by_year.get(seeded.year, 0) + 1
    ns = numpy.array([n_by_year.get(year, 0) for year in years])
    ks = numpy.array([k_by_year.get(year, 0) for year in years])
    pyplot.plot(years, 100.*ks/ns, linestyle=':', marker='o', markersize=10, label='Exit %')
    pyplot.fill_between(years,
                        100.*scipy.stats.beta.ppf(0.05, ks+1, ns-ks+1),
                        100.*scipy.stats.beta.ppf(0.95, ks+1, ns-ks+1),
                        alpha=0.2,
                        label='Confidence interval')

# Plot time to conversion
with shared_plot_setup(y_fmt='%d',
                       x_label='Year company was started',
                       y_label='Number of years until exit',
                       title='Time to exit by year started'):
    t_by_year = {}
    for seeded, exited in data:
        if exited:
            t_by_year.setdefault(seeded.year, []).append((exited - seeded).total_seconds()/YEAR)
    ts = [t_by_year.get(year, []) for year in years]
    pyplot.plot(years, [numpy.median(t) for t in ts], linestyle=':', marker='o', markersize=10, label='Median time to exit')
    pyplot.plot(years, [numpy.percentile(t, 5) for t in ts], linestyle=':', marker='o', markersize=10, label='5th percentile')
    pyplot.plot(years, [numpy.percentile(t, 95) for t in ts], linestyle=':', marker='o', markersize=10, label='95th percentile')

# Plot Kaplan-Meier estimate
for with_confidence_interval, group_years in [(False, False), (True, False), (True, True)]:
    with shared_plot_setup(y_fmt='%.0f%%',
                           x_label='Years after start',
                           y_label='Fraction of companies exited',
                           title='Fraction of companies exited by time after start',
                           legend_loc='upper left'):
        now = datetime.datetime.now()
        TE_by_group = {}
        if group_years:
            split_year = years[int(len(years)/2)]
            group_lo = '%d-%d' % (years[0], split_year-1)
            group_hi = '%d-%d' % (split_year, years[-1])
            groups = [group_lo, group_hi]
        else:
            groups = years
        for seeded, exited in data:
            if group_years:
                group = seeded.year < split_year and group_lo or group_hi
            else:
                group = seeded.year
            T, E = TE_by_group.setdefault(group, ([], []))
            if exited:
                T.append((exited - seeded).total_seconds()/YEAR)
                E.append(True)
            else:
                T.append((now - seeded).total_seconds()/YEAR)
                E.append(False)
        colors = seaborn.color_palette('hls', len(groups))
        for group, color in zip(groups, colors):
            # Compute Kaplan-Meier using lifelines
            T, E = TE_by_group[group]
            kmf = lifelines.KaplanMeierFitter()
            kmf.fit(T, event_observed=E)
            ts = kmf.survival_function_.index.values
            max_i = bisect.bisect_left(ts, 5.0)
            ps = 1.0 - kmf.survival_function_['KM_estimate'].values
            ps_hi = 1.0 - kmf.confidence_interval_['KM_estimate_lower_0.95'].values
            ps_lo = 1.0 - kmf.confidence_interval_['KM_estimate_upper_0.95'].values
            pyplot.plot(ts[:max_i], 100. * ps[:max_i], label='Started in %s' % group, color=color)
            if with_confidence_interval:
                pyplot.fill_between(ts[:max_i], 100. * ps_lo[:max_i], 100. * ps_hi[:max_i], color=color, alpha=0.2)

            # Compute it manually
            te = sorted(zip(*TE_by_group[group]))
            n, k = len(te), 0
