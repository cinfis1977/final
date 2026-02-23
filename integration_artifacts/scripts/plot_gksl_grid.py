"""Plot differences between GKSL and phase-shift from out/gksl_grid.csv
Usage: python scripts/plot_gksl_grid.py --in out/gksl_grid.csv --out out/gksl_grid_plot.png
"""
import argparse
import pandas as pd
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument('--in', dest='infile', default='out/gksl_grid.csv')
ap.add_argument('--out', dest='outfile', default='out/gksl_grid_plot.png')
args = ap.parse_args()

df = pd.read_csv(args.infile)

df['diff'] = df['P_gksl'] - df['P_phase']

fig, ax = plt.subplots(figsize=(6,4))
for gamma, gdf in df.groupby('gamma'):
    ax.plot(gdf['A'], gdf['diff'], marker='o', label=f'gamma={gamma}')
ax.set_xscale('log')
ax.set_xlabel('A')
ax.set_ylabel('P_gksl - P_phase')
ax.legend()
fig.tight_layout()
fig.savefig(args.outfile)
print('Wrote', args.outfile)
