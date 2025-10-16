#
#  This file is part of Sequana software
#
#  Copyright (c) 2016-2022 - Sequana Development Team
#
#  Distributed under the terms of the 3-clause BSD license.
#  The full license is in the LICENSE file, distributed with this software.
#
#  website: https://github.com/sequana/sequana
#  documentation: http://sequana.readthedocs.io
#
##############################################################################

import os
import re
from pathlib import Path

import colorlog

from sequana.lazy import numpy as np
from sequana.lazy import pandas as pd
from sequana.lazy import pylab
from sequana.rnadiff import RNADiffTable

logger = colorlog.getLogger(__name__)


__all__ = ["RNADiffCompare"]


class Compare:
    def __init__(self):
        pass


class RNADiffCompare(Compare):
    """An object representation of results coming from a RNADiff analysis.

    ::

        from sequana.compare import RNADiffCompare
        c = RNADiffCompare("data.csv", "data2.csv")

        # change the l2fc to update venn plots
        c.plot_venn_up()
        c.r1.log2_fc = 1
        c.r2.log2_fc = 1
        c.plot_venn_up()

    """

    def __init__(self, *args, design=None):
        self.rns = []
        for rnadiff_csv in args:
            if isinstance(rnadiff_csv, RNADiffTable):
                self.rns.append(rnadiff_csv)
            elif os.path.exists(rnadiff_csv):
                self.rns.append(RNADiffTable(rnadiff_csv))
            else:
                raise NotImplementedError

        # aliases
        self.r1 = self.rns[0]
        self.r2 = self.rns[1]

        # keep only entries in common
        A = self.r1.df.index
        B = self.r2.df.index
        common = set(A).intersection(B)

        if len(A) != len(B):
            self.r1.df = self.r1.df.loc[list(common)]
            self.r2.df = self.r2.df.loc[list(common)]
            self.r1.filt_df = self.r1.filter()
            self.r2.filt_df = self.r2.filter()
            self.r1.set_gene_lists()
            self.r2.set_gene_lists()
            logger.info(f"Two sets are not equal. Kept {len(self.r1.df)} in common")

    def plot_venn_down(self, labels=None, ax=None, title="Down expressed genes", mode="all", l2fc=0):
        assert l2fc <= 0, "l2fc must be negative"
        kargs = {}
        kargs["title"] = title
        kargs["labels"] = labels
        kargs["ax"] = ax
        kargs["data1"] = set(self.r1.gene_lists["down"])
        kargs["data2"] = set(self.r2.gene_lists["down"])
        self._venn(**kargs)

    def plot_venn_up(self, labels=None, ax=None, title="Up expressed genes", mode="all", l2fc=0):
        """Venn diagram of cond1 from RNADiff result1 vs cond2 in RNADiff
        result 2

        .. plot::
            :include-source:

            from sequana import sequana_data
            from sequana.compare import RNADiffCompare

            c = RNADiffCompare(
                sequana_data("rnadiff_salmon.csv", "doc/rnadiff_compare"),
                sequana_data("rnadiff_bowtie.csv", "doc/rnadiff_compare")
            )
            c.plot_venn_up()
        """
        assert l2fc >= 0, "l2fc must be positive"
        kargs = {}
        kargs["title"] = title
        kargs["labels"] = labels
        kargs["ax"] = ax
        kargs["data1"] = set(self.r1.gene_lists["up"])
        kargs["data2"] = set(self.r2.gene_lists["up"])
        self._venn(**kargs)

    def _venn(self, data1, data2, labels=None, ax=None, title="expressed genes"):
        from sequana.viz.venn import plot_venn

        if labels is None:
            labels = ["A", "B"]

        plot_venn([data1, data2], labels=labels, ax=ax, title=title)

    def plot_venn_all(self, labels=None, ax=None, title="all expressed genes", mode="all"):
        kargs = {}
        kargs["title"] = title
        kargs["labels"] = labels
        kargs["ax"] = ax
        kargs["data1"] = set(self.r1.gene_lists["all"])
        kargs["data2"] = set(self.r2.gene_lists["all"])
        self._venn(**kargs)

    def plot_corrplot_counts_raw(self, samples=None, log2=True, lower="pie", upper="text"):
        from sequana.viz import corrplot

        if samples is None:
            samples = self.r1.counts_raw.columns
        df1 = self.r1.counts_raw[samples]
        df2 = self.r2.counts_raw[samples]
        df = pd.concat([df1, df2], keys=["r1", "r2"], axis=1)
        if log2:
            df = pylab.log2(df)
        c = corrplot.Corrplot(df).plot(upper=upper, lower=lower)
        return df.corr()

    def plot_corrplot_counts_normed(self, samples=None, log2=True, lower="pie", upper="text"):
        from sequana.viz import corrplot

        if samples is None:
            samples = self.r1.counts_raw.columns
        df1 = self.r1.counts_norm[samples]
        df2 = self.r2.counts_norm[samples]
        df = pd.concat([df1, df2], keys=["r1", "r2"], axis=1)
        if log2:
            df = pylab.log2(df)
        c = corrplot.Corrplot(df).plot(upper=upper, lower=lower)
        return df.corr()

    def plot_jaccard_distance(
        self,
        mode,
        padjs=[0.0001, 0.001, 0.01, 0.05, 0.1],
        Nfc=50,
        smooth=False,
        window=5,
    ):
        assert mode in ["down", "up", "all"]
        pylab.clf()

        if mode == "down":
            m1 = self.r1.df.log2FoldChange.min()
            m2 = self.r2.df.log2FoldChange.min()
            minimum = min(m1, m2)
            print(m1, m2)
            X = pylab.linspace(0, minimum, Nfc)
        elif mode == "up":
            m1 = self.r1.df.log2FoldChange.max()
            m2 = self.r2.df.log2FoldChange.max()
            maximum = max(m1, m2)
            X = pylab.linspace(0, maximum, Nfc)
        else:
            minmax1 = self.r1.df.log2FoldChange.abs().max()
            minmax2 = self.r2.df.log2FoldChange.abs().max()
            maximum = max(minmax1, minmax2)
            X = pylab.linspace(0, maximum, Nfc)

        common = {}
        for padj in padjs:
            I = []
            common[padj] = []
            for x in X:
                if mode == "down":
                    # less than a given fold change that is negative
                    A = set(self.r1.df.query("log2FoldChange<=@x and padj<@padj").index)
                    B = set(self.r2.df.query("log2FoldChange<=@x and padj<@padj").index)
                elif mode == "up":
                    # greater than a given fold change that is positive
                    A = set(self.r1.df.query("log2FoldChange>=@x and padj<@padj").index)
                    B = set(self.r2.df.query("log2FoldChange>=@x and padj<@padj").index)
                else:
                    A = set(self.r1.df.query("(log2FoldChange>=@x or log2FoldChange<=-@x) and padj<@padj").index)
                    B = set(self.r2.df.query("(log2FoldChange>=@x or log2FoldChange<=-@x) and padj<@padj").index)
                if len(A) == 0 or len(B) == 0:
                    # no overlap yet
                    I.append(0)
                else:
                    res = len(A.intersection(B)) / (len(A) + len(B) - len(A.intersection(B))) * 100
                    I.append(res)
                common[padj].append(len(A.intersection(B)))

            try:
                if smooth:
                    I = pd.Series(I).rolling(window).median().values
                else:
                    assert False
            except:
                pass
            pylab.plot(X, I, "o-", label=str(padj))

        ax = pylab.gca()
        ax.set_ylabel("Jaccard similarity (intersection/union)")
        ax.set_xlabel("Fold change (log2)")
        ax2 = ax.twinx()
        for padj in padjs:
            ax2.plot(X, common[padj], ls="--")
        ax2.set_ylabel("Cardinality of the union ")
        ax.legend()
        ax.set_ylim([0, 100])
        # ax2.set_ylim([0,100])
        if mode == "down":
            ax.axvline(-2, ls="--", color="r")
        else:
            ax.axvline(2, ls="--", color="r")

        return I, common[padj]

    def plot_common_major_counts(
        self,
        mode,
        labels=None,
        switch_up_down_cond2=False,
        add_venn=True,
        xmax=None,
        title="",
        fontsize=12,
        sortby="log2FoldChange",
    ):
        """

        :param mode: down, up or all


        .. plot::
            :include-source:

            from sequana import sequana_data
            from sequana.compare import RNADiffCompare

            c = RNADiffCompare(
                sequana_data("rnadiff_salmon.csv", "doc/rnadiff_compare"),
                sequana_data("rnadiff_bowtie.csv", "doc/rnadiff_compare")
            )
            c.plot_common_major_counts("down")
        """
        # cond1, cond2 = self._get_cond1_cond2()
        if labels is None:
            labels = ["r1", "r2"]

        if mode in ["down"]:
            # Negative values !
            gl1 = list(set(self.r1.gene_lists["down"]))
            gl2 = list(set(self.r2.gene_lists["down"]))
            A = self.r1.df.loc[gl1].sort_values(by=sortby)
            B = self.r2.df.loc[gl1].sort_values(by=sortby)
        else:
            gl1 = list(set(self.r1.gene_lists[mode]))
            gl2 = list(set(self.r2.gene_lists[mode]))
            A = self.r1.df.loc[gl1].sort_values(by=sortby, ascending=False)
            B = self.r2.df.loc[gl1].sort_values(by=sortby, ascending=False)
        # sometimes, up and down may be inverted as compared to the other
        # conditions

        N = []
        for i in range(1, max(len(A), len(B))):
            a = A.iloc[0:i].index
            b = B.iloc[0:i].index
            n = len(set(b).intersection(set(a)))
            N.append(n / i * 100)

        max_common = len(set(A.index).intersection(set(B.index)))
        pylab.clf()
        if len(A) > len(B):
            pylab.axhline(
                max_common / len(A) * 100,
                color="r",
                ls="--",
                label="min set intersection",
            )
            pylab.axvline(len(B), ls="--", color="k", label="rank of minor set")
        else:
            pylab.axhline(max_common / len(B) * 100, color="r", ls="--", label="min set intersect")
            pylab.axvline(len(A), ls="--", color="k", label="rank of minor set")

        pylab.plot(N)
        pylab.xlabel("rank", fontsize=fontsize)
        pylab.ylabel("% common features", fontsize=fontsize)
        pylab.grid(True)
        pylab.ylim([0, 100])
        if xmax:
            pylab.xlim([0, xmax])
        else:
            pylab.xlim([0, max(len(A), len(B))])
        pylab.title(title, fontsize=fontsize)
        ax = pylab.gca()
        ax2 = ax.twinx()
        ax2.plot(A[sortby].values, "orange", label=sortby)
        ax2.set_ylabel(sortby)
        pylab.legend(loc="lower left")
        ax.legend(loc="lower right")

        if add_venn:
            f = pylab.gcf()
            ax = f.add_axes([0.5, 0.5, 0.35, 0.35], facecolor="grey")
            if mode == "down":
                self.plot_venn_down(ax=ax, title=None, labels=labels, mode="two_only")
            elif mode == "up":
                self.plot_venn_up(ax=ax, title=None, labels=labels, mode="two_only")
            elif mode == "all":
                self.plot_venn_all(ax=ax, title=None, labels=labels, mode="two_only")

    def plot_foldchange(self):
        mode = "all"

        # it may happen that list are not identical due to salmon and bowtie not
        # using same input gff for instance.
        X = self.r1.df.index
        Y = self.r2.df.index
        common = list(set(X).intersection(set(Y)))

        A = self.r1.df.loc[self.r1.gene_lists[mode]]
        B = self.r2.df.loc[self.r2.gene_lists[mode]]
        # cast set to list to avoid future error in pandas (june 2022)
        AB = list(set(A.index).intersection(set(B.index)))
        Ao = A.loc[list(set(A.index).difference(set(B.index)))]
        Bo = B.loc[list(set(B.index).difference(set(A.index)))]
        Ac = A.loc[AB]
        Bc = B.loc[AB]

        pylab.plot(
            self.r1.df.loc[common].log2FoldChange,
            self.r2.df.loc[common].log2FoldChange,
            "ko",
            alpha=0.5,
            markersize=1,
        )
        pylab.plot(Ac.log2FoldChange, Bc.log2FoldChange, "or", alpha=0.5)
        pylab.plot(Ao.log2FoldChange, self.r2.df.loc[Ao.index].log2FoldChange, "*b", alpha=0.5)
        pylab.plot(
            Bo.log2FoldChange,
            self.r1.df.loc[Bo.index].log2FoldChange,
            color="cyan",
            marker="o",
            lw=0,
            alpha=0.5,
        )

    def plot_volcano_differences(self, mode="all"):
        cond1, cond2 = "cond1", "cond2"
        labels = [cond1, cond2]

        A = self.r1.df.loc[self.r1.gene_lists[mode]]
        B = self.r2.df.loc[self.r2.gene_lists[mode]]
        # cast set to list to avoid future error in pandas (june 2022)
        AB = list(set(A.index).intersection(set(B.index)))
        Aonly = A.loc[list(set(A.index).difference(set(B.index)))]
        Bonly = B.loc[list(set(B.index).difference(set(A.index)))]
        Acommon = A.loc[AB]
        Bcommon = B.loc[AB]

        pylab.clf()
        pylab.plot(
            Acommon.log2FoldChange,
            -np.log10(Acommon.padj),
            marker="o",
            alpha=0.5,
            color="r",
            lw=0,
            label="Common in experiment 1",
            pickradius=4,
            picker=True,
        )
        pylab.plot(
            Bcommon.log2FoldChange,
            -np.log10(Bcommon.padj),
            marker="o",
            alpha=0.5,
            color="orange",
            lw=0,
            label="Common in experiment 2",
            pickradius=4,
            picker=True,
        )

        for x in AB:
            a_l = A.loc[x].log2FoldChange
            a_p = -np.log10(A.loc[x].padj)
            b_l = B.loc[x].log2FoldChange
            b_p = -np.log10(B.loc[x].padj)
            pylab.plot([a_l, b_l], [a_p, b_p], "k", alpha=0.5)

        pylab.plot(
            Bonly.log2FoldChange,
            -np.log10(Bonly.padj),
            marker="*",
            alpha=0.5,
            color="blue",
            lw=0,
            label="In experiment 2 only",
            pickradius=4,
            picker=True,
        )
        pylab.plot(
            Aonly.log2FoldChange,
            -np.log10(Aonly.padj),
            marker="*",
            alpha=0.5,
            color="cyan",
            lw=0,
            label="In experiment 1 only",
            pickradius=4,
            picker=True,
        )

        for name, x in Bonly.iterrows():
            x1 = x.log2FoldChange
            y1 = -np.log10(x.padj)
            x2 = self.r1.df.loc[name].log2FoldChange
            y2 = -np.log10(self.r1.df.loc[name].padj)
            pylab.plot([x1, x2], [y1, y2], ls="--", color="r")
        for name, x in Aonly.iterrows():
            x1 = x.log2FoldChange
            y1 = -np.log10(x.padj)
            x2 = self.r2.df.loc[name].log2FoldChange
            y2 = -np.log10(self.r2.df.loc[name].padj)
            pylab.plot([x1, x2], [y1, y2], ls="-", color="r")

        pylab.axhline(1.33, alpha=0.5, ls="--", color="r")

        pylab.xlabel("log2 fold Change")
        pylab.ylabel("log10 adjusted p-values")
        pylab.legend()
        pylab.grid(True)

        return Aonly, Bonly, Acommon, Bcommon

    def plot_volcano(self, labels=None):
        """Volcano plot of log2 fold change versus log10 of adjusted p-value

        .. plot::
            :include-source:

            from sequana import sequana_data
            from sequana.compare import RNADiffCompare

            c = RNADiffCompare(
                sequana_data("rnadiff_salmon.csv", "doc/rnadiff_compare"),
                sequana_data("rnadiff_bowtie.csv", "doc/rnadiff_compare")
            )
            c.plot_volcano()
        """
        cond1, cond2 = "cond1", "cond2"
        if labels is None:
            labels = [cond1, cond2]

        A = self.r1.df.loc[self.r1.gene_lists["all"]]
        B = self.r2.df.loc[self.r2.gene_lists["all"]]

        if cond1 == cond2:
            cond1 += "(1)"
            cond2 += "(2)"

        pylab.clf()
        pylab.plot(
            A.log2FoldChange,
            -np.log10(A.padj),
            marker="o",
            alpha=0.5,
            color="r",
            lw=0,
            label=labels[0],
            pickradius=4,
            picker=True,
        )
        pylab.plot(
            B.log2FoldChange,
            -np.log10(B.padj),
            marker="x",
            alpha=0.5,
            color="k",
            lw=0,
            label=labels[1],
            pickradius=4,
            picker=True,
        )

        genes = list(A.index) + list(B.index)
        pylab.grid(True)
        pylab.xlabel("fold change")
        pylab.ylabel("log10 adjusted p-value")
        pylab.legend(loc="lower right")
        ax = pylab.gca()

        def onpick(event):
            thisline = event.artist
            self.event = event
            label = thisline.get_label()
            if label == cond1:
                gene_name = A.index[event.ind[0]]
                x1 = round(A.loc[gene_name].log2FoldChange, 1)
                y1 = round(-np.log10(A.loc[gene_name].padj), 1)
                try:
                    x2 = round(B.loc[gene_name].log2FoldChange, 1)
                    y2 = round(-np.log10(B.loc[gene_name].padj), 1)
                except:
                    x2, y2 = None, None
            else:
                gene_name = B.index[event.ind[0]]
                x1 = round(B.loc[gene_name].log2FoldChange, 1)
                y1 = round(-np.log10(B.loc[gene_name].padj), 1)
                try:
                    x2 = round(A.loc[gene_name].log2FoldChange, 1)
                    y2 = round(-np.log10(A.loc[gene_name].padj), 1)
                except:
                    x2, y2 = None, None

            try:
                if x2 is None:
                    ax.title.set_text("{} at pos [{},{}]".format(gene_name, x1, y1))
                else:
                    ax.title.set_text("{} at pos [{},{}] and [{},{}]".format(gene_name, x1, y1, x2, y2))
            except:
                print("exception")
                ax.title.set_text("")
            pylab.draw()

        fig = pylab.gcf()
        fig.canvas.mpl_connect("pick_event", onpick)

    def plot_geneset(
        self,
        indices,
        showlines=True,
        showdots=True,
        colors={
            "bodies": "blue",
            "cbars": "k",
            "dot": "blue",
            "cmins": "k",
            "cmaxes": "k",
        },
    ):
        """indices is a list that represents a gene sets


        cmins, cmaxes, cbars are the colors of the bars inside the body of the violin plots


        .. plot::

            from sequana import sequana_data
            from sequana.compare import RNADiffCompare

            c = RNADiffCompare(
                sequana_data("rnadiff_salmon.csv", "doc/rnadiff_compare"),
                sequana_data("rnadiff_bowtie.csv", "doc/rnadiff_compare")
            )
            c.plot_volcano()
            indices = c.r1.df.query("log2FoldChange>1 or log2FoldChange<-1").index.values
            indices  = [x for x in indices if x in c.r1.df.index and x in c.r2.df.index]
            c.plot_geneset(indices, showlines=True)

        """
        from matplotlib.pyplot import violinplot
        from pylab import axhline, clf, plot, violinplot, xticks, ylabel

        N = len(self.rns)
        data = [self.rns[i].df.loc[indices]["log2FoldChange"].values for i in range(0, N)]

        clf()
        axhline(0, color="k", ls="--", zorder=-1)
        vp = violinplot(data)
        for x in vp["bodies"]:
            x.set_color(colors["bodies"])
        vp["cbars"].set_color(colors["cbars"])
        vp["cmins"].set_color(colors["cmins"])
        vp["cmaxes"].set_color(colors["cmaxes"])

        for i in range(N - 1):
            for x, y in zip(data[i], data[i + 1]):
                if showlines:
                    plot([i + 1, i + 2], [x, y], "or-", alpha=0.5)
                else:
                    plot([i + 1, i + 2], [x, y], "or", alpha=0.5)

        xticks(range(1, N + 1), [f"C{i}" for i in range(1, N + 1)], fontsize=16)
        ylabel("log2 Fold Change", fontsize=16)

        return data
