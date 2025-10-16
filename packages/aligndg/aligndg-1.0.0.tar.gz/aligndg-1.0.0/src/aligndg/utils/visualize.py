import random
import math
from typing import List, Mapping, Optional, Union

import scanpy as sc
import numpy as np
import pandas as pd
from anndata import AnnData

import matplotlib.pyplot as plt
import plotly.graph_objects as go
from aligndg.utils.color import *


def get_color(n=1, cmap: str = 'scanpy', seed: int = 42):
    if cmap == 'scanpy' and n <= 10:
        step = 10 // n
        return vega_10_scanpy[:: step][: n]
    elif cmap == 'scanpy' and n <= 20:
        step = 20 // n
        return vega_20_scanpy[:: step][: n]
    elif cmap == 'scanpy' and n <= 28:
        step = 28 // n
        return zeileis_28[:: step][: n]
    elif cmap == 'scanpy' and n <= 102:
        step = 102 // n
        return godsnot_102[:: step][: n]
    else:
        print('WARNING: Using random color!')
        random.seed(seed)
        if n == 1:
            return '#' + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
        elif n > 1:
            return ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)]) for i in range(n)]


class Build3D:
    def __init__(self, dataset_A: pd.DataFrame,
                 dataset_B: pd.DataFrame,
                 matching: np.ndarray,
                 meta: Optional[str] = None,
                 expr: Optional[str] = None,
                 subsample_size: Optional[int] = 300,
                 reliability: Optional[np.ndarray] = None,
                 scale_coordinate: Optional[bool] = True,
                 rotate: Optional[List[str]] = None,
                 exchange_xy: Optional[bool] = False,
                 subset: Optional[List[int]] = None
                 ) -> None:
        self.dataset_A = dataset_A.copy()
        self.dataset_B = dataset_B.copy()
        self.meta = meta
        self.matching = matching
        self.conf = reliability
        self.subset = subset  # index of query cells to be plotted
        scale_coordinate = True if rotate != None else scale_coordinate

        assert all(item in dataset_A.columns.values for item in ['index', 'x', 'y'])
        assert all(item in dataset_B.columns.values for item in ['index', 'x', 'y'])

        if meta:
            set1 = list(set(self.dataset_A[meta]))
            set2 = list(set(self.dataset_B[meta]))
            self.celltypes = set1 + [x for x in set2 if x not in set1]
            self.celltypes.sort()  # make sure celltypes are in the same order
            overlap = [x for x in set2 if x in set1]
            print(f"dataset1: {len(set1)} cell types; dataset2: {len(set2)} cell types; \n\
                    Total :{len(self.celltypes)} celltypes; Overlap: {len(overlap)} cell types \n\
                    Not overlap :[{[y for y in (set1 + set2) if y not in overlap]}]"
                  )
        self.expr = expr if expr else False

        if scale_coordinate:
            for i, dataset in enumerate([self.dataset_A, self.dataset_B]):
                for axis in ['x', 'y']:
                    dataset[axis] = (dataset[axis] - np.min(dataset[axis])) / (
                            np.max(dataset[axis]) - np.min(dataset[axis]))
                    if rotate == None:
                        pass
                    elif axis in rotate[i]:
                        dataset[axis] = 1 - dataset[axis]
        if exchange_xy:
            self.dataset_B[['x', 'y']] = self.dataset_B[['y', 'x']]

        if not subset is None:
            matching = matching[:, subset]
        if matching.shape[1] > subsample_size and subsample_size > 0:
            self.matching = matching[:, np.random.choice(matching.shape[1], subsample_size, replace=False)]
        else:
            subsample_size = matching.shape[1]
            self.matching = matching
        print(f'Subsampled {subsample_size} pairs from {matching.shape[1]}')

        self.datasets = [self.dataset_A, self.dataset_B]

    def draw_3D(self,
                size: Optional[List[int]] = [10, 10],
                conf_cutoff: Optional[float] = 0,
                point_size: Optional[List[int]] = [0.1, 0.1],
                line_width: Optional[float] = 0.3,
                line_color: Optional[str] = 'grey',
                line_alpha: Optional[float] = 0.7,
                hide_axis: Optional[bool] = False,
                show_error: Optional[bool] = True,
                show_celltype: Optional[bool] = False,
                cmap: Optional[bool] = 'Reds',
                save: Optional[str] = None
                ) -> None:

        self.conf_cutoff = conf_cutoff
        show_error = show_error if self.meta else False
        fig = plt.figure(figsize=(size[0], size[1]))
        ax = fig.add_subplot(111, projection='3d')
        # color by meta
        if self.meta:
            color = get_color(len(self.celltypes))
            c_map = {}
            for i, celltype in enumerate(self.celltypes):
                c_map[celltype] = color[i]
            if self.expr:
                c_map = cmap
                # expr_concat = pd.concat(self.datasets)[self.expr].to_numpy()
                # norm = plt.Normalize(expr_concat.min(), expr_concat.max())
            for i, dataset in enumerate(self.datasets):
                if self.expr:
                    norm = plt.Normalize(dataset[self.expr].to_numpy().min(), dataset[self.expr].to_numpy().max())
                for cell_type in self.celltypes:
                    slice = dataset[dataset[self.meta] == cell_type]
                    xs = slice['x']
                    ys = slice['y']
                    zs = i
                    if self.expr:
                        ax.scatter(xs, ys, zs, s=point_size[i], c=slice[self.expr], cmap=c_map, norm=norm)
                    else:
                        ax.scatter(xs, ys, zs, s=point_size[i], c=c_map[cell_type])
        # plot points without meta
        else:
            for i, dataset in enumerate(self.datasets):
                xs = dataset['x']
                ys = dataset['y']
                zs = i
                ax.scatter(xs, ys, zs, s=point_size[i])
        # plot line
        self.c_map = c_map
        self.draw_lines(ax, show_error, show_celltype, line_color, line_width, line_alpha)
        if hide_axis:
            plt.axis('off')
        if save != None:
            plt.savefig(save, dpi=800, bbox_inches='tight')
        else:
            plt.show()

    def draw_lines(self, ax, show_error, show_celltype, line_color, line_width=0.3, line_alpha=0.7) -> None:
        r"""
        Draw lines between paired cells in two datasets
        """
        for i in range(self.matching.shape[1]):
            if not self.conf is None and self.conf[i] < self.conf_cutoff:
                continue
            pair = self.matching[:, i]
            default_color = line_color
            if self.meta != None:
                celltype1 = self.dataset_A.loc[self.dataset_A['index'] == pair[1], self.meta].astype(str).values[0]
                celltype2 = self.dataset_B.loc[self.dataset_B['index'] == pair[0], self.meta].astype(str).values[0]
                if show_error:
                    if celltype1 == celltype2:
                        color = '#ade8f4'  # blue
                    else:
                        color = '#ffafcc'  # red
                if show_celltype:
                    if celltype1 == celltype2:
                        color = self.c_map[celltype1]
                    else:
                        color = '#696969'  # celltype1 error match color
            point0 = np.append(self.dataset_A[self.dataset_A['index'] == pair[1]][['x', 'y']], 0)
            point1 = np.append(self.dataset_B[self.dataset_B['index'] == pair[0]][['x', 'y']], 1)

            coord = np.row_stack((point0, point1))
            color = color if show_error or show_celltype else default_color
            ax.plot(coord[:, 0], coord[:, 1], coord[:, 2], color=color, linestyle="dashed", linewidth=line_width,
                    alpha=line_alpha)
