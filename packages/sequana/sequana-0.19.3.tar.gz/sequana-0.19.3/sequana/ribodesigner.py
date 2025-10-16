#  This file is part of Sequana software
#
#  Copyright (c) 2016-2020 - Sequana Development Team
#
#  Distributed under the terms of the 3-clause BSD license.
#  The full license is in the LICENSE file, distributed with this software.
#
#  website: https://github.com/sequana/sequana
#  documentation: http://sequana.readthedocs.io
#
##############################################################################
"""Ribodesigner module"""
import datetime
import json
import shutil
import subprocess
import sys
from itertools import product
from pathlib import Path

from sequana import logger, version
from sequana.fasta import FastA
from sequana.lazy import numpy as np
from sequana.lazy import pandas as pd
from sequana.lazy import pylab, pysam
from sequana.tools import reverse_complement

logger.setLevel("INFO")


class RiboDesigner(object):
    """Design probes for ribosomes depletion.

    From a complete genome assembly FASTA file and a GFF annotation file:

    - Extract genomic sequences corresponding to the selected ``seq_type``.
    - For these selected sequences, design probes computing probe length and inter probe space according to the length of the ribosomale sequence.
    - Detect the highest cd-hit-est identity threshold where the number of probes is inferior or equal to ``max_n_probes``.
    - Report the list of probes in BED and CSV files.

    In the CSV, the oligo names are in column 1 and the oligo sequences in column 2.

    :param fasta: The FASTA file with complete genome assembly to extract ribosome sequences from.
    :param gff: GFF annotation file of the genome assembly. If none provided, assuming the input FastA is
        already made of rRNA.
    :param output_directory: The path to the output directory defaults to ribodesigner.
    :param seq_type: string describing sequence annotation type (column 3 in GFF) to select rRNA from.
    :param max_n_probes: Max number of probes to design
    :param force:  If the `output_directory` already exists, overwrite it.
    :param threads: Number of threads to use in cd-hit clustering.
    :param float identity_step: step to scan the sequence identity (between 0 and 1) defaults to 0.01.
    :param force_clustering:
    """

    def __init__(
        self,
        fasta,
        gff=None,
        output_directory="ribodesigner",
        seq_type="rRNA",
        max_n_probes=384,
        force=False,
        threads=4,
        identity_step=0.01,
        force_clustering=False,
        **kwargs,
    ):
        # Input
        self.fasta = fasta
        self.gff = gff
        self.seq_type = seq_type
        self.max_n_probes = max_n_probes
        self.threads = threads
        self.outdir = Path(output_directory)
        self.identity_step = identity_step
        self.force_clustering = force_clustering

        if force:
            self.outdir.mkdir(exist_ok=True)
        else:
            try:
                self.outdir.mkdir()
            except FileExistsError as err:  # pragma: no cover
                logger.error(f"Output directory {output_directory} exists. Use --force or set force=True")
                sys.exit(1)

        # Outputs
        self.filtered_gff = self.outdir / "ribosome_filtered.gff"
        self.ribo_sequences_fasta = self.outdir / "ribosome_sequences.fas"
        self.probes_fasta = self.outdir / "probes_sequences.fas"

        self.clustered_probes_fasta = self.outdir / "clustered_probes.fas"
        self.clustered_probes_csv = self.outdir / "clustered_probes.csv"
        self.clustered_probes_bed = self.outdir / "clustered_probes.bed"
        self.output_json = self.outdir / "ribodesigner.json"

        self.json = {
            "max_n_probes": max_n_probes,
            "identity_step": identity_step,
            "feature": seq_type,
        }

    def get_rna_pos_from_gff(self):
        """Convert a GFF file into a pandas DataFrame filtered according to the
        self.seq_type.
        """
        total_length = 0

        gff = pd.read_csv(
            self.gff,
            sep="\t",
            comment="#",
            names=[
                "seqid",
                "source",
                "seq_type",
                "start",
                "end",
                "score",
                "strand",
                "phase",
                "attributes",
            ],
        )

        filtered_gff = gff.query("seq_type == @self.seq_type")

        with pysam.Fastafile(self.fasta) as fas:
            with open(self.ribo_sequences_fasta, "w") as fas_out:
                for row in filtered_gff.itertuples():
                    region = f"{row.seqid}:{row.start}-{row.end}"
                    seq_record = f">{region}\n{fas.fetch(region=region)}\n"
                    fas_out.write(seq_record)
                    total_length += len(fas.fetch(region=region))
        self.json["input_total_length"] = total_length
        self.json["input_number_sequences"] = filtered_gff.shape[0]

        seq_types = gff.seq_type.unique().tolist()

        self.json["seq_types"] = ",".join(seq_types)
        logger.info(f"Genetic types found in gff: {','.join(seq_types)}")
        logger.info(
            f"Found {filtered_gff.shape[0]} '{self.seq_type}' entries in the annotation file ({total_length}bp long)."
        )
        logger.debug(f"\t" + filtered_gff.to_string().replace("\n", "\n\t"))

        filtered_gff.to_csv(self.filtered_gff)

    def _get_probe_and_step_len_greedy(self, seq):
        """Modified version of _get_probe_and_step_len"""
        seq_len = len(seq.sequence)

        # sequences below 92 base fail when scanning the parameter space.
        # in such case, one probe or two overlapping probes should do it.

        if seq_len < 50:
            return 50, 15
        elif seq_len < 100:
            return 40, 10

        probe_lens = range(60, 40, -1)
        inter_probe_space = range(20, 10, -1)

        for probe_len, inter_probe_space in product(probe_lens, inter_probe_space):
            if ((seq_len + inter_probe_space) / (probe_len + inter_probe_space)).is_integer():
                return probe_len, inter_probe_space

        # 4% of sequence length are not found in the parameter space [60-40] x [10-20]
        # Using 70-40 x 30-10 gives 0 fails for sequences up to 200,000 bases
        probe_lens = range(70, 40, -1)
        inter_probe_space = range(30, 10, -1)

        for probe_len, inter_probe_space in product(probe_lens, inter_probe_space):
            X = (seq_len + inter_probe_space) / (probe_len + inter_probe_space)
            if X.is_integer():
                return probe_len, inter_probe_space

        # 34 of sequence length are not found in the parameter space [60-40] x [10-20]
        # Using 80-40 x 35-10 gives 0 fails for sequences up to 200,000 bases
        probe_lens = range(80, 40, -1)
        inter_probe_space = range(35, 10, -1)

        for probe_len, inter_probe_space in product(probe_lens, inter_probe_space):
            X = (seq_len + inter_probe_space) / (probe_len + inter_probe_space)
            if X.is_integer():
                return probe_len, inter_probe_space

        raise ValueError(
            f"No correct probe length/inter probe space combination was found for {seq.name}"
        )  # pragma: no cover

    def _get_probe_and_step_len(self, seq):
        """Calculates the probe_len and inter_probe_space for a ribosomal sequence.

        ribo_len = probe_len * n + (inter_probe_space * (n - 1))
        <=>
        n = (ribo_len + inter_probe_space) / (prob_len + inter_probe_space)
        """

        seq_len = len(seq.sequence)

        probe_lens = range(60, 40, -1)
        inter_probe_space = range(20, 10, -1)

        for probe_len, inter_probe_space in product(probe_lens, inter_probe_space):
            if ((seq_len + inter_probe_space) / (probe_len + inter_probe_space)).is_integer():
                return probe_len, inter_probe_space

        raise ValueError(
            f"No correct probe length/inter probe space combination was found for {seq.name}"
        )  # pragma: no cover

    def _get_probe_and_step_len_simple(self, seq):
        seq_len = len(seq.sequence)
        if seq_len < 50:
            return 50, 15
        elif seq_len < 100:
            return 40, 10

        probe_len = 50
        inter_probe_space = 15

        # starts = arange(0, seq_len, probe_len+inter_probe_space)
        return 50, 15

    def _get_probe_and_step_len_spiral(self, seq):
        # much slower than original and greedy but ensure that probes are closer to the
        # expected value
        seq_len = len(seq.sequence)
        if seq_len < 50:
            return 50, 15
        elif seq_len < 100:
            return 40, 10

        def spiral(X, Y, x0, y0):
            items = []
            x = y = 0
            dx = 0
            dy = -1
            for i in range(max(X, Y) ** 2):
                if (-X / 2 - 1 < x <= X / 2) and (-Y / 2 - 1 < y <= Y / 2):
                    items.append((x, y))
                if x == y or (x < 0 and x == -y) or (x > 0 and x == 1 - y):
                    dx, dy = -dy, dx
                x, y = x + dx, y + dy
            items = [(x + X / 2 + x0, y + Y / 2 + y0) for x, y in items]
            return items

        # set of points from 40 to 60 (40+21) and from 10 to 20 (10+11)
        positions = spiral(40, 10, 40, 10)

        for probe_len, inter_probe_space in positions:
            if ((seq_len + inter_probe_space) / (probe_len + inter_probe_space)).is_integer():
                return int(probe_len), int(inter_probe_space)

        raise ValueError(
            f"No correct probe length/inter probe space combination was found for {seq.name}"
        )  # pragma: no cover

    def _get_probes_df(self, seq, probe_len, step_len, mode="generic"):
        """Generate the Dataframe with probes information.

        Design probes to have end-to-end coverage on the + strand and fill the inter_probe_space present on the + strand with probes designed on the - strand.

        :param seq: A pysam sequence object.
        :param prob_len: The length of the probes calculated by self._get_probe_and_step_len.
        :param step_len: The length of the inter-probe space calculated by self._get_probe_and_step_len.
        :param strand: The strand on which probes are designed.
        """

        # + strand probes
        starts = [start for start in range(0, len(seq.sequence) - probe_len + 1, probe_len + step_len)]
        stops = [start + probe_len for start in starts]

        df = pd.DataFrame(
            {
                "name": seq.name,
                "start": starts,
                "stop": stops,
                "strand": "+",
                "score": 0,
            }
        )
        df["sequence"] = [seq.sequence[row.start : row.stop] for row in df.itertuples()]
        df["seq_id"] = df["name"] + f"_+_" + df["start"].astype(str) + "_" + df["stop"].astype(str)

        # - strand probes
        sequence = reverse_complement(seq.sequence)
        # Starts reverse probes to be centered on inter_probe_space of the forward probes
        rev_starts = [int((starts[i + 1] + starts[i]) / 2) for i in range(0, len(starts) - 1)]
        rev_stops = [start + probe_len for start in rev_starts]

        if mode == "simple":
            rev_starts = [x for x in starts]
            rev_stops = [start + probe_len for start in rev_starts]

        df_rev = pd.DataFrame(
            {
                "name": seq.name,
                "start": rev_starts,
                "stop": rev_stops,
                "strand": "-",
                "score": 0,
            }
        )
        df_rev["sequence"] = [sequence[row.start : row.stop] for row in df_rev.itertuples()]
        df_rev["seq_id"] = df_rev["name"] + f"_-_" + df_rev["start"].astype(str) + "_" + df_rev["stop"].astype(str)

        # Transform to bed coordinates for the reverse_complement
        df_rev["start"] = len(sequence) - df_rev["start"]
        df_rev["stop"] = len(sequence) - df_rev["stop"]
        df_rev.rename(columns={"start": "stop", "stop": "start"}, inplace=True)

        return pd.concat([df, df_rev])

    def get_all_probes(self, method="original"):
        """Run all probe design and concatenate results in a single DataFrame."""

        self.json["method"] = method
        probes_dfs = []

        with pysam.FastxFile(self.ribo_sequences_fasta) as fas:
            for seq in fas:

                if method == "greedy":
                    probe_len, step_len = self._get_probe_and_step_len_greedy(seq)
                    df = self._get_probes_df(seq, probe_len, step_len)
                elif method == "original":
                    probe_len, step_len = self._get_probe_and_step_len(seq)
                    df = self._get_probes_df(seq, probe_len, step_len)
                elif method == "spiral":
                    probe_len, step_len = self._get_probe_and_step_len_spiral(seq)
                    df = self._get_probes_df(seq, probe_len, step_len)
                elif method == "simple":
                    probe_len, step_len = self._get_probe_and_step_len_simple(seq)
                    df = self._get_probes_df(seq, probe_len, step_len, mode="simple")

                probes_dfs.append(df)

        self.probes_df = pd.concat(probes_dfs)
        self.probes_df["kept_after_clustering"] = True
        self.probes_df["bed_color"] = self.probes_df.kept_after_clustering.map({True: "21,128,0", False: "128,64,0"})

    def export_all_probes_to_fasta(self):
        """From the self.probes_df, export to FASTA and CSV files."""

        with open(self.probes_fasta, "w") as fas:
            for row in self.probes_df.itertuples():
                fas.write(f">{row.seq_id}\n{row.sequence}\n")

    def clustering_needed(self, force=False):
        """Checks if a clustering is needed.

        :param force: force clustering even if unecessary.
        """

        # Do not cluster if number of probes already inferior to defined threshold
        if not force and self.probes_df.shape[0] <= self.max_n_probes:
            logger.info(
                f"Number of probes {self.probes_df.shape[0]} already inferior to {self.max_n_probes}. No clustering will be performed."
            )
            return False
        else:
            return True

    def cluster_probes(self):
        """Use cd-hit-est to cluster highly similar probes."""
        logger.info("Clustering probes")
        outdir = (
            Path(self.clustered_probes_fasta).parent
            / f"cd-hit-est-{datetime.datetime.today().isoformat(timespec='seconds', sep='_')}"
        )
        outdir.mkdir()
        log_file = outdir / "cd-hit.log"

        res_dict = {"seq_id_thres": [], "n_probes": []}

        for seq_id_thres in np.arange(0.8, 1, self.identity_step).round(3):
            tmp_fas = outdir / f"clustered_{seq_id_thres}.fas"
            cmd = f"cd-hit-est -i {self.probes_fasta} -o {tmp_fas} -c {seq_id_thres} -n {self.threads}"
            logger.debug(f"Clustering probes with command: {cmd} (log in '{log_file}').")

            with open(log_file, "a") as f:
                subprocess.run(cmd, shell=True, check=True, stdout=f)

            res_dict["seq_id_thres"].append(seq_id_thres)
            res_dict["n_probes"].append(len(FastA(tmp_fas)))

        # Add number of probes without clustering
        res_dict["seq_id_thres"].append(1)
        res_dict["n_probes"].append(self.probes_df.shape[0])

        self.json["results"] = res_dict

        # Dataframe with number of probes for each cdhit identity threshold
        pylab.clf()
        df = pd.DataFrame(res_dict)

        import seaborn as sns  # local import to speed up imports

        p = sns.lineplot(data=df, x="seq_id_thres", y="n_probes", markers=["o"])
        p.axhline(
            self.max_n_probes,
            alpha=0.8,
            linestyle="--",
            color="red",
            label="max number of probes requested",
        )
        pylab.xlabel("Sequence identity", fontsize=16)
        pylab.ylabel("Number of probes", fontsize=16)

        # Extract the best identity threshold
        best_thres = df.query("n_probes <= @self.max_n_probes").seq_id_thres.max()

        if not np.isnan(best_thres):
            n_probes = df.query("seq_id_thres == @best_thres").loc[:, "n_probes"].values[0]

            self.json["n_probes"] = int(n_probes)
            self.json["best_thres"] = best_thres

            logger.info(f"Best clustering threshold: {best_thres}, with {n_probes} probes.")
            shutil.copy(outdir / f"clustered_{best_thres}.fas", self.clustered_probes_fasta)
            kept_probes = [seq.name for seq in FastA(outdir / f"clustered_{best_thres}.fas")]
            self.probes_df["kept_after_clustering"] = self.probes_df.seq_id.isin(kept_probes)
            self.probes_df["bed_color"] = self.probes_df.kept_after_clustering.map(
                {True: "21,128,0", False: "128,64,0"}
            )
            self.probes_df["clustering_thres"] = best_thres
            pylab.plot(best_thres, n_probes, "o", label="Final number of probes")
            pylab.legend()
        else:
            logger.warning(
                f"No identity threshold was found to have as few as {self.max_n_probes} probes. Keep all probes. Set a valid value with --max-n-probes between {df.n_probes.min()} (min) and {df.n_probes.max()} (max)"
            )

        self.clustering_df = df.sort_values("seq_id_thres")

        return self.probes_df.query("kept_after_clustering == True")

    def export_to_csv_bed(self):
        """Export final results to CSV and BED files"""

        if self.clustering_needed():
            df = self.cluster_probes()
        else:
            df = self.probes_df

        df.to_csv(self.clustered_probes_csv, index=False, columns=["seq_id", "sequence"])

        self.probes_df.to_csv(
            self.clustered_probes_bed,
            sep="\t",
            index=False,
            header=None,
            columns=[
                "name",
                "start",
                "stop",
                "sequence",
                "score",
                "strand",
                "start",
                "stop",
                "bed_color",
            ],
        )

    def export_to_json(self):
        with open(self.output_json, "w") as fout:
            json.dump(self.json, fout, indent=4, sort_keys=True)

    def run(self, method="greedy"):
        if self.gff:
            self.get_rna_pos_from_gff()
        else:
            shutil.copy(self.fasta, self.ribo_sequences_fasta)

        self.get_all_probes(method=method)
        self.export_all_probes_to_fasta()
        self.export_to_csv_bed()
        self.export_to_json()
