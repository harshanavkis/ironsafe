import pandas as pd

SYSTEM_ALIASES = {
    "vanilla-ndp": "vn",
    "pure-host-non-secure": "phns",
    "sec-ndp": "sec-ndp"
}

ROW_ALIASES = dict(
        kind=SYSTEM_ALIASES
    )

COLUMN_ALIASES = {
    "total_time": "Time [s]",
    "query_exec_time": "Time [s]",
    "kind": "system",
    "query_no": "query"
}

def systems_order(df):
    priorities = {
        "pure-host": 10,
        "vanilla-ndp": 15,
    }
    systems = list(df.system.unique())
    return sorted(systems, key=lambda v: priorities.get(v, 100))

def column_alias(name):
    return COLUMN_ALIASES.get(name, name)

def apply_aliases(df):
    for column in df.columns:
        aliases = ROW_ALIASES.get(column, None)
        if aliases is not None:
            df[column] = df[column].replace(aliases)
    return df.rename(index=str, columns=COLUMN_ALIASES)

def apply_to_graphs(ax, legend, legend_cols, width):
    # change_width(ax, 0.405)
    change_width(ax, width)

    ax.set_xlabel("")
    ax.set_ylabel(ax.get_ylabel(), size=7)
    ax.set_xticklabels(ax.get_xticklabels(), size=7)
    ax.set_yticklabels(ax.get_yticklabels(), size=7)

    # set_size(2.4, 2.4, ax)

    if legend:
        ax.legend(loc="best")

