import sys
import seaborn as sns
import pandas as pd

from plot import catplot
from matplotlib import pyplot as plt
from graph_utils import change_width

def main():
    data = sys.argv[1:]
    data = [pd.read_csv(i, header=None) for i in data]
    data = [list(i[i.columns[1]].values) for i in data]
    columns = ["1", "2", "3", "4", "5"]
    df = pd.DataFrame(data)
    df = df.transpose()
    df = df*1000
    df.columns = columns

    g = catplot(
        data = df,
        kind="bar",
        color='k',
    )

    g.fig.set_figheight(2)
    g.fig.set_figwidth(2)
    g.ax.set_ylabel("Time [ms]", fontsize=10)
    g.ax.set_xlabel("Use case", fontsize=10)
    change_width(g.ax, 0.3)
    plt.grid(which="major", axis="y")
    g.savefig("USE_CASES.pdf")
    

if __name__ == "__main__":
    main()