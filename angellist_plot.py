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

print(len(data))
print(sum(1 for seeded, exited in data if exited is not None))

YEAR = 365.25 * 24 * 60 * 60
years = list(range(2008, 2016))

@contextlib.contextmanager
def shared_plot_setup(y_fmt=None, x_label=None, y_label=None, title=None, legend_loc='upper right', output_fn=None, xlim=None, ylim=None):
    fig = pyplot.figure(1, (9, 6))
    ax = fig.add_subplot(1, 1, 1)
    yticks = ticker.FormatStrFormatter(y_fmt)
    ax.yaxis.set_major_formatter(yticks)
    yield
    pyplot.legend(loc=legend_loc)
    pyplot.xlabel(x_label)
    pyplot.ylabel(y_label)
    pyplot.title(title)
    if xlim:
        pyplot.xlim(xlim)
    if ylim:
        pyplot.ylim(ylim)
    if output_fn:
        pyplot.savefig(output_fn)
    pyplot.show()

# Plot conversion by year
with shared_plot_setup(y_fmt='%.0f%%',
                       x_label='Year company was started',
                       y_label='Fraction exited',
                       title='Fraction of companies exited by year started',
                       output_fn='conversion_by_year.png'):
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
                       title='Time to exit by year started',
                       output_fn='time_to_conversion_by_year.png'):
    t_by_year = {}
    for seeded, exited in data:
        if exited:
            t_by_year.setdefault(seeded.year, []).append((exited - seeded).total_seconds()/YEAR)
    ts = [t_by_year.get(year, []) for year in years]
    pyplot.plot(years, [numpy.median(t) for t in ts], linestyle=':', color=(1, 0.2, 0.2), marker='o', markersize=10, label='Median time to exit')
    pyplot.plot(years, [numpy.percentile(t, 5) for t in ts], linestyle=':', color=(1, 0.7, 0.7), markersize=10, label='5th percentile')
    pyplot.plot(years, [numpy.percentile(t, 95) for t in ts], linestyle=':', color=(1, 0.7, 0.7), markersize=10, label='95th percentile')

def get_grouped_data(group_years):
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
        if not years[0] <= seeded.year <= years[-1]:
            continue
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
    return groups, TE_by_group

    
# Plot cohort conversion rates
for with_confidence_interval, group_years, output_fn in [(False, False, 'cohort_plot_all_years.png'), (True, True, 'cohort_plot_grouped.png')]:
    with shared_plot_setup(y_fmt='%.0f%%',
                           x_label='Years after start',
                           y_label='Fraction of companies exited',
                           title='Fraction of companies exited by time after start',
                           legend_loc='upper left',
                           output_fn=output_fn,
                           xlim=[0, 5.2],
                           ylim=[0, 25]):
        groups, TE_by_group = get_grouped_data(group_years)
        colors = seaborn.color_palette('hls', len(groups))
        for group, color in zip(groups, colors):
            T, E = TE_by_group[group]
            group_max_t = min(t for t, e in zip(T, E) if not e)
            exits = sorted(t for t, e in zip(T, E) if e and t < group_max_t)
            ts = [0] + exits
            ks = numpy.arange(len(exits) + 1)
            pyplot.plot(ts, 100. * ks / len(T), label='Started in %s' % group, color=color)
            if with_confidence_interval:
                pyplot.fill_between(ts,
                                    100.*scipy.stats.beta.ppf(0.05, ks+1, len(T)-ks+1),
                                    100.*scipy.stats.beta.ppf(0.95, ks+1, len(T)-ks+1),
                                    color=color, alpha=0.2)

    
# Plot Kaplan-Meier estimate
for with_confidence_interval, group_years, output_fn in [(False, False, 'kaplan_meier_all_years.png'), (True, True, 'kaplan_meier_grouped.png')]:
    with shared_plot_setup(y_fmt='%.0f%%',
                           x_label='Years after start',
                           y_label='Fraction of companies exited',
                           title='Fraction of companies exited by time after start - Kaplan-Meier',
                           legend_loc='upper left',
                           output_fn=output_fn,
                           xlim=[0, 5.2],
                           ylim=[0, 25]):
        groups, TE_by_group = get_grouped_data(group_years)
        colors = seaborn.color_palette('hls', len(groups))
        for group, color in zip(groups, colors):
            # Compute Kaplan-Meier using lifelines
            T, E = TE_by_group[group]
            kmf = lifelines.KaplanMeierFitter()
            kmf.fit(T, event_observed=E)
            ts = kmf.survival_function_.index.values
            # max_i = bisect.bisect_left(ts, 5.0)
            ps = 1.0 - kmf.survival_function_['KM_estimate'].values
            ps_hi = 1.0 - kmf.confidence_interval_['KM_estimate_lower_0.95'].values
            ps_lo = 1.0 - kmf.confidence_interval_['KM_estimate_upper_0.95'].values
            pyplot.plot(ts, 100. * ps, label='Started in %s' % group, color=color)
            if with_confidence_interval:
                pyplot.fill_between(ts, 100. * ps_lo, 100. * ps_hi, color=color, alpha=0.2)

            continue
            # Compute it manually
            te = sorted(zip(*TE_by_group[group]))
            n, k = len(te), 0
            ts, ys = [], []
            p = 1.0
            for t, e in te:
                if e:
                   p *= (n-1) / n
                n -= 1
                ts.append(t)
                ys.append(100. * (1-p))
            pyplot.plot(ts, ys, 'b')
