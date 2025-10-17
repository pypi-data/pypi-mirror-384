#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import json
import numpy as np
from scipy.interpolate import PchipInterpolator


class CurvedLaneRegion:
    VERSION = 1

    @staticmethod
    def deserialize(nodes: str):
        region = None
        nodes = json.loads(nodes)
        if isinstance(nodes, list):
            x, y, h, w = nodes
            region = dict(nodes=[[x + w / 2, y], [x + w / 2, y + h]], width=w, version=1)

        elif isinstance(nodes, dict):
            if nodes["version"] <= 1:
                # Ensuring that y coordinates are increasing order if for some reason it's saved differently in the DB
                a = np.array(nodes["nodes"])
                sort_indexes = np.argsort(a, axis=0)[:, 1]
                nodes["nodes"] = np.vstack(
                    [a[:, 0][sort_indexes], a[:, 1][sort_indexes]]
                ).T.tolist()
                region = nodes

        return CurvedLaneRegion(region=region)

    def __init__(self, region=None, nodes=None, width=None):
        if region is None:
            if nodes is None or width is None:
                raise ValueError("Provide either region or nodes and width")
            self.region = dict(nodes=nodes, width=width)
        else:
            self.region = region

        if len(self.nodes) < 2:
            raise ValueError("Provide at least 2 nodes")

        self.spline = None
        self._init_spline()

    @property
    def nodes_xy(self):
        """
        Returns nodes as to separate list of x and y
        """
        x, y = np.array(self.nodes).T
        return x, y

    @property
    def nodes(self):
        """
        Returns nodes as a list of [[x0, y0], ..., [xn, yn]]
        """
        return self.region["nodes"]

    @property
    def width(self):
        return self.region["width"]

    @nodes.setter
    def nodes(self, xy):
        self.region["nodes"] = np.vstack([*xy]).T.tolist()
        self._init_spline()

    @width.setter
    def width(self, width):
        self.region["width"] = width

    def get_coordinates(self):
        x, y = self.nodes_xy
        if len(x) > 0:
            return x[0], y[0]
        return 0, 0

    def calculate_intensities(self, image) -> np.array:
        _, _y = self.nodes_xy
        halfwidth = int(np.round(self.width / 2))
        spl = self.spline
        y = np.arange(max(0, np.ceil(_y[0])), min(np.ceil(_y[-1]), image.shape[0])).astype(int)
        x = np.round(spl(y)).astype(int)

        intensities = np.zeros(image.shape[0])
        for i, j in zip(x, y):
            i0 = max(i - halfwidth, 0)
            i1 = min(i + halfwidth, image.shape[1])
            row = image[j, i0:i1]
            intensities[j] = np.sum(row)

        return intensities

    def serialize(self) -> str:
        region = {
            "nodes": self.nodes,
            "width": self.width,
            "version": self.VERSION,
            "type": CurvedLaneRegion.__name__,
        }
        return json.dumps(region)

    def offset(self, offset_x, offset_y):
        delta = np.array([offset_x, offset_y])
        nodes = self.nodes + delta
        self.nodes = nodes[:, 0], nodes[:, 1]

    def _init_spline(self):
        x, y = self.nodes_xy
        try:
            self.spline = PchipInterpolator(y, x)
        except ValueError:
            pass
