import sys
import seaborn as sns
import pandas as pd
import matplotlib
import matplotlib as mpl
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker
from graph_utils import apply_aliases, column_alias, systems_order, change_width, config_order
import numpy as np
from scipy import stats

"""
    - first arg: kind of plot(ndp, microbench)
    - subseq args: filenames
        - ndp: pure host, vanilla ndp, secndp, storage-side-secndp
"""

mpl.use("Agg")
mpl.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42

# # plt.rc('text', usetex=True)
# plt.figure(figsize=(10, 10))
# sns.set(rc={'figure.figsize':(5,5)})
# sns.set_style("whitegrid")
# sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})
# sns.set_context(font_scale=1.5)
# sns.set_context("paper", rc={"font.size":10,"axes.titlesize":10,"axes.labelsize":10})
# sns.set_palette(sns.color_palette(palette="gray", n_colors=2))

# plot_queries = [1, 6, 11, 13, 15, 16, 17, 18, 20, 21, 22]
plot_queries = []
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

if sys.argv[1] == "ndp":
    pure_host = sys.argv[2]
    pure_host_secure = sys.argv[3]
    vanilla_ndp = sys.argv[4]
    secndp = sys.argv[5]
    storage_side_secndp = sys.argv[6]
    all_offload = sys.argv[7]
    storage_all_offload = sys.argv[8]

xlabel_fsize = 9
ylabel_fsize = 9
leg_size = 9
tick_fsize = 9

def catplot(**kwargs):
    # kwargs.setdefault("palette", "Greys")
    g = sns.catplot(**kwargs)
    g.despine(top=False, right=False)
    plt.autoscale()
    plt.subplots_adjust(top=0.98)
    return g

def host_ndp_plot():
    ph_df = pd.read_csv(pure_host, header=0, sep=',')
    vanilla_ndp = pd.read_csv(vanilla_ndp, header=0, sep=',')
    sn = pd.read_csv(secndp, header=0, sep=',')

    ph_df = ph_df[["kind", "query_no", "query_exec_time"]]
    vanilla_ndp = vanilla_ndp[["kind", "query", "total_time"]]
    sn = sn[["kind", "query", "total_time"]]

    ph_df = apply_aliases(ph_df)
    vanilla_ndp = apply_aliases(vanilla_ndp)
    sn = apply_aliases(sn)

    plot_df = pd.concat([ph_df, vanilla_ndp, sn, crap_df])
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

def secndp_overheads():
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

    columns = ["query", "ndp", "other", "encryption", "freshness"]
    plot_df = pd.DataFrame(columns=columns)
    plot_df["query"] = vn["query"]
    plot_df["freshness"] = stsn["mt_verify_time"]/sn["total_time"]
    plot_df["encryption"] = (stsn["codec_time"]-stsn["mt_verify_time"])/sn["total_time"]
    plot_df["other"] = (sn["total_time"]-stsn["query_exec_time"]-sn["total_host_query_time"])/sn["total_time"]
    plot_df["ndp"] = ((stsn["query_exec_time"]+sn["total_host_query_time"]-stsn["codec_time"])/sn["total_time"])

    plot_df = plot_df[~plot_df["query"].isin(plot_queries)].reset_index()
    plot_df = plot_df.drop("index", axis=1)

    plot_df = apply_aliases(plot_df)
    plot_df = plot_df.set_index("Query")

    # import pdb; pdb.set_trace()

    # sns.mpl.rc("figure", figsize=(8, 2))
    ax = plot_df.plot.bar(stacked=True, rot=0, color={"freshness":"black", "encryption":"dimgray", "other":"darkgray", "ndp":"lightgray"}, width=0.5, figsize=(5, 2.2))
    ax.legend(loc="upper center", ncol=len(plot_df.columns), bbox_to_anchor=(0.5, 1.2), fontsize=leg_size)
    ax.tick_params(axis='both', which='major', labelsize=tick_fsize)
    ax.set_xlabel(xlabel="Query", fontsize=xlabel_fsize)
    ax.set_ylabel(ylabel="Overhead", fontsize=ylabel_fsize)

    plt.grid(which="major", axis="y")

    plt.savefig("END_END_OVERHEAD.pdf", bbox_inches = 'tight', pad_inches = 0.1)

def tee_overhead():
    tee_queries = [3]

    ph_df = pd.read_csv(pure_host, header=0, sep=',')
    ph_df = ph_df[["kind", "query_no", "query_exec_time"]]
    ph_df = apply_aliases(ph_df)

    vanilla_ndp_df = pd.read_csv(vanilla_ndp, header=0, sep=',')
    vanilla_ndp_df = vanilla_ndp_df[["kind", "query", "total_time"]]
    vanilla_ndp_df = apply_aliases(vanilla_ndp_df)

    sn = pd.read_csv(secndp, header=0, sep=',')
    sn = sn[["kind", "query", "total_time"]]
    sn = apply_aliases(sn)

    phs_df = pd.read_csv(pure_host_secure, header=0, sep=',')
    phs_df = phs_df[["kind", "query_no", "query_exec_time"]]
    phs_df = apply_aliases(phs_df)

    all_off = pd.read_csv(all_offload, header=0, sep=',')
    all_off = all_off[["kind", "query", "total_time"]]
    all_off = apply_aliases(all_off)

    plot_df = pd.concat([ph_df, vanilla_ndp_df, sn, phs_df, all_off])
    plot_df = plot_df[plot_df["query"].isin(tee_queries)].reset_index()
    plot_df = plot_df.drop("index", axis=1)

    g = catplot(
        data=plot_df,
        x=plot_df.columns[0],
        y=plot_df.columns[2],
        kind="bar",
        height=0.25,
        legend=False,
        color='blue',
        order=systems_order(plot_df)
    )

    g.fig.set_figheight(10)
    g.fig.set_figwidth(10)
    g.ax.tick_params(axis='both', which='major', labelsize=15)
    g.ax.set_xlabel(xlabel="",)
    g.ax.set_ylabel(ylabel=plot_df.columns[2], fontsize=15)
    g.savefig("HETERO_TEE.pdf")

def end_end_rel_ndp():
    ph_df = pd.read_csv(pure_host, header=0, sep=',')
    vanilla_ndp_df = pd.read_csv(vanilla_ndp, header=0, sep=',')
    sn = pd.read_csv(secndp, header=0, sep=',')
    phs_df = pd.read_csv(pure_host_secure, header=0, sep=',')

    ph_df = ph_df[["kind", "query_no", "query_exec_time"]]
    ph_df["kind"] = "non-secure"
    vanilla_ndp_df = vanilla_ndp_df[["kind", "query", "total_time"]]
    vanilla_ndp_df["kind"] = "non-secure"
    sn = sn[["kind", "query", "total_time"]]
    sn["kind"] = "secure"
    phs_df = phs_df[["kind", "query_no", "query_exec_time"]]
    phs_df["kind"] = "secure"

    ph_df = apply_aliases(ph_df)
    vanilla_ndp_df = apply_aliases(vanilla_ndp_df)
    sn = apply_aliases(sn)
    phs_df = apply_aliases(phs_df)

    ns_plot_df = pd.DataFrame(columns=["kind", "query", "speedup"])
    s_plot_df = pd.DataFrame(columns=["kind", "query", "speedup"])

    ns_plot_df["kind"] = ph_df["system"]
    ns_plot_df["query"] = ph_df["query"]
    ns_plot_df["speedup"] = ph_df["Time [s]"]/vanilla_ndp_df["Time [s]"]

    s_plot_df["kind"] = phs_df["system"]
    s_plot_df["query"] = phs_df["query"]
    s_plot_df["speedup"] = phs_df["Time [s]"]/sn["Time [s]"]

    # plot_queries = [1, 6, 11, 13, 15, 16, 17, 18, 20, 21, 22]

    # crap_df = [
    #             ["non-secure", 1, 1], ["secure", 1, 1],
    #             ["non-secure", 6, 1], ["secure", 6, 1],
    #             ["non-secure", 11,1], ["secure", 11, 1],
    #             ["non-secure", 13, 1], ["secure", 13, 1],
    #             ["non-secure", 15, 1], ["secure", 15, 1],
    #             ["non-secure", 16, 1], ["secure", 16, 1],
    #             ["non-secure", 17, 1], ["secure", 17, 1],
    #             ["non-secure", 18, 1], ["secure", 18, 1],
    #             ["non-secure", 20, 1], ["secure", 20, 1],
    #             ["non-secure", 21, 1], ["secure", 21, 1],
    #             ["non-secure", 22, 1], ["secure", 22, 1],
    #         ]
    # crap_df = pd.DataFrame(crap_df)
    # crap_df.columns = ["kind", "query", "speedup"]

    plot_df = pd.concat([ns_plot_df, s_plot_df])

    plot_df = plot_df[~plot_df["query"].isin(plot_queries)].reset_index()
    plot_df = plot_df.drop("index", axis=1)

    # plot_df = pd.concat([plot_df, crap_df])
    plot_df = plot_df.sort_values("query")
    # plot_df = plot_df.astype({plot_df.columns[1]:str, plot_df.columns[2]:np.float64})
    non_sec = plot_df[plot_df[plot_df.columns[0]]=="non-secure"]
    sec = plot_df[plot_df[plot_df.columns[0]]=="secure"]
    average_row = [["non-secure", 0, stats.gmean(non_sec["speedup"])], ["secure", 0, stats.gmean(sec["speedup"])]]
    plot_df = plot_df.append(pd.DataFrame(average_row, columns=plot_df.columns), ignore_index=True)
    # import pdb; pdb.set_trace()

    # plot_df = apply_aliases(plot_df)

    sns.mpl.rc("figure", figsize=(16, 2))

    g = sns.barplot(
            data=plot_df,
            x=plot_df.columns[1],
            y=plot_df.columns[2],
            hue="kind",
            # legend=False,
            palette=["gray", "black"],
            hue_order=["non-secure", "secure"]
        )
    # g.fig.set_figheight(8)
    # g.fig.set_figwidth(16)
    g.tick_params(axis='both', which='major', labelsize=tick_fsize*1.3)
    g.set_xlabel(xlabel=column_alias(plot_df.columns[1]), fontsize=xlabel_fsize*1.5)
    g.set_ylabel(ylabel=column_alias(plot_df.columns[2]), fontsize=ylabel_fsize*1.5)
    g.legend(loc="upper center", fontsize=leg_size*1.3, bbox_to_anchor=(0.5, 1.25), ncol=2)
    change_width(g, 0.2)

    end_end_rel_ylim = 100
    # g.set_ylim(top=end_end_rel_ylim)
    xticks = g.get_xticks()

    # bar_text = {
    #     1 : "ndp incompatible",
    #     6 : "ndp incompatible",
    #     11 : "ndp incompatible",
    #     13 : "ndp incompatible",
    #     15 : "ndp incompatible",
    #     16 : "ndp incompatible",
    #     17 : "ndp incompatible",
    #     18 : "ndp incompatible",
    #     20 : "ndp incompatible",
    #     21 : "ndp incompatible",
    #     22: "ndp incompatible",
    # }

    bar_height = list(plot_df["speedup"].values)
    # import pdb; pdb.set_trace()
    for i in range(len(g.patches)):
        # if i+1 in plot_queries:
        if g.patches[i].get_height() >=end_end_rel_ylim:
            y_pos = 15
        else:
            y_pos = g.patches[i].get_height()
        g.annotate(f"{g.patches[i].get_height():.1f}x", (g.patches[i].get_x() - 0.01 + g.patches[i].get_width() / 2., y_pos+0.1),
            ha='center', va="bottom", fontsize=leg_size, color='k', annotation_clip=False)
            # pass
        # else:
        #     if bar_height[i*2] > end_end_rel_ylim:
        #         g.annotate(bar_height[i*2], (g.patches[i*2].get_x() + g.patches[i*2].get_width() / 2., 1.2),
        #         ha='center', fontsize=leg_size, color='k', rotation=90)
        #     if bar_height[i*2 + 1] > end_end_rel_ylim:
        #         g.annotate(bar_height[i*2 + 1], (g.patches[i*2 + 1].get_x() + g.patches[i*2 + 1].get_width() / 2., 1.2),
        #         ha='center', fontsize=leg_size, color='k', rotation=90)

    x_labs = g.get_xticklabels()
    x_labs[0] = 'AVG'
    g.set_xticklabels(x_labs)
    g.set_yscale("symlog")
    g.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

    plt.grid(which="major", axis="y")

    plt.savefig("END_2_END_REL.pdf", bbox_inches = 'tight', pad_inches = 0.1)

def ssd_sec_storage_overheads():
    sec_store_queries = [2, 9]
    s_ao_df = pd.read_csv(storage_all_offload, header=None)
    s_ao_df.columns = storage_side_secndp_cols

    ao_df = pd.read_csv(all_offload, header=0)

    s_ao_df = s_ao_df[["query_exec_time", "codec_time", "mt_verify_time"]]
    s_ao_df["query"] = ao_df["query"]
    s_ao_df["codec"] = (s_ao_df["codec_time"] - s_ao_df["mt_verify_time"])/s_ao_df["query_exec_time"]
    s_ao_df["freshness"] = s_ao_df["mt_verify_time"]/s_ao_df["query_exec_time"]
    s_ao_df["query_time"] = (s_ao_df["query_exec_time"]-s_ao_df["codec_time"])/s_ao_df["query_exec_time"]

    codec_df = s_ao_df[["query", "codec"]]
    codec_df.columns = ["query", "overhead"]
    codec_df["operation"] = "codec"
    codec_df = codec_df[["query", "overhead", "operation"]]

    mt_df = s_ao_df[["query", "freshness"]]
    mt_df.columns = ["query", "overhead"]
    mt_df["operation"] = "freshness"
    mt_df = mt_df[["query", "overhead", "operation"]]    

    plot_df = pd.concat([codec_df, mt_df])
    plot_df = plot_df[plot_df["query"].isin(sec_store_queries)].reset_index()
    plot_df = plot_df.drop("index", axis=1)
    import pdb; pdb.set_trace()
    g = catplot(
            data=plot_df,
            x=plot_df.columns[0],
            y=plot_df.columns[1],
            kind="bar",
            height=0.25,
            hue="operation",
            legend=False,
            palette=["gray", "black"]
        )
    g.fig.set_figheight(5)
    g.fig.set_figwidth(5)
    change_width(g.ax, 0.15)
    g.ax.tick_params(axis='both', which='major', labelsize=tick_fsize*2)
    g.ax.set_xlabel(xlabel=column_alias(plot_df.columns[0]), fontsize=xlabel_fsize*2)
    g.ax.set_ylabel(ylabel=column_alias(plot_df.columns[1]), fontsize=ylabel_fsize*2)
    g.ax.legend(loc="upper center", fontsize=leg_size*2, ncol=2, bbox_to_anchor=(0.5, 1.1))
    g.ax.set(ylim=(0, 1))

    plt.grid(which="major", axis="y")

    g.savefig("SEC_STORAGE.pdf")

def selectivity_vs_query():
    # single size and vary filter factor
    data_scale = 3
    dfs = sys.argv[2:]
    dfs = [pd.read_csv(i, header=0) for i in dfs]

    systems = ["phs", "sns", "sss"]

    plot_df = pd.concat(dfs)
    plot_df = plot_df[plot_df["scale_factor"] == data_scale]
    plot_df = plot_df[["system", "split_point", "time"]]
    plot_df = plot_df[plot_df["system"].isin(systems)].reset_index()
    plot_df = plot_df.drop("index", axis=1)
    plot_df = apply_aliases(plot_df)
    plot_df["System"] = plot_df["System"].str.replace("phs", "hos")
    plot_df["System"] = plot_df["System"].str.replace("sns", "sndp")
    plot_df["System"] = plot_df["System"].str.replace("sss", "sos")

    import pdb; pdb.set_trace()

    g = catplot(
            data=plot_df,
            x=column_alias("split_point"),
            y=column_alias("time"),
            hue="System",
            legend=False,
            palette=["lightgray", "darkgray", "black"],
            kind="bar"
        )
    g.fig.set_figheight(5)
    g.fig.set_figwidth(5)
    change_width(g.ax, 0.2)
    g.ax.tick_params(axis='both', which='major', labelsize=tick_fsize*2)
    g.ax.set_xlabel(xlabel=column_alias("split_point"), fontsize=xlabel_fsize*2)
    g.ax.set_ylabel(ylabel=column_alias("time"), fontsize=ylabel_fsize*2)
    g.ax.legend(loc="upper center", fontsize=leg_size*2, ncol=3, bbox_to_anchor=(0.5, 1.1))

    plt.grid(which="major", axis="y")

    g.savefig("SELECTIVITY_VS_QUERY.pdf")

def size_vs_query():
    split_point = 0.2
    data_size = [3, 4, 5]

    dfs = sys.argv[2:]
    dfs = [pd.read_csv(i, header=0) for i in dfs]

    systems = ["phs", "sns", "sss"]

    plot_df = pd.concat(dfs)
    import pdb; pdb.set_trace()
    plot_df = plot_df[plot_df["split_point"] == split_point]
    plot_df = plot_df[["system", "scale_factor", "time"]]
    plot_df = plot_df[plot_df["system"].isin(systems)].reset_index()
    plot_df = plot_df.drop("index", axis=1)
    plot_df = plot_df[plot_df["scale_factor"].isin(data_size)].reset_index()
    plot_df = plot_df.drop("index", axis=1)
    plot_df = apply_aliases(plot_df)
    plot_df["System"] = plot_df["System"].str.replace("phs", "hos")
    plot_df["System"] = plot_df["System"].str.replace("sns", "sndp")
    plot_df["System"] = plot_df["System"].str.replace("sss", "sos")

    g = catplot(
            data=plot_df,
            x=column_alias("scale_factor"),
            y=column_alias("time"),
            hue="System",
            legend=False,
            palette=["lightgray", "darkgray", "black"],
            kind="bar"
        )
    g.fig.set_figheight(5)
    g.fig.set_figwidth(5)
    change_width(g.ax, 0.2)
    g.ax.tick_params(axis='both', which='major', labelsize=tick_fsize*2)
    g.ax.set_xlabel(xlabel=column_alias("scale_factor"), fontsize=xlabel_fsize*2)
    g.ax.set_ylabel(ylabel=column_alias("time"), fontsize=ylabel_fsize*2)
    g.ax.legend(loc="upper center", fontsize=leg_size*2, ncol=3, bbox_to_anchor=(0.5, 1.1))

    plt.grid(which="major", axis="y")

    g.savefig("SIZE_VS_QUERY.pdf")

def io_speedup():
    df = pd.read_csv(sys.argv[2], header=0)
    plot_df = df[["Query", "I/O Ratio"]]
    plot_df = plot_df[~plot_df["Query"].isin(plot_queries)].reset_index()
    plot_df = plot_df.drop("index", axis=1)
    plot_df["I/O Ratio"] = plot_df["I/O Ratio"]
    plot_df.columns = ["Query", "I/O Ratio"]

    average_row = [[0, stats.gmean(plot_df["I/O Ratio"])]]
    plot_df = plot_df.append(pd.DataFrame(average_row, columns=plot_df.columns), ignore_index=True)

    # sns.mpl.rc("figure", figsize=(2, 8))

    g = catplot(
            data=plot_df,
            x=plot_df.columns[0],
            y=plot_df.columns[1],
            legend=False,
            palette = ["black"],
            kind="bar"
        )
    g.ax.set_yscale("symlog")
    g.ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    # plt.autoscale(enable=True, axis='y')
    g.fig.set_figheight(2)
    g.fig.set_figwidth(5)
    change_width(g.ax, 0.5)

    x_labs = g.ax.get_xticklabels()
    x_labs[0] = 'AVG'
    g.ax.set_xticklabels(x_labs)

    # y_labs = g.ax.get_yticklabels()
    # y_labs = [int(float(i.get_text())) for i in y_labs]
    # g.ax.set_yticklabels(y_labs)

    g.ax.tick_params(axis='both', which='major', labelsize=tick_fsize)
    g.ax.set_xlabel(xlabel="Query", fontsize=xlabel_fsize)
    g.ax.set_ylabel(ylabel="I/O Ratio", fontsize=ylabel_fsize)

    for i in range(len(g.ax.patches)):
        y_pos = g.ax.patches[i].get_height()
        g.ax.annotate(f"{g.ax.patches[i].get_height():.1f}x", (g.ax.patches[i].get_x() - 0.01 + g.ax.patches[i].get_width() / 2., y_pos+0.1),
            ha='center', va="bottom", fontsize=leg_size*0.8, color='k', annotation_clip=False)

    # plt.axhline(y=1, color='k', linewidth='0.1')

    plt.grid(which="major", axis="y")

    g.savefig("IO_SPEEDUP.pdf")

def main():
    if len(sys.argv) < 2:
        printf("More arguments...")
        sys.exit(1)

    graphs = []

    if sys.argv[1] == "ndp":
        # graphs.append(("END_2_END", host_ndp_plot()))
        # graphs.append(("END_END_OVERHEAD", secndp_overheads()))
        # graphs.append(("HETERO_TEE", tee_overhead()))
        graphs.append(("REL_NDP", end_end_rel_ndp()))
        # graphs.append(("SEC_STORAGE", ssd_sec_storage_overheads()))

    if sys.argv[1] == "sel":
        # selectivity_vs_query()
        size_vs_query()

    if sys.argv[1] == "io-speed":
        io_speedup()

    # for name, graph in graphs:
    #     filename = f"{name}.pdf"
    #     print(f"write {filename}")
    #     plt.savefig(filename)

if __name__=="__main__":
    main()