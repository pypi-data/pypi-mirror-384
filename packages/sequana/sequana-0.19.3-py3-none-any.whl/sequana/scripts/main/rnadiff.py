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
import os
import sys
from pathlib import Path

import colorlog
import rich_click as click

from sequana.gff3 import GFF3
from sequana.rnadiff import RNADesign, RNADiffAnalysis
from sequana.scripts.common import teardown
from sequana.scripts.utils import CONTEXT_SETTINGS, common_logger
from sequana.utils import config

logger = colorlog.getLogger(__name__)


def rnadiff_auto_batch_column(ctx, args, incomplete):
    if "--design" in args:
        dfile = args[args.index("--design")]
        if os.path.exists(dfile):
            d = RNADesign(dfile)
        else:
            logger.critical("You must have a valid design.csv file following --design")
            sys.exit(1)
    else:
        try:
            d = RNADesign("design.csv")
            logger.warning("Using local design.csv to infer the batch column")
        except FileNotFoundError:
            logger.critical("No default design.csv found. Please use --design YOUR_DESIGN.csv ")
            sys.exit(1)

    batch = (x for x in d.df.columns if x not in {"label", "condition"})
    if len(batch) == 0:
        logger.warning("No batch effect included in your design file")
    else:
        return [c for c in batch if incomplete in c[0]]


click.rich_click.OPTION_GROUPS = {
    "sequana rnadiff": [
        {
            "name": "Required",
            "options": ["--design", "--features", "--annotation-file", "--feature-name", "--attribute-name"],
        },
        {
            "name": "DeSEQ2 statistical analysis / design",
            "options": [
                "--beta-prior",
                "--condition",
                "--batch",
                "--comparisons",
                "--cooks-cutoff",
                "--independent-filtering",
                "--fit-type",
                "--keep-all-conditions",
                "--minimum-mean-reads-per-gene",
                "--minimum-mean-reads-per-condition-per-gene",
                "--shrinkage",
                "--reference",
            ],
        },
        {
            "name": "Informative options",
            "options": ["--help"],
        },
    ],
}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--design",
    type=click.Path(),
    required=True,
    default="design.csv",
    help="The design file in CSV format (see documentation above)",
)
@click.option(
    "--features",
    type=click.Path(),
    required=True,
    default="all_features.out",
    help="The merged features counts. Output of the sequana_rnaseq pipeline",
)
@click.option(
    "--annotation-file",
    "annotation",
    type=click.Path(),
    default=None,
    required=False,
    help="""The annotation GFF file used to perform the feature count""",
)
@click.option(
    "--beta-prior/--no-beta-prior",
    default=False,
    help="Use beta prior or not. Default is no beta prior",
)
@click.option(
    "--condition",
    type=str,
    default="condition",
    help="""The name of the column in design.csv to use as condition
for the differential analysis. Default is 'condition'""",
)
@click.option(
    "--force/--no-force",
    default=False,
    help="If output directory exists, use this option to erase previous results",
)
@click.option(
    "--output-directory",
    type=click.Path(),
    default="rnadiff",
    help="""Output directory where are saved the results. Use --force if it exists already""",
)
@click.option(
    "--feature-name",
    default="gene",
    required=True,
    help="The feature name compatible with your GFF (default is 'gene')",
)
@click.option(
    "--attribute-name",
    default="ID",
    required=True,
    help="""The attribute used as identifier. Compatible with your GFF (default is 'ID')""",
)
@click.option(
    "--reference",
    type=click.Path(),
    default=None,
    help="""The reference to test DGE against. If provided, conditions not
            involving the reference are ignored. Otherwise all combinations are
            tested""",
)
@click.option(
    "--comparisons",
    type=click.Path(),
    default=None,
    help="""By default, if a reference is provided, all conditions versus that
reference are tested. If no reference, the entire combinatory is performed
(Ncondition * (Ncondition-1) / 2. In both case all condtions found in the
design file are used. If a comparison file is provided, only conditions found in
it will be used. """,
)
@click.option(
    "--cooks-cutoff",
    type=click.Path(),
    default=None,
    help="""if none, let DESeq2 choose the cutoff. Note that the Cook’s distance 
    is set to NA for genes with values above the threshold. At least 3 replicates 
    are required for flagging).""",
)
@click.option(
    "--independent-filtering/--no-independent-filtering",
    default=False,
    help="""Do not perform independent_filtering by default. low counts may not
have adjusted pvalues otherwise""",
)
@click.option(
    "--batch",
    type=str,
    default=None,
    help="""set the column name (in your design) corresponding to the batch
effect to be included in the statistical model as batch ~ condition""",
    shell_complete=rnadiff_auto_batch_column,
)
@click.option(
    "--fit-type",
    default="parametric",
    help="""DESeq2 type of fit. Default is 'parametric'. Uing the mean of gene-wise 
    disperion estimates as the fitted value can be specified setting this argument 
    to 'mean'. """,
)
@click.option(
    "--minimum-mean-reads-per-gene",
    default=0,
    help="""Keeps genes that have an average number of reads greater or equal to this value. This is the average across all
replicates and conditions. Not recommended if you have lots of conditions. By default all genes are kept""",
)
@click.option(
    "--minimum-mean-reads-per-condition-per-gene",
    default=0,
    help="""Keep genes that have at least one condition where the average number of reads 
    is greater or equal to this value. By default all genes are kept""",
)
@click.option(
    "--model",
    default=None,
    help="By default, the model is ~batch + condition. For more complex cases, you may set the --model more specifically",
)
@click.option(
    "--shrinkage/--no-shrinkage",
    default=True,
    help="""Shrinkage was added in the DESeq2 script analysis in Sequana 0.14.7. Although it 
    has a marginal impact, number of DGEs may be different and volcano plots have usually 
    a different shape. To ignore the shrinkage, you could set the option to --no-shrinkage""",
)
@click.option(
    "--keep-all-conditions/--no-keep-all-conditions",
    default=False,
    help="""Even though sub set of comparisons are provided, keep all conditions
in the analysis and report only the provided comparisons""",
)
@click.option(
    "--hover-name",
    default=None,
    help="""In volcano plot, we set the hover name to Name if present in the GFF,
otherwise to gene_id if present, then locus_tag, and finally ID and gene_name. One can specify
a hover name to be used with this option""",
)
@click.option(
    "--report-only",
    is_flag=True,
    help="""If analysis was done, you may want to redo the HTML report only using this option""",
)
@click.option(
    "--split-full-table/--no-split-full-table",
    default=False,
    help="Multiple comparisons on large genomes may create HTML reports that are quite large and would required lots of memory. Using this option, only significative DGE are in the main HTML report and full table are save in individual HTML pages",
)
@click.option("--xticks-fontsize", default=10, help="""Reduce fontsize of xticks""")
@common_logger
def rnadiff(**kwargs):
    """**Sequana RNADiff**: differential analysis and reporting.

     ----

     The **Sequana rnadiff** command performs the differential analysis of input RNAseq data using
     DeSEQ2 behind the scene.

     The command line looks like

         sequana rnadiff --annotation Lepto.gff --design design.csv --features all_features.out --feature-name gene --attribute-name ID

     This command performs the differential analysis of feature counts using DESeq2.
     A HTML report is created as well as a set of output files, including summary
     tables of the analysis.

     The expected input is a tabulated file which is the aggregation of feature counts
     for each sample. This file is produced by the Sequana RNA-seq pipeline
     (https://github.com/sequana/rnaseq).

     It is named all_features.out and looks like:

        Geneid   Chr Start End Strand Length BAM1  BAM2  BAM3  BAM4
        ENSG0001 1       1  10      +     10 120    130   140  150
        ENSG0002 2       1  10      +     10 120    130     0    0

    To perform this analysis, you will also need the GFF file used during the RNA-seq
    analysis.

    You also need a design file that give the correspondance
    between the sample names found in the feature_count file above and the
    conditions of your RNA-seq analysis. The design looks like:

            label,condition
            BAM1,condition_A
            BAM2,condition_A
            BAM3,condition_B
            BAM4,condition_B

     The feature-name is the feature that was used in your counting.
     The attribute-name is the main attribute to use in the HTML reports.
     Note however, that all attributes found in your GFF file are repored
     in the HTML page

     Batch effet can be included by adding a column in the design.csv file. For
     example if called 'day', you can take this information into account using
     '--batch day'

     By default, when comparing conditions, all combination are computed. If
     you have N conditions, we compute the N(N-1)/2 comparisons. The
     reference is automatically chosen as the last one found in the design
     file. In this example:

         label,condition
         BAM1,A
         BAM2,A
         BAM3,B
         BAM4,B

     we compare A versus B. If you do not want that behaviour, use
     '--reference A'.

     In a more complex design,

         label,condition
         BAM1,A
         BAM2,A
         BAM3,B
         BAM4,B
         BAM5,C
         BAM6,C

     The comparisons are A vs B, A vs C and B vs C.
     If you wish to perform different comparisons or restrict the
     combination, you can use a comparison input file. For instance, to
     perform the C vs A  and C vs B comparisons only, create this
     file (e.g. comparison.csv):

         alternative,reference
         C,A
         C,B

     and use '--comparison comparison.csv'.


    """
    import pandas as pd
    from easydev import cmd_exists

    from sequana import logger
    from sequana.modules_report.rnadiff import RNAdiffModule

    logger.setLevel(kwargs["logger"])

    if not cmd_exists("Rscript"):
        logger.critical(
            """Rscript not found; You will need R with the DESeq2 and ashr packages installed. 
            You may install it yourself or use damona using the rtools:1.2.0 image """
        )
        sys.exit(1)

    outdir = kwargs["output_directory"]
    feature = kwargs["feature_name"]
    attribute = kwargs["attribute_name"]

    if os.path.exists(outdir) and not kwargs["force"]:
        logger.error(f"{outdir} exist already. Use --force to overwrite. This will possibly delete existing files")
        sys.exit(1)

    if os.path.exists(outdir):
        # let us just remove the file with degs_DESeq2.csv
        # if files remains from previous comparisons they will
        # otherwise be included in the new analysis.
        for filename in Path(outdir).glob("*degs_DESeq2.csv"):
            filename.unlink()

    if kwargs["annotation"]:
        gff_filename = kwargs["annotation"]
        logger.info("Checking annotation file (feature and attribute)")
        gff = GFF3(gff_filename)
        for feat in feature.split(","):
            if feat not in gff.features:
                logger.error(f"{feature} not found in the GFF. Most probably a wrong feature name. Correct features are e.g. {gff.features[0:10]}")
                sys.exit(1)
            attributes = gff.get_attributes(feat)
            if attribute not in attributes:

                logger.error(
                    f"{attribute} not found in the GFF for the provided feature ({feat}). Most probably a wrong feature name."
                    f" Please change --attribute-name option or do not provide any GFF. Correct attribute names are {attributes}"
                )
                sys.exit(1)
    else:
        gff = None

    comparisons = kwargs["comparisons"]
    if comparisons:
        # use \s*,\s* to strip spaces
        compa_df = pd.read_csv(comparisons, sep="\s*,\s*", engine="python")
        comparisons = list(zip(compa_df["alternative"], compa_df["reference"]))

    logger.info(f"Differential analysis to be saved into ./{outdir}")
    for k in sorted(
        [
            "independent_filtering",
            "beta_prior",
            "batch",
            "cooks_cutoff",
            "fit_type",
            "reference",
        ]
    ):
        logger.info(f"  Parameter {k} set to : {kwargs[k]}")

    # The analysis is here
    r = RNADiffAnalysis(
        kwargs["features"],
        kwargs["design"],
        kwargs["condition"],
        keep_all_conditions=kwargs["keep_all_conditions"],
        batch=kwargs["batch"],
        comparisons=comparisons,
        reference=kwargs["reference"],
        fc_feature=feature,
        fc_attribute=attribute,
        outdir=outdir,
        gff=gff,
        cooks_cutoff=kwargs.get("cooks_cutoff"),
        independent_filtering=kwargs.get("independent_filtering"),
        beta_prior=kwargs.get("beta_prior"),
        fit_type=kwargs.get("fit_type"),
        minimum_mean_reads_per_gene=kwargs.get("minimum_mean_reads_per_gene"),
        minimum_mean_reads_per_condition_per_gene=kwargs.get("minimum_mean_reads_per_condition_per_gene"),
        model=kwargs["model"],
        sep_counts=","
    )

    if not kwargs["report_only"]:
        try:
            logger.info(f"Running DGE. Saving results into {outdir}")
            results = r.run()
            results.to_csv(f"{outdir}/rnadiff.csv")
        except Exception as err:
            logger.error(err)
            logger.error(f"please see {outdir}/code/rnadiff.err file for errors")
            sys.exit(1)

    logger.info("Reporting. Saving in summary.html")
    # this define the output directory where summary.html is saved
    config.output_dir = outdir

    import seaborn as sns

    RNAdiffModule(
        outdir,
        gff=gff,
        fc_attribute=attribute,
        fc_feature=feature,
        alpha=0.05,
        log2_fc=0,
        condition=kwargs["condition"],
        annot_cols=None,
        pattern="*vs*_degs_DESeq2.csv",
        palette=sns.color_palette(desat=0.6, n_colors=13),
        hover_name=kwargs["hover_name"],
        pca_fontsize=6,
        xticks_fontsize=kwargs.get("xticks_fontsize", 10),
        shrinkage=kwargs.get("shrinkage"),
        split_full_table=kwargs.get("split_full_table"),
        command=" ".join(["sequana"] + sys.argv[1:]),
    )

    #
    # save info.txt with sequana version
    teardown(outdir)
