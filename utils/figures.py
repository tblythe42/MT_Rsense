import os
from datetime import datetime as dt
import json
import numpy as np
from pandas import DataFrame, to_datetime
from matplotlib import pyplot as plt
from matplotlib.ticker import StrMethodFormatter

from hydrograph import read_hydrograph


def plot_hydrograph_years(csv, inst_q_dir, fig_dir, min_flow=400, long_name='Gage'):
    print('\n{}'.format(os.path.basename(csv)))
    df = read_hydrograph(csv)
    name = df.columns[0]
    df['date'] = df.index
    df['year'] = df.date.dt.year
    df['date'] = df.date.dt.strftime('%m-%d')
    df.index = [x for x in range(0, df.shape[0])]
    ydf = df.set_index(['year', 'date'])[name].unstack(-2)
    ydf.dropna(axis=1, how='all', inplace=True)
    ldf = ydf.copy()
    cols = ldf.columns
    s, e = '05-01', '10-31'
    mins = [(c, ldf[c][s: e].idxmin(), ldf[c][s: e].min()) for c in cols if ldf[c][s: e].min() < min_flow]
    ldf = ldf[[y[0] for y in mins]]
    ldf[ldf.values >= min_flow] = np.nan
    ldf = ldf.loc[s: e, :]
    periods = []
    unverified = []
    for k, v in ldf.items():
        d = DataFrame(v)
        d['ix'] = [x for x in range(0, d.shape[0])]
        d['lf'] = (d[k] < min_flow)
        d['crossing'] = (d.lf != d.lf.shift()).cumsum()
        d['count'] = d.groupby(['lf', 'crossing']).cumcount(ascending=True)
        d['rolling'] = d['lf'].rolling(5).sum()

        if d['rolling'].max() < 4:
            continue

        # d = d[d['lf'] == 1]

        missing = False
        inst_csv = os.path.join(inst_q_dir, '{}_{}.csv'.format(os.path.basename(csv).split('.')[0], k))
        try:
            iv = read_hydrograph(inst_csv)

            full_days = []

            for i, r in d.iterrows():
                day = iv.loc['{}-{}'.format(k, i): '{}-{}'.format(k, i)]
                if day.empty:
                    full_days.append(False)
                    missing = True
                else:
                    day = day.values
                    full_days.append(np.all(day < min_flow))

        except FileNotFoundError:
            missing = True

        summer_min = d[k].min()

        if missing:
            d = d[d['rolling'] > 4]
            lf_days = np.count_nonzero(d['lf'])
            unverified.append(k)
        else:
            d['lf_update'] = full_days
            d['crossing_update'] = (d.lf != d.lf.shift()).cumsum()
            d['count_update'] = d.groupby(['lf_update', 'crossing_update']).cumcount(ascending=True)
            lf_days = np.count_nonzero(d['lf_update'])
            d = d[(d['count_update'] >= 4) & (d['lf_update'] == 1)]
            if d.empty:
                continue

        window = k, d.index[0], lf_days, summer_min
        periods.append(window)

    ydf['hline'] = [min_flow for _ in ydf.index]
    colors = ['k' if _ != 'hline' else 'r' for _ in ydf.columns]
    ax = ydf.plot(logy=True, legend=False, alpha=0.2, color=colors, ylabel='discharge [cfs]',
                  title='{}: {}\n'
                        '1985 - 2020'.format(long_name, name.split(':')[1]), figsize=(30, 10))
    ax.yaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))
    head = ['Call Date, Days < IFR, Min']
    ann = head + [('{}-{},   {},  {:.0f} cfs'.format(p[1], p[0], p[2], p[3])) for p in periods]
    txt = '\n'.join(ann)
    props = dict(boxstyle='round', facecolor='white', alpha=1)

    ax.text(1, 1, txt, transform=ax.transAxes, fontsize=12,
            horizontalalignment='right', verticalalignment='top', bbox=props)

    ax.annotate('{} cfs'.format(min_flow), xy=(100, min_flow + 10), xycoords='data', color='r')
    plt.savefig(os.path.join(fig_dir, 'stacked_{}'.format(name.split(':')[1])))
    plt.close()

    jsn = os.path.join(fig_dir, '{}_lf.json'.format(os.path.basename(csv).replace('.csv', '')))
    d = {}
    for y, dm, lf, minflow in periods:
        dstr = '{}-{}'.format(y, dm)
        dt = to_datetime(dstr)
        doy = dt.dayofyear
        d[str(y)] = {'date': dstr,
                     'doy': doy,
                     'min_flow': minflow,
                     'low_flow_days': lf}
    with open(jsn, 'w') as f:
        json.dump(d, f)

    [print(x[0]) for x in periods]

    print('{} lf years, {} gage years, {} unverified\n'.format(len(periods), len(ldf.columns),
                                                               len(unverified)))


if __name__ == '__main__':

    d = {'12334550': (500, 'Clark Fork at Turah Bridge nr Bonner MT'),  # I can't quite believe some of these numbers
         '06052500': (947, 'Gallatin River at Logan MT'),
         '06076690': (150, 'Smith River near Ft Logan MT'),
         '06195600': (945, 'Shields River nr Livingston MT'),
         '12340000': (700, 'Blackfoot River near Bonner MT')}

    root = '/media/research/IrrigationGIS/Montana/water_rights/hydrographs'
    for k, v in d.items():
        try:
            gage = os.path.join(root, k)
            insta = os.path.join(gage, 'insta_q')
            h = os.path.join(gage, '{}.csv'.format(k))
            plot_hydrograph_years(h, insta, gage, min_flow=v[0], long_name=v[1])
        except Exception as e:
            print(k, e)
# ========================= EOF ====================================================================
