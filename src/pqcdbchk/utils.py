import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def alk_gfw_duplicates(
    df: pd.DataFrame, target_column: str
) -> tuple[int, pd.DataFrame]:
    """
    Find duplicate rows in a DataFrame based on the target column.
    """
    if target_column not in df.columns:
        raise ValueError(f"{target_column} not in DataFrame columns")
    dups = df.dropna(subset=[target_column])
    dups = dups[["element", "species", target_column, "source"]].drop_duplicates(
        subset=["element", "species", target_column]
    )
    dups = dups[dups.duplicated(subset=["element", "species"], keep=False)].sort_values(
        by=["element"]
    )
    dif = dups.groupby(["element", "species"]).nunique()
    unique_count = dif.shape[0]
    return unique_count, dups


def remove_ones_full(equation: pd.Series) -> pd.Series:
    """removes all instances of '1' from a series of equations"""
    ones = re.compile(r"\b1\.0{0,4}\s?")
    return equation.str.replace(ones, "", regex=True)


def equation_duplicates(
    df: pd.DataFrame, column_of_interest: str
) -> tuple[int, pd.DataFrame]:
    """
    Find duplicate rows in a DataFrame based on the equation column.
    """
    if column_of_interest not in df.columns:
        raise ValueError(f"{column_of_interest} not in DataFrame columns")
    # remove all whitespace from the equation column
    dups = pd.DataFrame()
    dups["equation"] = df["equation"].str.replace(" ", "")
    # dups = remove_ones_full(df['equation'])
    dups = df.drop_duplicates(subset=["equation", column_of_interest])
    dups = dups.dropna(subset=[column_of_interest])
    dups = dups[dups.duplicated(subset=["equation"], keep=False)].sort_values(
        by=["equation"]
    )
    return dups["equation"].nunique(), dups


def plot_source_hist(
    df: pd.DataFrame,
    title: str = None,
    rotation: int = 45,
    ax: plt.Axes = None,
    color: str = "blue",
    label: str = None,
) -> None:
    """
    Plot the distribution of conflicting attributes in a DataFrame on the given axes.

    Parameters:
    df (pd.DataFrame): The data frame containing the data to plot.
    title (str): The title of the plot.
    rotation (int): The rotation angle of the x-axis labels.
    ax (plt.Axes): Existing axes to plot on. If None, creates a new figure and axes.
    color (str): Color of the histogram.
    label (str): Label for the histogram (for legend).

    Returns:
    None
    """
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure  # Get the figure from the existing axes

    sns.histplot(data=df, x="source", ax=ax, color=color, label=label, alpha=0.7)
    ax.set_xlabel("Source")
    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.set_xticks(ax.get_xticks())

    # Adjust xticklabels using re.sub to replace '#', '.dat', and '_'
    substrings_to_replace = ["#", ".dat", "_"]
    pattern = "|".join(map(re.escape, substrings_to_replace))

    ax.set_xticklabels(
        [re.sub(pattern, "", label.get_text()) for label in ax.get_xticklabels()],
        rotation=rotation,
    )

    if label:
        ax.legend(loc="best", frameon=False)

    # Optional: Remove top and right spines for a cleaner look
    sns.despine(ax=ax)

    # Add a grid with reduced opacity for better readability
    ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.7)
