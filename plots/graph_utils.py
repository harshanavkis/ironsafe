import pandas as pd

SYSTEM_ALIASES = {
    "vanilla-ndp": "vn",
    "pure-host-non-secure": "phns",
    "sec-ndp": "sec-ndp",
    "phs": "hos",
    "sns":"sndp",
    "sss": "sos"
}

ROW_ALIASES = dict(
        kind=SYSTEM_ALIASES
    )

COLUMN_ALIASES = {
    "total_time": "Time [s]",
    "query_exec_time": "Time [s]",
    "kind": "system",
    "query_no": "query",
    "speedup": "Speedup",
    "time": "Time [s]",
    "split_point": "Selectivity",
    "scale_factor": "Scale factor",
    "system": "System",
    "query": "Query",
    "overhead": "Overhead"
}

def systems_order(df):
    priorities = {
        "phns": 10,
        "pure-host-secure": 15,
        "vn": 20,
        "sec-ndp": 25,
        "all-offload": 30
    }
    systems = list(df.system.unique())
    return sorted(systems, key=lambda v: priorities.get(v, 100))

def config_order(df):
    priorities = {
        "secure":10,
        "non-secure":15
    }
    systems = list(df.kind.unique())
    return sorted(systems, key=lambda v: priorities.get(v, 100))

def column_alias(name):
    return COLUMN_ALIASES.get(name, name)

def apply_aliases(df):
    for column in df.columns:
        aliases = ROW_ALIASES.get(column, None)
        if aliases is not None:
            df[column] = df[column].replace(aliases)
    return df.rename(index=str, columns=COLUMN_ALIASES)

def change_width(ax, new_value):
    for patch in ax.patches:
        current_width = patch.get_width()
        diff = current_width - new_value
        patch.set_width(new_value)

        patch.set_x(patch.get_x()+diff*0.5)

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

