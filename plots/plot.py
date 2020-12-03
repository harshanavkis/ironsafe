import sys
import seaborn as sns
import pandas as pd
import matplotlib as mpl
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker
from graph_utils import apply_aliases, column_alias
import numpy as np

"""
    - first arg: kind of plot(ndp, microbench)
    - subseq args: filenames
        - ndp: pure host, vanilla ndp, secndp, storage-side-secndp
"""

# mpl.use("Agg")
# mpl.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"
# mpl.rcParams["pdf.fonttype"] = 42
# mpl.rcParams["ps.fonttype"] = 42

# # plt.rc('text', usetex=True)
# plt.figure(figsize=(10, 10))
# sns.set(rc={'figure.figsize':(5,5)})
# sns.set_style("whitegrid")
# sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})
# sns.set_context(font_scale=1.5)
# sns.set_context("paper", rc={"font.size":10,"axes.titlesize":10,"axes.labelsize":10})
# sns.set_palette(sns.color_palette(palette="gray", n_colors=2))

plot_queries = [1]
storage_side_secndp_cols = [
    "num_prot_pages",
    "query_exec_time",
    "codec_time",
    "mt_verify_time",
    "num_encryption",
    "num_decryption",
    "packets_sent",
    "rows_processed"
]

sns.set_style("whitegrid", {'axes.grid' : False})

def catplot(**kwargs):
    # kwargs.setdefault("palette", "Greys")
    g = sns.catplot(**kwargs)
    g.despine(top=False, right=False)
    plt.autoscale()
    plt.subplots_adjust(top=0.98)
    return g

def host_ndp_plot(pure_host, vanilla_ndp, secndp):
    ph_df = pd.read_csv(pure_host, header=0, sep=',')
    vanilla_ndp = pd.read_csv(vanilla_ndp, header=0, sep=',')
    sn = pd.read_csv(secndp, header=0, sep=',')

    ph_df = ph_df[["kind", "query_no", "query_exec_time"]]
    vanilla_ndp = vanilla_ndp[["kind", "query", "total_time"]]
    sn = sn[["kind", "query", "total_time"]]

    ph_df = apply_aliases(ph_df)
    vanilla_ndp = apply_aliases(vanilla_ndp)
    sn = apply_aliases(sn)

    plot_df = pd.concat([ph_df, vanilla_ndp, sn])
    plot_df = plot_df[plot_df["query"].isin(plot_queries)].reset_index()
    plot_df = plot_df.drop("index", axis=1)

    # import pdb; pdb.set_trace()

    g = catplot(
            data=plot_df,
            x=plot_df.columns[1],
            y=plot_df.columns[2],
            kind="bar",
            height=0.25,
            hue="system",
            legend=False
        )
    g.fig.set_figheight(12)
    g.fig.set_figwidth(24)
    g.ax.tick_params(axis='both', which='major', labelsize=20)
    g.ax.set_xlabel(xlabel=plot_df.columns[1], fontsize=20)
    g.ax.set_ylabel(ylabel=plot_df.columns[2], fontsize=20)
    g.ax.legend(loc="upper left", fontsize=20)
    g.ax.set(ylim=(0, 400))
    g.savefig("END_2_END.pdf")

def secndp_overheads(vanilla_ndp, secndp, storage_side_secndp):
    """
        - four overlapping bars
            - end2end secndp
            - end2end secndp without merkle tree
            - end2end secndp without encryption
            - vanilla ndp
    """
    vn = pd.read_csv(vanilla_ndp, header=0, sep=',')
    vn = vn[["kind", "query", "total_time"]]

    sn = pd.read_csv(secndp, header=0, sep=',')
    sn = sn[["kind", "query", "total_time", "total_host_query_time"]]

    stsn = pd.read_csv(storage_side_secndp, header=None, sep=',')
    # import pdb; pdb.set_trace()
    stsn.columns = storage_side_secndp_cols
    stsn["query"] = vn["query"]
    stsn = stsn[["query", "query_exec_time", "codec_time", "mt_verify_time"]]

    columns = ["query", "vanilla_ndp", "other_overhead", "encr_time", "mt_verify_time"]
    plot_df = pd.DataFrame(columns=columns)
    plot_df["query"] = vn["query"]
    plot_df["mt_verify_time"] = stsn["mt_verify_time"]/sn["total_time"]
    plot_df["encr_time"] = (stsn["codec_time"]-stsn["mt_verify_time"])/sn["total_time"]
    plot_df["other_overhead"] = (sn["total_time"]-stsn["query_exec_time"]-sn["total_host_query_time"])/sn["total_time"]
    plot_df["vanilla_ndp"] = ((stsn["query_exec_time"]+sn["total_host_query_time"]-stsn["codec_time"])/sn["total_time"])

    plot_df = plot_df[~plot_df["query"].isin(plot_queries)].reset_index()
    plot_df = plot_df.drop("index", axis=1)

    plot_df = apply_aliases(plot_df)
    plot_df = plot_df.set_index("query")

    # import pdb; pdb.set_trace()

    ax = plot_df.plot.bar(stacked=True)
    ax.legend(loc="upper center", ncol=len(plot_df.columns), bbox_to_anchor=(0.5, 1.09))

    plt.savefig("SEC_STORAGE.pdf")

def tee_overhead(pure_host, vanilla_ndp, secndp, pure_host_secure, all_offload):
    tee_queries = [4]

    ph_df = pd.read_csv(pure_host, header=0, sep=',')
    ph_df = ph_df[["kind", "query_no", "query_exec_time"]]
    ph_df = apply_aliases(ph_df)

    vanilla_ndp = pd.read_csv(vanilla_ndp, header=0, sep=',')
    vanilla_ndp = vanilla_ndp[["kind", "query", "total_time"]]
    vanilla_ndp = apply_aliases(vanilla_ndp)

    sn = pd.read_csv(secndp, header=0, sep=',')
    sn = sn[["kind", "query", "total_time"]]
    sn = apply_aliases(sn)

    phs_df = pd.read_csv(pure_host_secure, header=0, sep=',')
    phs_df = phs_df[["kind", "query_no", "query_exec_time"]]
    phs_df = apply_aliases(phs_df)

    all_off = pd.read_csv(all_offload, header=0, sep=',')
    all_off = all_off[["kind", "query", "total_time"]]
    all_off = apply_aliases(all_off)

    plot_df = pd.concat([ph_df, vanilla_ndp, sn, phs_df, all_off])
    plot_df = plot_df[plot_df["query"].isin(tee_queries)].reset_index()
    plot_df = plot_df.drop("index", axis=1)

    g = catplot(
        data=plot_df,
        x=plot_df.columns[0],
        y=plot_df.columns[2],
        kind="bar",
        height=0.25,
        legend=False,
        color='k'
    )

    g.fig.set_figheight(8)
    g.fig.set_figwidth(10)
    g.ax.tick_params(axis='both', which='major', labelsize=15)
    g.ax.set_xlabel(xlabel="",)
    g.ax.set_ylabel(ylabel=plot_df.columns[2], fontsize=15)
    g.savefig("HETERO_TEE.pdf")

def end_end_rel_ndp(pure_host, vanilla_ndp, secndp, pure_host_secure):
    ph_df = pd.read_csv(pure_host, header=0, sep=',')
    vanilla_ndp = pd.read_csv(vanilla_ndp, header=0, sep=',')
    sn = pd.read_csv(secndp, header=0, sep=',')
    phs_df = pd.read_csv(pure_host_secure, header=0, sep=',')

    ph_df = ph_df[["kind", "query_no", "query_exec_time"]]
    ph_df["kind"] = "non-secure"
    vanilla_ndp = vanilla_ndp[["kind", "query", "total_time"]]
    vanilla_ndp["kind"] = "non-secure"
    sn = sn[["kind", "query", "total_time"]]
    sn["kind"] = "secure"
    phs_df = phs_df[["kind", "query_no", "query_exec_time"]]
    phs_df["kind"] = "secure"

    ph_df = apply_aliases(ph_df)
    vanilla_ndp = apply_aliases(vanilla_ndp)
    sn = apply_aliases(sn)
    phs_df = apply_aliases(phs_df)

    ns_plot_df = pd.DataFrame(columns=["kind", "query", "speedup"])
    s_plot_df = pd.DataFrame(columns=["kind", "query", "speedup"])

    ns_plot_df["kind"] = ph_df["kind"]
    ns_plot_df["query"] = ph_df["query"]
    ns_plot_df["speedup"] = vanilla_ndp["Time [s]"]/ph_df["Time [s]"]

    s_plot_df["kind"] = phs_df["kind"]
    s_plot_df["query"] = phs_df["query"]
    s_plot_df["speedup"] = sn["Time [s]"]/phs_df["Time [s]"]

    plot_df = pd.concat([ns_plot_df, s_plot_df])

    g = catplot(
            data=plot_df,
            x=plot_df.columns[1],
            y=plot_df.columns[2],
            kind="bar",
            height=0.25,
            hue="kind",
            legend=False
        )
    g.fig.set_figheight(12)
    g.fig.set_figwidth(24)
    g.ax.tick_params(axis='both', which='major', labelsize=20)
    g.ax.set_xlabel(xlabel=plot_df.columns[1], fontsize=20)
    g.ax.set_ylabel(ylabel=plot_df.columns[2], fontsize=20)
    g.ax.legend(loc="upper left", fontsize=20)
    g.ax.set(ylim=(0, 400))
    g.savefig("END_2_END_REL.pdf")


def main():
    if len(sys.argv) < 2:
        printf("More arguments...")
        sys.exit(1)

    graphs = []

    if sys.argv[1] == "ndp":
        # graphs.append(("END_2_END", host_ndp_plot(sys.argv[2], sys.argv[3], sys.argv[4])))
        # graphs.append(("SEC_STORAGE", secndp_overheads(sys.argv[3], sys.argv[4], sys.argv[5])))
        # graphs.append(("HETERO_TEE", tee_overhead(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[6], sys.argv[7])))
        graphs.append(("REL_NDP", end_end_rel_ndp(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[6])))

    # for name, graph in graphs:
    #     filename = f"{name}.pdf"
    #     print(f"write {filename}")
    #     plt.savefig(filename)

if __name__=="__main__":
    main()