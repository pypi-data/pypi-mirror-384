import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def setup_svg_output():
    """Configure matplotlib to output SVG in Jupyter notebooks."""
    try:
        from IPython import get_ipython

        ipython = get_ipython()
        if ipython is not None:
            ipython.run_line_magic("config", "InlineBackend.figure_formats = ['svg']")
    except (ImportError, AttributeError):
        # Not in IPython/Jupyter environment, or magic not available
        pass


class Plotter:
    """Initialize the Plotter with a DataFrame of contributions obtained by the `Fetcher`.

    Args:
        df: DataFrame containing contribution data with columns: author, type, date, repo.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        setup_svg_output()
        sns.set_theme()

    def plot_total_number_by_author_by_type(
        self,
        top_n: int = 10,
        start_date: str = None,
    ):
        """Plot total contributions by author, grouped by contribution type.

        Creates a bar chart showing the number of commits, pull requests, and issues
        for the top N contributors.

        Args:
            top_n: Number of top contributors to display. Defaults to 10.
            exclude_author: Author to exclude from the plot. Defaults to "github-actions[bot]".
            start_date: Only include contributions on or after this date (format: "YYYY-MM-DD").
                       Defaults to None (no filter).
        """
        self._plot_contributions(
            x="author",
            hue="type",
            top_n=top_n,
            start_date=start_date,
        )

    def plot_number_by_month_by_author(
        self,
        top_n: int = 10,
        type_filter: str = "pr",
        start_date: str = None,
    ):
        """Plot contributions over time by author.

        Creates a bar chart showing contributions aggregated by month, with different
        colors for each author. Useful for tracking contributor activity over time.

        Args:
            top_n: Number of top contributors to display. Defaults to 10.
            exclude_author: Author to exclude from the plot. Defaults to "github-actions[bot]".
            type_filter: Show only this type of contribution ("commit", "issue", or "pr").
                        Defaults to "pr".
            start_date: Only include contributions on or after this date (format: "YYYY-MM-DD").
                       Defaults to None (no filter).
        """
        self._plot_contributions(
            x="time",
            hue="author",
            top_n=top_n,
            type_filter=type_filter,
            start_date=start_date,
        )

    def _plot_contributions(
        self,
        x: str = "author",
        hue: str = "type",
        top_n: int = 10,
        exclude_authors: list[str] = None,
        time_aggregation: str = "month",
        type_filter: str = None,
        start_date: str = None,
    ):
        """A configurable plot showing contributions.

        Args:
            x: Variable to plot on x-axis. Options: "author", "time". Defaults to "author".
            hue: Variable to use for color grouping. Options: "type", "author". Defaults to "type".
            top_n: Number of top items to show (authors or time periods). Defaults to 10.
            exclude_authors: Author to exclude from the plot. Defaults to "github-actions[bot]".
            time_aggregation: Time aggregation level when x="time". Options: "day", "week", "month", "year". Defaults to "month".
            type_filter: Filter to specific contribution type. Options: "commit", "issue", "pr", or None for all types.
            start_date: Filter contributions to only include those on or after this date. Format: "YYYY-MM-DD". Defaults to None (no filter).
        """
        if exclude_authors is None:
            exclude_authors = ["github-actions[bot]", "invalid-email-address"]
        df = self.df[~self.df.author.isin(exclude_authors)].copy()

        # Convert date column to datetime
        df["date"] = pd.to_datetime(df["date"])

        # Filter by start_date if specified
        if start_date is not None:
            start_date_dt = pd.to_datetime(start_date)
            df = df[df["date"] >= start_date_dt]

        # Filter by type if specified
        if type_filter is not None:
            if type_filter not in ["commit", "issue", "pr"]:
                raise ValueError(
                    f"Invalid type_filter: {type_filter}. Must be 'commit', 'issue', 'pr', or None"
                )
            df = df[df.type == type_filter]

        # Prepare data based on configuration
        if x == "time":
            # Aggregate by time period
            if time_aggregation == "day":
                df["time_period"] = df["date"].dt.to_period("D").astype(str)
            elif time_aggregation == "week":
                df["time_period"] = df["date"].dt.to_period("W").astype(str)
            elif time_aggregation == "month":
                df["time_period"] = df["date"].dt.to_period("M").astype(str)
            elif time_aggregation == "year":
                df["time_period"] = df["date"].dt.to_period("Y").astype(str)
            else:
                raise ValueError(f"Invalid time_aggregation: {time_aggregation}")

            if hue == "author":
                # Group by time and author
                plot_data = (
                    df.groupby(["time_period", "author"])
                    .size()
                    .reset_index(name="Count")
                )

                # Get top N authors by total contributions
                top_authors = df.groupby("author").size().nlargest(top_n).index
                plot_data = plot_data[plot_data["author"].isin(top_authors)]

                # Sort time periods
                plot_data = plot_data.sort_values("time_period")

                x_var = "time_period"
                hue_var = "author"
                x_label = f"Time ({time_aggregation})"
                hue_label = "Author"
                palette = None  # Use default palette for many authors

            elif hue == "type":
                # Group by time and type
                plot_data = (
                    df.groupby(["time_period", "type"]).size().reset_index(name="Count")
                )

                # Map type names
                type_map = {"commit": "Commits", "issue": "Issues", "pr": "PRs"}
                plot_data["type"] = plot_data["type"].map(type_map)

                # Sort time periods and optionally limit to top_n periods
                plot_data = plot_data.sort_values("time_period")
                time_periods = (
                    plot_data.groupby("time_period")["Count"]
                    .sum()
                    .nlargest(top_n)
                    .index
                )
                plot_data = plot_data[plot_data["time_period"].isin(time_periods)]
                plot_data = plot_data.sort_values("time_period")

                x_var = "time_period"
                hue_var = "type"
                x_label = f"Time ({time_aggregation})"
                hue_label = "Activity Type"
                palette = ["#2ecc71", "#3498db", "#e74c3c"]
            else:
                raise ValueError(f"Invalid hue for x='time': {hue}")

        elif x == "author":
            if hue == "type":
                # Original behavior: group by author and type
                commits_df = df[df.type == "commit"]
                issues_df = df[df.type == "issue"]
                prs_df = df[df.type == "pr"]

                contributors_data = pd.concat(
                    [
                        prs_df.groupby("author").size().rename("PRs"),
                        commits_df.groupby("author").size().rename("Commits"),
                        issues_df.groupby("author").size().rename("Issues"),
                    ],
                    axis=1,
                ).fillna(0)

                contributors_data["Total"] = contributors_data.sum(axis=1)
                contributors_data = contributors_data.sort_values(
                    "Total", ascending=False
                ).head(top_n)
                contributors_data = contributors_data.drop("Total", axis=1)

                plot_data = contributors_data.reset_index().melt(
                    id_vars="author", var_name="Activity Type", value_name="Count"
                )

                x_var = "author"
                hue_var = "Activity Type"
                x_label = "Author"
                hue_label = "Activity Type"
                palette = ["#2ecc71", "#3498db", "#e74c3c"]

            elif hue == "time":
                raise ValueError("hue='time' is not supported when x='author'")
            else:
                raise ValueError(f"Invalid hue for x='author': {hue}")
        else:
            raise ValueError(f"Invalid x value: {x}")

        # Calculate date range
        min_date = df["date"].min()
        max_date = df["date"].max()
        date_range = (
            f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
        )

        # Get repositories
        repos_list = sorted(df["repo"].unique())
        repos_chunks = [repos_list[i : i + 10] for i in range(0, len(repos_list), 10)]
        repos = "\n".join([", ".join(chunk) for chunk in repos_chunks])

        # Build title with type filter info if applicable
        title_parts = [f"Contributions to repositories: {repos}"]

        # Build title with type filter info if applicable
        title_parts = [f"Contributions to repositories: {repos}"]
        if type_filter is not None:
            type_name_map = {"commit": "Commits", "issue": "Issues", "pr": "PRs"}
            title_parts[0] = f"{type_name_map[type_filter]} to repositories: {repos}"
        title_parts.append(date_range)
        title = "\n".join(title_parts)

        # Set up the plot
        fig_width = max(12, len(plot_data[x_var].unique()) * 0.8)
        plt.figure(figsize=(fig_width, 8))

        # Create the plot
        ax = sns.barplot(
            data=plot_data, x=x_var, y="Count", hue=hue_var, palette=palette
        )

        # Add value labels only if not too many bars
        if len(plot_data[x_var].unique()) <= 20:
            for c in ax.containers:
                ax.bar_label(c, label_type="edge", fmt="%d", padding=3)

        # Customize the plot
        plt.title(title)
        plt.ylabel("Number of contributions")
        plt.xlabel(x_label)

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha="right")

        # Position legend
        plt.legend(title=hue_label, loc="upper right")

        # Ensure all labels are visible
        plt.tight_layout()
