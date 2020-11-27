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

plot_queries = [2, 3, 4, 5, 8, 9, 13, 21]
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

def catplot(**kwargs):
    # kwargs.setdefault("palette", "Greys")
    g = sns.catplot(**kwargs)
    g.despine(top=False, right=False)
    plt.autoscale()
    plt.subplots_adjust(top=0.98)
    return g

def host_ndp_plot(pure_host, vanilla_ndp):
    ph_df = pd.read_csv(pure_host, header=0, sep=',')
    vanilla_ndp = pd.read_csv(vanilla_ndp, header=0, sep=',')


    ph_df = ph_df[["kind", "query_no", "query_exec_time"]]
    vanilla_ndp = vanilla_ndp[["kind", "query", "total_time"]]

    ph_df = apply_aliases(ph_df)
    vanilla_ndp = apply_aliases(vanilla_ndp)

    plot_df = pd.concat([ph_df, vanilla_ndp])
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
    g.ax.legend(loc="upper center", fontsize=20)
    g.savefig("HOST_VS_VANILLA.png")

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
    sn = sn[["kind", "query", "total_time"]]

    stsn = pd.read_csv(storage_side_secndp, header=None, sep=',')
    # import pdb; pdb.set_trace()
    stsn.columns = storage_side_secndp_cols
    stsn["query"] = vn["query"]
    stsn = stsn[["query", "codec_time", "mt_verify_time"]]

    columns = ["query", "e2e-secndp", "e2e-secndp-enc", "e2e-secndp-none", "e2e-vanilla-ndp"]
    plot_df = pd.DataFrame(columns=columns)
    plot_df["query"] = vn["query"]
    plot_df["e2e-secndp"] = sn["total_time"]
    plot_df["e2e-secndp-enc"] = (sn["total_time"]-stsn["mt_verify_time"])
    plot_df["e2e-secndp-none"] = (sn["total_time"]-stsn["codec_time"])
    plot_df["e2e-vanilla-ndp"] = vn["total_time"]

    plot_df = plot_df[plot_df["query"].isin(plot_queries)].reset_index()
    plot_df = plot_df.drop("index", axis=1)

    plot_df = apply_aliases(plot_df)

    import pdb; pdb.set_trace()
    
    indices = np.arange(len(plot_queries))
    width=0.8
    plt.bar(indices, plot_df["e2e-secndp"].values, color='r', width=width, label="Freshness overhead")
    plt.bar(indices, plot_df["e2e-secndp-enc"].values, color='g', width=width, label="Encryption overhead")
    plt.bar(indices, plot_df["e2e-secndp-none"].values, color='b', width=width, label="TLS and other overhead")
    plt.bar(indices, plot_df["e2e-vanilla-ndp"].values, color='k', width=width, label="vanilla-ndp")
    plt.xticks(indices, plot_df["query"])
    plt.legend(loc="upper left")

    plt.savefig("VANILLA_VS_SEC.png")

    # return graphs

def main():
    if len(sys.argv) < 2:
        printf("More arguments...")
        sys.exit(1)

    graphs = []

    if sys.argv[1] == "ndp":
        # graphs.append(("HOST_VS_VANILLA", host_ndp_plot(sys.argv[2], sys.argv[3])))
        graphs.append(("VANILLA_VS_SEC", secndp_overheads(sys.argv[3], sys.argv[4], sys.argv[5])))

    # for name, graph in graphs:
    #     filename = f"{name}.pdf"
    #     print(f"write {filename}")
    #     plt.savefig(filename)

if __name__=="__main__":
    main()