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
import subprocess
import sys
from itertools import combinations
from pathlib import Path

import colorlog
from easydev import AttrDict
from jinja2 import Environment, PackageLoader

from sequana.featurecounts import FeatureCount
from sequana.gff3 import GFF3
from sequana.lazy import numpy as np
from sequana.lazy import pandas as pd
from sequana.lazy import pylab

logger = colorlog.getLogger(__name__)


__all__ = ["RNADiffAnalysis", "RNADiffResults", "RNADiffTable", "RNADesign"]


class RNADesign:
    """Simple RNA design handler"""

    def __init__(self, filename, sep=r"\s*,\s*", condition_col="condition", reference=None):
        self.filename = filename
        self.condition_col = condition_col
        # \s to strip the white spaces
        self.df = pd.read_csv(filename, sep=sep, engine="python", comment="#", dtype=str)
        self.reference = reference

    def checker(self):
        from sequana.utils.checker import Checker

        c = Checker()
        c.tryme(self._check_condition)
        c.tryme(self._check_condition_col_name)
        c.tryme(self._check_label_col_name)
        c.tryme(self._check_label_uniqueness)
        return c.results

    def validate(self):
        checks = self.checker()
        # Stop after first error
        for check in checks:
            if check["status"] == "Error":
                sys.exit("\u274C " + check["msg"] + self.filename)

    def _check_label_uniqueness(self):
        if self.df["label"].duplicated().sum() > 0:
            duplicated = list(self.df["label"][self.df["label"].duplicated()].values)
            return {"msg": f"Found duplicated labels {duplicated}", "status": "Error"}
        else:
            return {"msg": f"No duplicated labels", "status": "Success"}

    def _check_condition(self):

        if self.condition_col not in self.df.columns:
            return {"msg": f"Cannot check the conditions. Header is missing {self.condition_col}", "status": "Error"}

        conds = sorted(self.df[self.condition_col].unique())
        C = len(conds)
        if C == 0:
            return {"msg": f"Found no conditions", "status": "Error"}
        elif C == 1:
            return {"msg": f"Found only one condition {conds}", "status": "Error"}
        else:

            # checks whether a conditon has only 1 replicate. Forbidden by DeSeq2
            for cond in conds:
                if sum(self.df[self.condition_col] == cond) == 1:
                    return {
                        "msg": f"Found condition {cond} with only one replicate. Forbidden by DeSeq2",
                        "status": "Error",
                    }
            if len(self.df) % C == 0:
                return {"msg": f"Found {C} conditions and {len(self.df)} samples", "status": "Success"}
            else:
                return {"msg": f"Found {C} conditions but {len(self.df)} samples (uneven?)", "status": "Warning"}

    def _check_label_col_name(self):
        if "label" not in self.df.columns:
            return {"msg": "Incorrect header. Expected 'label' but not found", "status": "Error"}
        else:
            return {"msg": "Found name 'label' in the Header", "status": "Success"}

    def _check_condition_col_name(self):
        if self.condition_col not in self.df.columns:
            return {"msg": f"Incorrect header. Expected {self.condition_col} but not found", "status": "Error"}
        else:
            return {"msg": f"Found name '{self.condition_col}' in the Header", "status": "Success"}

    def _get_conditions(self):
        try:
            return sorted(self.df[self.condition_col].unique())
        except KeyError:
            logger.error(f"No column named '{self.condition_col}' in design dataframe '{self.filename}'")
            sys.exit(1)

    conditions = property(_get_conditions)

    def _get_comparisons(self):
        conditions = self.conditions
        if self.reference is None:
            import itertools

            comps = list(itertools.combinations(conditions, 2))
        else:
            # only those versus reference
            comps = [(x, self.reference) for x in conditions if x != self.reference]
        return sorted(comps)

    comparisons = property(_get_comparisons)

    def keep_conditions(self, conditions):
        self.df = self.df.query(f"{self.condition_col} in @conditions")


class RNADiffAnalysis:
    """A tool to prepare and run a RNA-seq differential analysis with DESeq2

    :param counts_file: Path to tsv file out of FeatureCount with all samples together.
    :param design_file: Path to tsv file with the definition of the groups for each sample.
    :param condition: The name of the column from groups_tsv to use as condition. For more
        advanced design, a R function of the type 'condition*inter' (without the '~') could
        be specified (not tested yet). Each name in this function should refer to column
        names in groups_tsv.
    :param comparisons: A list of tuples indicating comparisons to be made e.g A vs B would be [("A", "B")]
    :param batch: None for no batch effect or name of a column in groups_tsv to add a batch effect.
    :param keep_all_conditions: if user set comparisons, it means will only want
        to include some comparisons and therefore their conditions. Yet,
        sometimes, you may still want to keep all conditions in the diffential
        analysis. If some set this flag to True.
    :param fit_type: Default "parametric".
    :param beta_prior: Default False.
    :param independent_filtering: To let DESeq2 perform the independentFiltering or not.
    :param cooks_cutoff: To let DESeq2 decide for the CooksCutoff or specifying a value.
    :param gff: Path to the corresponding gff3 to add annotations.
    :param fc_attribute: GFF attribute used in FeatureCounts.
    :param fc_feature: GFF feaure used in FeatureCounts.
    :param annot_cols: GFF attributes to use for results annotations
    :param threads: Number of threads to use
    :param outdir: Path to output directory.
    :param sep_counts: The separator used in the input count file.
    :param sep_design: The separator used in the input design file.

    This class reads a :class:`sequana.featurecounts.`

    ::

        r = rnadiff.RNADiffAnalysis("counts.csv", "design.csv",
                condition="condition", comparisons=[(("A", "B"), ('A', "C")],


    For developers: the rnadiff_template.R script behind the scene expects those
    attributes to be found in the RNADiffAnalysis class: counts_filename,
    design_filename, fit_type, fonction, comparison_str, independent_filtering,
    cooks_cutoff, code_dir, outdir, counts_dir, beta_prior, threads

    """

    _template_file = "rnadiff_light_template.R"
    _template_file_batch_vst = "rnadiff_batch_vst.R"
    _template_env = Environment(loader=PackageLoader("sequana", "resources/scripts"))
    template = _template_env.get_template(_template_file)

    def __init__(
        self,
        counts_file,
        design_file,
        condition,
        keep_all_conditions=False,
        reference=None,
        comparisons=None,
        batch=None,
        fit_type="parametric",
        beta_prior=False,
        independent_filtering=True,
        cooks_cutoff=None,
        gff=None,
        fc_attribute=None,
        fc_feature=None,
        annot_cols=None,
        # annot_cols=["ID", "Name", "gene_biotype"],
        threads=4,
        outdir="rnadiff",
        sep_counts=",",
        sep_design=r"\s*,\s*",
        minimum_mean_reads_per_gene=0,
        minimum_mean_reads_per_condition_per_gene=0,
        model=None,
    ):
        # if set, we can filter genes that have low counts (on average)
        self.minimum_mean_reads_per_gene = minimum_mean_reads_per_gene
        self.minimum_mean_reads_per_condition_per_gene = minimum_mean_reads_per_condition_per_gene

        # define some output directory and create them
        self.outdir = Path(outdir)
        self.counts_dir = self.outdir / "counts"
        self.code_dir = self.outdir / "code"
        self.images_dir = self.outdir / "images"

        self.outdir.mkdir(exist_ok=True)
        self.code_dir.mkdir(exist_ok=True)
        self.counts_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)

        self.usr_counts = counts_file

        self.counts_filename = self.code_dir / "counts.csv"

        # Read and check the design file. Filtering if comparisons is provided
        self.design = RNADesign(design_file, sep=sep_design, condition_col=condition, reference=reference)
        for check in self.design.checker():
            if check["status"] == "Error":
                logger.error(f"Found an error while parsing the design file {design_file}:")
                logger.error(f"{check['msg']}")
                sys.exit(1)
            elif check["status"] == "Warning":
                logger.warning(check["msg"])

        self.comparisons = comparisons if comparisons else self.design.comparisons

        _conditions = {x for comp in self.comparisons for x in comp}
        if not keep_all_conditions:
            self.design.keep_conditions(_conditions)

        logger.info(f"Conditions that are going to be included: ")
        for x in self.design.conditions:
            logger.info(f" - {x}")

        # we do not sort the design but the user order. Important for plotting
        self.design = self.design.df.set_index("label")

        # save the design file keeping track of its name
        self.design_filename = self.code_dir / "design.csv"
        self.design.to_csv(self.design_filename)

        # the name of the condition in the design file
        self.condition = condition

        # Reads and check the count file
        self.counts = self.check_and_save_input_tables(sep_counts)

        # check comparisons and print information
        self.check_comparisons()

        logger.info(f"Comparisons to be included:")
        for x in self.comparisons:
            logger.info(f" - {x}")
        self.comparisons_str = f"list({', '.join(['c' + str(x) for x in self.comparisons])})"

        # For DeSeq2
        self.batch = batch

        # if user provides a model, reset the default one
        if model:
            self.model = model
            logger.info(f"model: {self.model} (user's model)")
        else:
            self.model = f"~{batch} + {condition}" if batch else f"~{condition}"
            logger.info(f"model: {self.model}")

        self.fit_type = fit_type
        self.beta_prior = "TRUE" if beta_prior else "FALSE"
        self.independent_filtering = "TRUE" if independent_filtering else "FALSE"
        self.cooks_cutoff = cooks_cutoff if cooks_cutoff else "TRUE"

        # for metadata
        self.gff = gff
        self.fc_feature = fc_feature
        self.fc_attribute = fc_attribute
        self.annot_cols = annot_cols
        self.threads = threads

        # sanity check for the R scripts:
        for attr in (
            "counts_filename",
            "design_filename",
            "fit_type",
            "comparisons_str",
            "independent_filtering",
            "cooks_cutoff",
            "code_dir",
            "images_dir",
            "outdir",
            "counts_dir",
            "beta_prior",
            "threads",
        ):
            try:  # pragma: no cover
                getattr(self, attr)
            except AttributeError as err:  # pragma: no cover
                logger.error(f"Attribute {attr} missing in the RNADiffAnalysis class. cannot go further")
                raise Exception(err)

    def __repr__(self):
        info = f"RNADiffAnalysis object:\n\
- {self.counts.shape[1]} samples.\n\
- {len(self.comparisons)} comparisons.\n\n\
Counts overview:\n\
{self.counts.head()}\n\n\
Design overview:\n\
{self.design.head()}"

        return info

    def check_and_save_input_tables(self, sep_counts):
        # input may be an existing rnadiff.csv file create with FeatureCount
        # class, or (if it fails) a feature count file (tabulated with
        # Chr/Start/Geneid columns)
        try:
            # low memory set to False to avoid warnings (see pandas.read_csv doc)
            counts = pd.read_csv(
                self.usr_counts,
                sep=sep_counts,
                index_col="Geneid",
                comment="#",
                low_memory=False,
            )
        except ValueError:  # pragma: no cover
            try:
                counts = FeatureCount(self.usr_counts).df
            except:
                # could read any CSV file (useful with simulated data)
                counts = pd.read_csv(self.usr_counts)

        Ncounts = len(counts)
        logger.info(f"Found {Ncounts} counts. ")
        if self.minimum_mean_reads_per_gene > 0:
            logger.info(f"{len(counts)} annotated feature to be processed")
            counts = counts[counts.mean(axis=1) >= self.minimum_mean_reads_per_gene]
            logger.info(
                f"Keeping {len(counts)} features after removing low "
                f"counts below {self.minimum_mean_reads_per_gene} on average"
            )

        if self.minimum_mean_reads_per_condition_per_gene > 0:
            conditions = {x for comp in self.comparisons for x in comp}

            mean_per_conditions = pd.concat(
                [counts[self.design.query(f"{self.condition} == @cond").index].mean(axis=1) for cond in conditions],
                axis=1,
            )
            max_mean_per_condition = mean_per_conditions.max(axis=1)

            logger.info(f"{len(counts)} annotated feature to be processed")
            counts = counts[max_mean_per_condition >= self.minimum_mean_reads_per_condition_per_gene]
            logger.info(
                f"Keeping {len(counts)} features after removing low "
                f"counts below {self.minimum_mean_reads_per_condition_per_gene} on average"
            )

        # filter count based on the design and the comparisons provide in the
        # constructor so that columns match as expected by a DESeq2 analysis.

        counts = counts[self.design.index]

        # Save this sub count file
        counts.to_csv(self.counts_filename)

        return counts

    def check_comparisons(self):
        # let us check the consistenct of the design and comparisons
        valid_conditions = ",".join(set(self.design[self.condition].values))
        for item in [x for y in self.comparisons for x in y]:
            if item not in self.design[self.condition].values:
                logger.error(
                    f"""{item} not found in the design. Fix the design
or comparisons. possible values are {valid_conditions}"""
                )
                sys.exit(1)

    def run(self):
        """Create outdir and a DESeq2 script from template for analysis. Then execute
        this script.

        :return: a :class:`RNADiffResults` instance
        """

        logger.info("Running DESeq2 analysis. Rscript/R with DESeq2 must be installed. Please wait")
        rnadiff_script = self.code_dir / "rnadiff_light.R"

        with open(rnadiff_script, "w") as f:
            f.write(RNADiffAnalysis.template.render(self.__dict__))

        logger.info("Starting differential analysis with DESeq2...")

        # capture_output is valid for py3.7 and above
        p = subprocess.Popen(
            f"Rscript {rnadiff_script}",
            shell=True,
            universal_newlines=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        p.wait()
        stdout, stderr = p.stdout.read(), p.stderr.read()

        # Capture rnadiff output, Unfortunately, R code mixes stdout/stderr
        # FIXME
        with open(self.code_dir / "rnadiff.err", "w") as f:
            f.write(stderr)
        with open(self.code_dir / "rnadiff.out", "w") as f:
            f.write(stdout)

        with open(self.code_dir / "rnadiff.err", "r") as f:
            messages = [
                (
                    "every gene contains at least one zero, cannot compute log geometric means",
                    ". Please check your input feature file content.",
                ),
                (
                    "counts matrix should be numeric, currently it has mode: logical",
                    "May be a wrong design. Check the condition column",
                ),
            ]

            data = f.read()
            for msg in messages:  # pragma: no cover
                if msg[0] in data:
                    logger.critical(msg[0] + msg[1])

        logger.info("DGE analysis done. Processing the results")
        results = RNADiffResults(
            self.outdir,
            condition=self.condition,
            gff=self.gff,
            fc_feature=self.fc_feature,
            fc_attribute=self.fc_attribute,
            annot_cols=self.annot_cols,
        )
        return results


class RNADiffTable:
    def __init__(
        self,
        path,
        alpha=0.05,
        log2_fc=0,
        sep=",",
        condition="condition",
        shrinkage=True,
    ):
        """A representation of the results of a single rnadiff comparison

        Expect to find output of RNADiffAnalysis file named after condt1_vs_cond2_degs_DESeq2.csv

        ::

            from sequana.rnadiff import RNADiffTable
            RNADiffTable("A_vs_B_degs_DESeq2.csv")


        """
        self.path = Path(path)
        self.name = self.path.stem.replace("_degs_DESeq2", "").replace("-", "_")

        if shrinkage is True:
            self.l2fc_name = "log2FoldChange"
        else:
            self.l2fc_name = "log2FoldChangeNotShrinked"

        self._alpha = alpha
        self._log2_fc = log2_fc

        self.df = pd.read_csv(self.path, index_col=0, sep=sep)

        self.df.loc[self.df.padj == 0, "padj"] = 1e-50
        self.condition = condition

        self.filt_df = self.filter()
        self.set_gene_lists()

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, value):
        self._alpha = value
        self.filt_df = self.filter()
        self.set_gene_lists()

    @property
    def log2_fc(self):
        return self._log2_fc

    @log2_fc.setter
    def log2_fc(self, value):
        self._log2_fc = value
        self.filt_df = self.filter()
        self.set_gene_lists()

    def filter(self):
        """filter a DESeq2 result with FDR and logFC thresholds"""

        fc_filt = self.df[self.l2fc_name].abs() < self._log2_fc
        fdr_filt = self.df["padj"] > self._alpha
        outliers = self.df["padj"].isna()

        filt_df = self.df.copy()
        filt_df[fc_filt.values | fdr_filt.values | outliers] = np.nan
        return filt_df

    def set_gene_lists(self):
        only_drgs_df = self.filt_df.dropna(how="all")

        self.gene_lists = {
            "up": list(only_drgs_df.query(f"{self.l2fc_name} > 0").index),
            "down": list(only_drgs_df.query(f"{self.l2fc_name} < 0").index),
            "all": list(only_drgs_df.index),
        }

    def summary(self):
        return pd.DataFrame(
            {
                "log2_fc": self._log2_fc,
                "alpha": self._alpha,
                "up": len(self.gene_lists["up"]),
                "down": len(self.gene_lists["down"]),
                "all": len(self.gene_lists["all"]),
            },
            index=[self.name],
        )

    def plot_volcano(
        self,
        padj=0.05,
        add_broken_axes=False,
        markersize=4,
        limit_broken_line=[20, 40],
        plotly=False,
        annotations=None,
        hover_name=None,
    ):
        """

        .. plot::
            :include-source:

            from sequana.rnadiff import RNADiffResults
            from sequana import sequana_data

            r = RNADiffResults(sequana_data("rnadiff/", "doc"))
            r.comparisons["A_vs_B"].plot_volcano()

        """

        if plotly:
            from plotly import express as px

            df = self.df.copy()
            # ignore genes with undefined pvalues
            df = df[~df.padj.isnull()]

            if annotations is not None:
                try:
                    df = pd.concat([df, annotations], axis=1)
                except Exception as err:  # pragma: no cover
                    logger.warning(f"Could not merge rnadiff table with annotation. Full error is: {err}")
            df["log_adj_pvalue"] = -pylab.log10(df.padj)
            df["significance"] = ["<{}".format(padj) if x else ">={}".format(padj) for x in df.padj < padj]

            if hover_name is not None:  # pragma: no cover
                if hover_name not in df.columns:
                    logger.warning(f"hover_name {hover_name} not in the GFF attributes. Switching to automatic choice")
                    hover_name = None

            if hover_name is None:
                for name in ["Name", "gene_name", "gene_id", "locus_tag", "ID"]:
                    if name in df.columns:
                        hover_name = name
                        # once found, we can stop
                        break

            fig = px.scatter(
                df,
                x=self.l2fc_name,
                y="log_adj_pvalue",
                hover_name=hover_name,
                hover_data=["baseMean"],
                log_y=False,
                opacity=0.5,
                color="significance",
                height=600,
                labels={"log_adj_pvalue": "log adjusted p-value"},
            )
            # in future version of plotly, a add_hlines will be available. For
            # now, this is the only way to add axhline
            X = df[self.l2fc_name]

            fig.update_layout(
                shapes=[
                    dict(
                        type="line",
                        xref="x",
                        x0=X.min(),
                        x1=X.max(),
                        yref="y",
                        y0=-pylab.log10(padj),
                        y1=-pylab.log10(padj),
                        line=dict(color="black", width=1, dash="dash"),
                    )
                ]
            )

            return fig

        from brokenaxes import brokenaxes

        M = max(-pylab.log10(self.df.padj.dropna()))

        br1, br2 = limit_broken_line
        if M > br1:
            if add_broken_axes:
                bax = brokenaxes(ylims=((0, br1), (M - 10, M)), xlims=None)
            else:
                bax = pylab
        else:
            bax = pylab

        d1 = self.df.query("padj>@padj")
        d2 = self.df.query("padj<=@padj")

        x1 = d1[self.l2fc_name]
        x2 = d2[self.l2fc_name]

        bax.plot(
            x1,
            -np.log10(d1.padj),
            marker="o",
            alpha=0.5,
            color="k",
            lw=0,
            markersize=markersize,
        )
        bax.plot(
            x2,
            -np.log10(d2.padj),
            marker="o",
            alpha=0.5,
            color="r",
            lw=0,
            markersize=markersize,
        )

        bax.grid(True)
        try:
            bax.set_xlabel("fold change")
            bax.set_ylabel("log10 adjusted p-value")
        except Exception:
            bax.xlabel("fold change")
            bax.ylabel("log10 adjusted p-value")

        # we set the limits by finding max and min fold change.
        # Note, however, that we should ignore null pvalue
        l2fc = self.df[~self.df.padj.isnull()][self.l2fc_name]
        m1 = abs(min(l2fc))
        m2 = max(l2fc)

        limit = max(m1, m2)
        try:  # pragma: no cover
            bax.set_xlim([-limit, limit])
        except Exception:
            bax.xlim([-limit, limit])

        try:  # pragma: no cover
            y1, _ = bax.get_ylim()
            ax1 = bax.axs[0].set_ylim([br2, y1[1] * 1.1])
        except Exception:
            y1, y2 = bax.ylim()
            bax.ylim([0, y2])
        bax.axhline(-np.log10(0.05), lw=2, ls="--", color="r", label="pvalue threshold (0.05)")

    def plot_pvalue_hist(self, bins=60, fontsize=16, rotation=0):
        pylab.hist(self.df.pvalue.dropna(), bins=bins, ec="k")
        pylab.grid(True)
        pylab.xlabel("raw p-value", fontsize=fontsize)
        pylab.ylabel("Occurences", fontsize=fontsize)
        try:
            pylab.gcf().set_layout_engine("tight")
        except Exception:  # pragma: no cover
            pass

    def plot_padj_hist(self, bins=60, fontsize=16):
        pylab.hist(self.df.padj.dropna(), bins=bins, ec="k")
        pylab.grid(True)
        pylab.xlabel("Adjusted p-value", fontsize=fontsize)
        pylab.ylabel("Occurences", fontsize=fontsize)
        try:
            pylab.gcf().set_layout_engine("tight")
        except Exception:  # pragma: no cover
            pass


class RNADiffResults:
    """The output of a RNADiff analysis"""

    def __init__(
        self,
        rnadiff_folder,
        gff=None,
        fc_attribute=None,
        fc_feature=None,
        pattern="*vs*_degs_DESeq2.csv",
        alpha=0.05,
        log2_fc=0,
        palette=None,
        condition="condition",
        annot_cols=None,
        **kwargs,
    ):
        """

        :rnadiff_folder: a valid rnadiff folder created by :class:`RNADiffAnalysis`

        ::

            RNADiffResults("rnadiff/")


        """
        import seaborn as sns

        if palette is None:
            palette = (sns.color_palette(desat=0.6),)

        self.path = Path(rnadiff_folder)
        self.files = [x for x in self.path.glob(pattern)]

        self.counts_raw = pd.read_csv(self.path / "counts" / "counts_raw.csv", index_col=0, sep=",")
        self.counts_raw.sort_index(axis=1, inplace=True)

        self.counts_norm = pd.read_csv(self.path / "counts" / "counts_normed.csv", index_col=0, sep=",")
        self.counts_norm.sort_index(axis=1, inplace=True)

        self.counts_vst = pd.read_csv(self.path / "counts" / "counts_vst_norm.csv", index_col=0, sep=",")
        self.counts_vst.sort_index(axis=1, inplace=True)

        try:
            self.counts_vst_batch = pd.read_csv(self.path / "counts" / "counts_vst_batch.csv", index_col=0, sep=",")
            self.counts_vst_batch.sort_index(axis=1, inplace=True)
        except:
            self.counts_vst_batch = None

        self.dds_stats = pd.read_csv(self.path / "code" / "overall_dds.csv", index_col=0, sep=",")
        self.condition = condition

        design_file = f"{rnadiff_folder}/code/design.csv"
        self.design_df = self._get_design(design_file, condition=self.condition, palette=palette)

        # optional annotation
        self.fc_attribute = fc_attribute
        self.fc_feature = fc_feature
        self.annot_cols = annot_cols
        if gff:
            if fc_feature is None or fc_attribute is None:
                logger.warning("Since you provided a GFF file you must provide the feature and attribute to be used.")
            self.annotation = self.read_annot(gff)
        else:

            try:
                annots = pd.read_csv(self.path / "rnadiff.csv", index_col=0, header=[0, 1])
                self.annotation = annots.loc[:, "annotation"]
            except Exception as err:
                logger.warning(
                    "annotation from input GFF or existing rnadiff.csv not available. No annotaion will be used."
                )
                self.annotation = None

        # some filtering attributes
        self._alpha = alpha
        self._log2_fc = log2_fc

        # shrinkage required to import the table
        self.shrinkage = kwargs.get("shrinkage", True)
        self.comparisons = self.import_tables()

        self.df = self._get_total_df()
        self.filt_df = self._get_total_df(filtered=True)

        self.fontsize = kwargs.get("fontsize", 12)
        self.xticks_fontsize = kwargs.get("xticks_fontsize", 12)

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, value):
        self._alpha = value
        self.comparisons = self.import_tables()
        self.filt_df = self._get_total_df(filtered=True)

    @property
    def log2_fc(self):
        return self._log2_fc

    @log2_fc.setter
    def log2_fc(self, value):
        self._log2_fc = value
        self.comparisons = self.import_tables()
        self.filt_df = self._get_total_df(filtered=True)

    def to_csv(self, filename):
        self.df.to_csv(filename)

    def read_csv(self, filename):
        logger.warning("DEPRECATED DO NOT USE read_csv from RNADiffResults")
        self.df = pd.read_csv(filename, index_col=0, header=[0, 1])

    def import_tables(self):
        data = {
            compa.stem.replace("_degs_DESeq2", "").replace("-", "_"): RNADiffTable(
                compa,
                alpha=self._alpha,
                log2_fc=self._log2_fc,
                condition=self.condition,
                # gff=self.annotation.annotation,
                shrinkage=self.shrinkage,
            )
            for compa in self.files
        }

        return AttrDict(**data)

    def read_annot(self, gff):
        """Get a properly formatted dataframe from the gff.

        :param gff: a input GFF filename or an existing instance of GFF3
        """

        # if gff is already instanciated, we can just make a copy. Otherwise
        # we read it.
        if not hasattr(gff, "df"):
            gff = GFF3(gff)

        if self.annot_cols is None:
            lol = [
                list(x.keys()) for x in gff.df.query("genetic_type in @self.fc_feature.split(',')")["attributes"].values
            ]
            annot_cols = sorted(list(set([x for item in lol for x in item])))
        else:
            annot_cols = self.annot_cols

        df = gff.df.query("genetic_type in @self.fc_feature.split(',')").loc[:, annot_cols]
        df.drop_duplicates(inplace=True)

        # we want to keep the attribute in the columns for simplicity (to use in e.g.
        # volcano plots as a hover name) hence the drop=False
        df.set_index(self.fc_attribute, inplace=True, drop=False)

        # It may happen that a GFF has duplicated IDs ! For instance ecoli
        # has 20 duplicated ID that are part 1 and 2 of the same gene
        df = df[~df.index.duplicated(keep="last")]
        return df

    def _get_total_df(self, filtered=False):
        """Concatenate all rnadiff results in a single dataframe.

        FIXME: Columns relative to significative comparisons are not using
        self.log2_fc and self.alpha
        """

        dfs = []

        for compa, res in self.comparisons.items():
            df = res.filt_df if filtered else res.df
            df = df.transpose().reset_index()
            df["file"] = res.name
            df = df.set_index(["file", "index"])
            dfs.append(df)

        df = pd.concat(dfs, sort=True).transpose()

        # Add number of comparisons which are significative for a given gene
        num_sign_compa = (df.loc[:, (slice(None), "padj")] < 0.05).sum(axis=1)
        df.loc[:, ("statistics", "num_of_significative_comparisons")] = num_sign_compa

        # Add list of comparisons which are significative for a given gene
        df_sign_padj = df.loc[:, (slice(None), "padj")] < 0.05
        sign_compa = df_sign_padj.loc[:, (slice(None), "padj")].apply(
            # Extract column names (comparison names) for significative comparisons
            lambda row: {col_name[0] for sign, col_name in zip(row, row.index) if sign},
            axis=1,
        )
        df.loc[:, ("statistics", "significative_comparisons")] = sign_compa

        if self.annotation is not None:
            annot = self.annotation.copy()
            annot.columns = pd.MultiIndex.from_product([["annotation"], annot.columns])
            df = pd.concat([annot, df], axis=1)

        return df

    def summary(self):
        return pd.concat(res.summary() for compa, res in self.comparisons.items())

    def report(self):
        template_file = "rnadiff_report.html"
        template_env = Environment(loader=PackageLoader("sequana", "resources/templates"))
        template = template_env.get_template(template_file)

        with open("rnadiff_report.html", "w") as f:
            f.write(template.render({"table": self.summary().to_html(classes="table table-striped")}))

    def get_gene_lists(self, annot_col="index", Nmax=None, dropna=False):  # pragma: no cover
        gene_lists_dict = {}

        for compa in self.comparisons.keys():
            df = self.df.loc[:, [compa]].copy()
            df = df.droplevel(0, axis=1)

            # Let us add the annotation columns
            if self.annotation is not None:
                df = pd.concat([df, self.annotation.loc[df.index]], axis=1)

            fc_filt = df["log2FoldChange"].abs() >= self._log2_fc
            fdr_filt = df["padj"] <= self._alpha

            df = df[fc_filt.values & fdr_filt.values]
            df.reset_index(inplace=True)

            if annot_col not in df.columns:
                logger.error(f"attribute '{annot_col}' not found in input file. Use one of {df.columns}")
                sys.exit(1)

            if Nmax:
                df.sort_values("log2FoldChange", ascending=False, inplace=True)
                up_genes = list(df.query("log2FoldChange > 0")[annot_col])[:Nmax]

                df.sort_values("log2FoldChange", ascending=True, inplace=True)
                down_genes = list(df.query("log2FoldChange < 0")[annot_col])[:Nmax]

                all_genes = list(list(df.sort_values("log2FoldChange", key=abs, ascending=False)[annot_col])[:Nmax])

            else:
                up_genes = list(df.query("log2FoldChange > 0")[annot_col])
                down_genes = list(df.query("log2FoldChange < 0")[annot_col])
                all_genes = list(df.loc[:, annot_col])

            gene_lists_dict[compa] = {
                "up": up_genes,
                "down": down_genes,
                "all": all_genes,
            }

            # sometimes, an attribute may not have an entry for each ID...
            # the column correponding to this annotation will therefore be
            # made of NaN, which need to be removed (or None possibly?).
            if dropna:
                for direction in gene_lists_dict[compa]:
                    gl = gene_lists_dict[compa][direction]
                    if not gl:
                        continue

                    N = len(gl)
                    # drop None and nan (from math.nan)
                    gl = [x for x in gl if not str(x) == "nan" and x]

                    perc_unannotated = (N - len(gl)) / N * 100
                    if perc_unannotated > 0:
                        logger.warning(
                            f"{compa} {direction}: Removing {perc_unannotated:.0f}% of the genes for enrichment (missing identifiers in annotation)."
                        )
                    gene_lists_dict[compa][direction] = gl

        return gene_lists_dict

    def _get_design(self, design_file, condition, palette):
        """Import design from a table file and add color groups following the
        groups defined in the column 'condition' of the table file.
        """
        import seaborn as sns

        design = RNADesign(design_file, condition_col=condition)
        df = design.df.set_index("label")

        if len(design.conditions) > len(palette):
            palette = sns.color_palette("deep", n_colors=len(design.conditions))

        col_map = dict(zip(df.loc[:, condition].unique(), palette))

        df["group_color"] = df.loc[:, condition].map(col_map)
        return df

    def _format_plot(self, title="", xlabel="", ylabel="", rotation=0, fontsize=None):
        pylab.title(title)
        pylab.xticks(rotation=rotation, ha="right", fontsize=fontsize)
        pylab.xlabel(xlabel)
        pylab.ylabel(ylabel)

    # Probably not used anywhere.
    def __get_specific_commons(self, direction, compas=None, annot_col="index"):  # pragma: no cover
        """Extract gene lists for all comparisons.

        Genes are in common (but specific, ie a gene  only appears in the
        combination considered) comparing all combinations of comparisons.

        :param direction: The regulation direction (up, down or all) of the gene
            lists to consider
        :param compas: Specify a list of comparisons to consider (Comparisons
            names can be found with self.comparisons.keys()).

        """
        common_specific_dict = {}

        total_gene_lists = self.get_gene_lists(annot_col=annot_col)

        if not compas:
            compas = self.comparisons.keys()

        for size in range(1, len(compas)):
            for compa_group in combinations(compas, size):
                gene_lists = [total_gene_lists[compa][direction] for compa in compa_group]
                commons = set.intersection(*[set(gene_list) for gene_list in gene_lists])
                other_compas = [compa for compa in compas if compa not in compa_group]
                genes_in_other_compas = {
                    x for other_compa in other_compas for x in total_gene_lists[other_compa][direction]
                }

                commons = commons - genes_in_other_compas
                common_specific_dict[compa_group] = commons

        return common_specific_dict

    def _set_figsize(self, height=5, width=8):
        pylab.figure()
        fig = pylab.gcf()
        fig.set_figheight(height)
        fig.set_figwidth(width)

    def plot_count_per_sample(self, fontsize=None, rotation=45, xticks_fontsize=None):
        """Number of mapped and annotated reads (i.e. counts) per sample. Each color
        for each replicate

        .. plot::
            :include-source:

            from sequana.rnadiff import RNADiffResults
            from sequana import sequana_data

            r = RNADiffResults(sequana_data("rnadiff/", "doc"))
            r.plot_count_per_sample()

        """
        self._set_figsize()
        if fontsize is None:
            fontsize = self.fontsize
        if xticks_fontsize is None:
            xticks_fontsize = self.xticks_fontsize

        pylab.clf()
        df = self.counts_raw.sum().rename("total_counts")
        df = pd.concat([self.design_df, df], axis=1)

        pylab.bar(
            df.index,
            df.total_counts / 1000000,
            color=df.group_color,
            lw=1,
            zorder=10,
            ec="k",
            width=0.9,
        )

        pylab.xlabel("Samples", fontsize=fontsize)
        pylab.ylabel("reads (M)", fontsize=fontsize)
        pylab.grid(True, zorder=0)
        pylab.title("Total read count per sample", fontsize=fontsize)
        pylab.xticks(rotation=rotation, ha="right", fontsize=xticks_fontsize)
        try:
            pylab.gcf().set_layout_engine("tight")
        except Exception:
            pass

    def plot_percentage_null_read_counts(self, fontsize=None, xticks_fontsize=None):
        """Bars represent the percentage of null counts in each samples.  The dashed
        horizontal line represents the percentage of feature counts being equal
        to zero across all samples

        .. plot::
            :include-source:

            from sequana.rnadiff import RNADiffResults
            from sequana import sequana_data

            r = RNADiffResults(sequana_data("rnadiff/", "doc"))
            r.plot_percentage_null_read_counts()

        """
        self._set_figsize()
        if fontsize is None:
            fontsize = self.fontsize
        if xticks_fontsize is None:
            xticks_fontsize = self.xticks_fontsize

        # how many null counts ?
        df = (self.counts_raw == 0).sum() / self.counts_raw.shape[0] * 100
        df = df.rename("percent_null")
        df = pd.concat([self.design_df, df], axis=1)

        pylab.bar(df.index, df.percent_null, color=df.group_color, ec="k", lw=1, zorder=10)

        all_null = (self.counts_raw == 0).all(axis=1).sum() / self.counts_raw.shape[0]

        pylab.axhline(all_null, ls="--", color="black", alpha=0.5)

        pylab.xticks(rotation=45, ha="right", fontsize=xticks_fontsize)
        pylab.ylabel("Proportion of null counts (%)")
        pylab.grid(True, zorder=0)
        try:
            pylab.gcf().set_layout_engine("tight")
        except Exception:
            pass

    def plot_pca(
        self,
        n_components=2,
        colors=None,
        plotly=False,
        max_features=500,
        genes_to_remove=[],
        fontsize=10,
        adjust=True,
        transform_method="none",  # already done if count_mode == 'vst' or 'vst_batch'
        count_mode="vst",
    ):
        """

        .. plot::
            :include-source:

            from sequana.rnadiff import RNADiffResults
            from sequana import sequana_data

            r = RNADiffResults(sequana_data("rnadiff/", "doc"))

            colors = {
                'surexp1': 'r',
                'surexp2':'r',
                'surexp3':'r',
                'surexp1': 'b',
                'surexp2':'b',
                'surexp3':'b'}
            r.plot_pca(colors=colors)
        """
        import seaborn as sns

        from sequana.viz import PCA

        if count_mode == "vst":
            counts = self.counts_vst
        elif count_mode == "vst_batch":
            if self.counts_vst_batch is not None:
                counts = self.counts_vst_batch
        else:
            logger.error("count_mode must be vst or vst_batch")

        # let us use filter out genes to be ignored
        top_features = counts.index
        if genes_to_remove:
            top_features = [x for x in top_features if x not in genes_to_remove]
        counts_top_features = counts.loc[top_features, :]

        # We create the PCA instance here
        p = PCA(counts_top_features)

        # and the plotting
        if plotly is True:
            assert n_components == 3
            variance = p.plot(
                n_components=n_components,
                colors=colors,
                show_plot=False,
                max_features=max_features,
                transform=transform_method,
            )

            from plotly import express as px

            df = pd.DataFrame(p.Xr)
            df.index = p.df.columns
            df.columns = ["PC1", "PC2", "PC3"]
            df["size"] = [10] * len(df)  # same size for all points ?

            df = pd.concat([df, self.design_df], axis=1)
            df["label"] = df.index
            df["group_color"] = df[self.condition]

            # plotly uses 10 colors by default. Here we cope with the case
            # of having more than 10 conditions
            colors = None
            try:
                if len(set(self.design_df[self.condition].values)):
                    colors = sns.color_palette("deep", n_colors=13)

                    colors = px.colors.qualitative.Light24
            except Exception as err:
                logger.warning("Could not determine number of conditions")

            fig = px.scatter_3d(
                df,
                x="PC1",
                y="PC2",
                z="PC3",
                color="group_color",
                color_discrete_sequence=colors,
                labels={
                    "PC1": "PC1 ({}%)".format(round(100 * variance[0], 1)),
                    "PC2": "PC2 ({}%)".format(round(100 * variance[1], 1)),
                    "PC3": "PC3 ({}%)".format(round(100 * variance[2], 1)),
                },
                height=800,
                hover_name="label",
            )
            return fig
        else:
            variance = p.plot(
                n_components=n_components,
                colors=self.design_df.group_color,
                max_features=max_features,
                fontsize=fontsize,
                adjust=adjust,
                transform=transform_method,
            )

        return variance

    def plot_mds(self, n_components=2, colors=None, clf=True):
        """IN DEV, not functional"""

        from sequana.viz.mds import MDS

        p = MDS(self.counts_vst)  # [self.sample_names])
        p.plot(n_components=n_components, colors=self.design_df.group_color, clf=clf)

    def plot_isomap(self, n_components=2, colors=None):
        """IN DEV, not functional"""

        from sequana.viz.isomap import Isomap

        p = Isomap(self.counts_vst)
        p.plot(n_components=n_components, colors=self.design_df.group_color)

    def plot_density(self):
        import seaborn

        seaborn.set()
        for sample in self.counts_raw.columns:
            seaborn.kdeplot(pylab.log10(self.counts_raw[sample].clip(lower=1)))

        self._format_plot(
            title="Count density distribution",
            xlabel="Raw counts (log10)",
            ylabel="Density",
        )

    def plot_most_expressed_features(self, N=20):
        pylab.clf()

        # we will normalise to get pourcentage
        S = self.counts_raw.sum(axis=0)

        # let us make a copy
        dd = self.counts_raw.copy()
        dd = dd.divide(S) * 100  # percentage

        # average of each genes to ordered them by expression
        ordered_genes = dd.mean(axis=1).sort_values(ascending=False).index
        subdf = dd.loc[ordered_genes[0:N]]

        conditions = sorted(self.design_df.condition.unique())
        for condition in conditions:
            for (
                i,
                sample,
            ) in enumerate(self.design_df.query("condition == @condition").index):
                if i == 0:
                    pylab.plot(
                        subdf[sample],
                        color=self.design_df.loc[sample].group_color,
                        label=condition,
                    )
                else:
                    pylab.plot(subdf[sample], color=self.design_df.loc[sample].group_color)

        pylab.legend()

        self._format_plot(title="", xlabel="Most expressed genes", ylabel="Percentage (%)")

        pylab.xticks(range(0, len(subdf)), subdf.index, rotation=90)
        try:
            pylab.gcf().set_layout_engine("tight")
        except:
            pass
        return subdf

    def plot_feature_most_present(self, fontsize=None, xticks_fontsize=None):
        """"""
        if fontsize is None:
            fontsize = self.fontsize
        if xticks_fontsize is None:
            xticks_fontsize = self.xticks_fontsize

        df = []

        for x, y in self.counts_raw.idxmax().items():
            most_exp_gene_count = self.counts_raw.stack().loc[y, x]
            total_sample_count = self.counts_raw.sum().loc[x]

            df.append(
                {
                    "label": x,
                    "gene_id": y,
                    "count": most_exp_gene_count,
                    "total_sample_count": total_sample_count,
                    "most_exp_percent": most_exp_gene_count / total_sample_count * 100,
                }
            )

        df = pd.DataFrame(df).set_index("label")
        df = pd.concat([self.design_df, df], axis=1)

        pylab.clf()
        p = pylab.barh(
            df.index,
            df.most_exp_percent,
            color=df.group_color,
            zorder=10,
            lw=1,
            ec="k",
            height=0.9,
        )
        pylab.yticks(fontsize=xticks_fontsize)

        self._format_plot(
            # title="Counts monopolized by the most expressed gene",
            # xlabel="Sample",
            xlabel="Percent of total reads",
            fontsize=xticks_fontsize,
        )

        ax = pylab.gca()
        ax2 = ax.twinx()
        N = len(df)
        ax2.set_yticks([x + 0.5 for x in range(N)])
        if N <= 12:
            fontdict = {"fontsize": 12}
        elif N <= 24:
            fontdict = {"fontsize": 10}
        else:
            fontdict = {"fontsize": 8}

        ax2.set_yticklabels(list(df.gene_id.values), fontdict=fontdict)
        ax2.tick_params(axis="y", grid_linewidth=0)  # this is for the case seaborn is used

        pylab.sca(ax)

        pylab.gcf().set_layout_engine("tight")

    # for back compatibility, we stick to transform_method = log
    # max_features = 5000, count_mode = count_norm.
    def plot_dendogram(
        self, max_features=5000, transform_method="log", method="ward", metric="euclidean", count_mode="norm"
    ):
        # for info about metric and methods: https://tinyurl.com/yyhk9cl8
        from sequana.viz import clusterisation, dendogram

        if count_mode == "norm":
            cluster = clusterisation.Cluster(self.counts_norm)
        elif count_mode == "vst":
            cluster = clusterisation.Cluster(self.counts_vst)
        elif count_mode == "vst_batch":
            cluster = clusterisation.Cluster(self.counts_vst_batch)
        elif count_mode == "raw":
            cluster = clusterisation.Cluster(self.counts_raw)
        else:
            raise ValueError(f"counts_mode is incorrect {count_mode}")

        # scaling
        data = cluster.scale_data(transform_method=transform_method)

        # slect the best features only
        tokeep = data.std(axis=1).sort_values(ascending=False).index[0:max_features]
        df = pd.DataFrame(data.loc[tokeep])

        # actual computation
        d = dendogram.Dendogram(
            df.T,
            metric=metric,
            method=method,
            side_colors=list(self.design_df.group_color.unique()),
        )

        # Convert groups into numbers for Dendrogram category
        group_conv = {group: i for i, group in enumerate(self.design_df[self.condition].unique())}
        d.category = self.design_df[self.condition].map(group_conv).to_dict()
        d.plot()

    def plot_boxplot_rawdata(
        self,
        fliersize=2,
        linewidth=2,
        rotation=0,
        fontsize=None,
        xticks_fontsize=None,
        **kwargs,
    ):
        import seaborn as sbn

        if fontsize is None:
            fontsize = self.fontsize
        if xticks_fontsize is None:
            xticks_fontsize = self.xticks_fontsize

        ax = sbn.boxplot(
            data=self.counts_raw.clip(1),
            linewidth=linewidth,
            fliersize=fliersize,
            palette=[self.design_df.group_color.loc[x] for x in self.counts_raw.columns],
            **kwargs,
        )
        pos, labs = pylab.xticks()
        pylab.xticks(pos, labs, rotation=rotation)
        ax.set_ylabel("Counts (raw) in log10 scale")
        ax.set_yscale("log")
        self._format_plot(ylabel="Raw count distribution", fontsize=xticks_fontsize)
        pylab.gcf().set_layout_engine("tight")

    def plot_boxplot_normeddata(
        self,
        fliersize=2,
        linewidth=2,
        rotation=0,
        fontsize=None,
        xticks_fontsize=None,
        **kwargs,
    ):
        import seaborn as sbn

        if fontsize is None:
            fontsize = self.fontsize
        if xticks_fontsize is None:
            xticks_fontsize = self.xticks_fontsize

        ax = sbn.boxplot(
            data=self.counts_norm.clip(1),
            linewidth=linewidth,
            fliersize=fliersize,
            palette=[self.design_df.group_color.loc[x] for x in self.counts_norm.columns],
            **kwargs,
        )
        pos, labs = pylab.xticks()
        pylab.xticks(pos, labs, rotation=rotation)
        ax.set(yscale="log")
        self._format_plot(ylabel="Normalised count distribution")
        pylab.gcf().set_layout_engine("tight")

    def plot_dispersion(self):
        pylab.plot(
            self.dds_stats.baseMean,
            self.dds_stats.dispGeneEst,
            "ok",
            label="Estimate",
            ms=1,
        )
        pylab.plot(
            self.dds_stats.baseMean,
            self.dds_stats.dispersion,
            "ob",
            label="final",
            ms=1,
        )
        pylab.plot(self.dds_stats.baseMean, self.dds_stats.dispFit, "or", label="Fit", ms=1)
        pylab.legend()
        ax = pylab.gca()
        ax.set(yscale="log")
        ax.set(xscale="log")

        self._format_plot(
            title="Dispersion estimation",
            xlabel="Mean of normalized counts",
            ylabel="Dispersion",
        )

    def heatmap(self, comp, log2_fc=1, padj=0.05):
        assert comp in self.comparisons.keys()
        from sequana.viz import heatmap

        h = heatmap.Clustermap(
            self.counts_norm.loc[
                self.comparisons[comp]
                .df.query("(log2FoldChange<-@log2_fc or log2FoldChange>@log2_fc) and padj<@padj")
                .index
            ]
        ).plot()

    def _replace_index_with_annotation(self, df, annot):
        # ID is unique but annotation_column may not be complete with NA
        # Let us first get the annotion with index as the data index
        # and one column (the annotation itself)
        dd = self.annotation.loc[df.index][annot]

        # Let us replace the possible NA with the ID
        dd = dd.fillna(dict({(x, x) for x in dd.index}))

        # Now we replace the data index with this annoation
        df.index = dd.values

        return df

    def heatmap_vst_centered_data(
        self,
        comp,
        log2_fc=1,
        padj=0.05,
        xlabel_size=8,
        ylabel_size=12,
        figsize=(10, 15),
        annotation_column=None,
    ):
        assert comp in self.comparisons.keys()
        from sequana.viz import heatmap

        # Select counts based on the log2 fold change and padjusted
        data = self.comparisons[comp].df.query("(log2FoldChange<-@log2_fc or log2FoldChange>@log2_fc) and padj<@padj")
        counts = self.counts_vst.loc[data.index].copy()

        logger.info(f"Using {len(data)} DGE genes")

        # replace the indices with the proper annotation if required.
        if self.annotation and annotation_column:
            data = self._replace_index_with_annotation(data, annotation_column)
            counts.index = data.index

        # finally the plots
        h = heatmap.Clustermap(counts, figsize=figsize, z_score=0, center=0)

        ax = h.plot()
        ax.ax_heatmap.tick_params(labelsize=xlabel_size, axis="x")
        ax.ax_heatmap.tick_params(labelsize=ylabel_size, axis="y")

        return ax

    def plot_upset(self, force=False, max_subsets=20):
        """Plot the upset plot (alternative to venn diagram).


        with many comparisons, plots may be quite large. We can reduce the width
        by ignoring the small subsets. We fix the max number of subsets to 20 for now.
        """
        import upsetplot as upset
        from upsetplot.plotting import _process_data

        if len(self.comparisons) > 6 and not force:
            logger.warning("Upset plots are not computed for more than 6 comparisons.")
            return

        if len(self.comparisons) < 2:
            logger.warning("Upset plots can not computed for less than 2 comparisons.")
            return

        df = self.df.copy()
        df = df.loc[:, (slice(None), "padj")]

        # Keep only the name of the comparison as column name
        df.columns = [x[0] for x in df.columns]
        df = df < self.alpha

        # From a dataframe of booleans, get data structure needed for upset
        # ie a dictionnary with comparisons as keys and list of DEG as values.
        data = df.apply(lambda x: list(x.index[x])).to_dict()

        # let us figure out how many subsets we will have
        updata = _process_data(
            upset.from_contents(data),
            sort_by="cardinality",
            subset_size="count",
            sum_over=None,
            sort_categories_by="cardinality",
        )
        subsets = updata[2]

        if len(subsets) > max_subsets:
            min_subset_size = updata[2].values[max_subsets]
        else:
            min_subset_size = None

        # now let us do the plotting
        u = upset.UpSet(
            upset.from_contents(data),
            subset_size="count",
            sort_by="cardinality",
            totals_plot_elements=4,
            element_size=44,
            intersection_plot_elements=len(data),
            min_subset_size=min_subset_size,
        )

        u._default_figsize = (16, 8)
        u.plot()
