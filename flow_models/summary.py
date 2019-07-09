#!/usr/bin/python3
import argparse
import pathlib

import numpy as np
import pandas as pd
import scipy.interpolate

from .lib.data import UNITS, detect_x_value
from .lib.util import logmsg

X_VALUES = ['length', 'size', 'duration', 'rate']
Y_VALUES = ['flows', 'packets', 'octets']

def summary(obj, x_val=None):
    if isinstance(obj, (str, pathlib.Path)):
        file = pathlib.Path(obj)
        logmsg(f'Loading file {file}')
        data = pd.read_csv(file, index_col=0, sep=',', low_memory=False,
                           usecols=lambda col: not col.endswith('_ssq'))
        logmsg(f'Loaded file {file}')
    else:
        data = obj

    print(stats_summary(data))
    print('\n')
    print(cdf_summary(data, x_val))
    print('\n')

def stats_summary(data):
    if isinstance(data, pd.DataFrame):
        s = ['\\begin{tabular}{lrr}',
             '\\toprule',
             '\\textbf{Dataset name} & XXX & \\\\',
             '\\textbf{Exporter} & XXX & \\\\',
             '\\textbf{L2 technology} & Ethernet & \\\\',
             '\\textbf{Sampling rate} & none & \\\\',
             '\\textbf{Active timeout} & 300 & seconds \\\\',
             '\\textbf{Inactive timeout} & 15 & seconds \\\\',
             '\\midrule']
        for what in Y_VALUES:
            col = what + '_sum'
            if col in data:
                tot = data[col].sum()
                s.append('\\textbf{Number of %s} & ' % what + '{:,}'.format(tot).replace(',', ' ') + f' & {what} \\\\')
        for what in X_VALUES:
            col = UNITS[what]
            if col not in Y_VALUES:
                col = what
            col = col + '_sum'
            if col in data:
                tot = data[col].sum() / data['flows_sum'].sum()
                s.append('\\textbf{Average flow %s} & ' % what + '{:.6f}'.format(tot) + f' & {UNITS[what]} \\\\')
        tot = data['octets_sum'].sum() / data['packets_sum'].sum()
        s.append('\\textbf{Average packet size} & ' + '{:.6f}'.format(tot) + ' & bytes \\\\')
        s += ['\\bottomrule',
              '\\end{tabular}']
        return '\n'.join(s)

def cdf_summary(data, x_val):
    if isinstance(data, pd.DataFrame):
        if not x_val:
            x_val = detect_x_value(data.index)
        if x_val == 'length':
            points = [1, 2, 4, 8, 10, 100, 1000, 10000, 100000, 1000000]
        else:
            points = [64, 128, 256, 512, 1024, 1500, 4096, 10000, 100000, 1000000,
                      10000000, 100000000, 1000000000]
        vals = {}
        for what in Y_VALUES:
            cdf = data[what + '_sum'].cumsum() / data[what + '_sum'].sum()
            cdfi = scipy.interpolate.interp1d(cdf.index, cdf, 'linear', bounds_error=False)(np.array(points))
            vals[what] = cdfi * 100
        s = ['\\begin{tabular}{lrrr}',
             '\\toprule',
             '\\textbf{Flows of %s up to} & ' % x_val + '\\multicolumn{3}{c}{\\textbf{Make up \\%}} \\\\',
             '\\cmidrule(lr){2-4}',
             '\\multicolumn{1}{c}{(%s)} & ' % UNITS[x_val] + ' & '.join(Y_VALUES) + ' \\\\',
             '\\midrule']
        for n in range(len(points)):
            s.append(f'{points[n]} & ' + ' & '.join(f'{vals[what][n]:.4f}' for what in Y_VALUES) + ' \\\\')
        s += ['\\bottomrule',
              '\\end{tabular}']
        return '\n'.join(s)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--format', default='png', help='plot file format')
    parser.add_argument('--one', action='store_true', help='plot PDF and CDF in one file')
    parser.add_argument('-x', choices=X_VALUES, help='x axis value')
    parser.add_argument('file', help='csv_hist file to summarize')
    app_args = parser.parse_args()

    summary(app_args.file, app_args.x)


if __name__ == '__main__':
    main()
