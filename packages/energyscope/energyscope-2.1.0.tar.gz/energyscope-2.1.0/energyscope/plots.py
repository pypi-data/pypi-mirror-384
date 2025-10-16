from plotly import graph_objects as go
import numpy as np
import pandas as pd
import os
import seaborn as sns
import matplotlib.dates as mdates
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import pandas as pd
import numpy as np
from pandas.api.types import (
    is_integer_dtype,
    is_datetime64_any_dtype,
    is_period_dtype,
)
from ipywidgets import Dropdown, HBox, VBox, Button, Output
from ipywidgets import Dropdown, HBox, VBox, Button, Output
import matplotlib.pyplot as plt
from typing import Union

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from energyscope.colors import default_colors, Color, Colors
from energyscope.result import Result


def _create_sankey_figure(df_flow: pd.DataFrame, colors: Colors) -> go.Figure:
    """
    Creates a Sankey diagram from the processed flow data.

    This function generates a Sankey diagram using the provided flow data.
    It supports custom color mappings for different technologies and applies
    them to the links in the diagram. The resulting figure can be displayed
    or saved as an HTML file.

    Args:
        df_flow (pd.DataFrame):
            A DataFrame containing the processed flow data, with columns
            for 'source', 'target', and 'value' representing the flow
            between different nodes.

        colors (dict, optional):
            A dictionary of custom colors mapping technology names to
            hexadecimal color codes. If provided, these colors will override
            the default color mappings for the corresponding technologies.
            The dictionary format should be:
            {"TECH_NAME": "#HEXCOLOR", ...}

            Example:
                custom_colors = {
                    "GASOLINE": "#FF0000CC",
                    "BIO_DIESEL": "#00FF00CC",
                    "DIESEL": "#0000FFCC",
                    # Add more as needed
                }

    Returns:
        go.Figure:
            A Plotly Figure object representing the Sankey diagram. This
            can be displayed using `fig.show()` or saved to an HTML file
            using `fig.write_html()`.

    Example:
        # Assuming df_flow is your processed data and you want to apply custom colors:
        fig = _build_sankey(df_flow, custom_colors={"GASOLINE": "#FF0000CC"})
        fig.show()  # To display the diagram
        fig.write_html("output/sankey_diagram.html")  # To save the diagram
    """

    pd.set_option('future.no_silent_downcasting', True)

    df_flow['color'] = df_flow.apply(lambda row: str(colors[row['target']] | colors[row['source']]), axis=1)
    node = np.unique(np.concatenate((df_flow['source'].unique(), df_flow['target'].unique())))
    df_sankey = df_flow.replace(node, range(len(node)))

    opacity = 0.5

    fig = go.Figure(data=[go.Sankey(
        valueformat=".0f",
        valuesuffix="",
        node=dict(
            pad=15,
            thickness=15,
            line=dict(color="black", width=0.5),
            label=node,
            color="#DCDCDC"
        ),
        link=dict(
            source=df_sankey['source'],
            target=df_sankey['target'],
            value=df_sankey['value'],
            label=df_sankey['value'],
            color=df_sankey['color'].apply(lambda c: Color(c).rgba(opacity))
        )
    )])
    fig.update_layout(title_text="Sankey Diagram", font_size=10, template = "plotly", font_color="black")

    return fig


def generate_sankey_flows(results: Result, aggregate_mobility, aggregate_grid, aggregate_technology,
                          run_id) -> pd.DataFrame:
    """
    Processes the `Result` object to transform and filter flow data for Sankey diagram visualization.

    This function takes in a `Result` object, which contains various data frames and parameters
    from an energy modeling process, and performs several transformations and aggregations.
    The goal is to prepare the flow data for use in a Sankey diagram.

    Args:
        results (Result):
            A `Result` object containing dictionaries of data frames for constraints,
            parameters, objectives, sets, and variables.

    Returns:
        pd.DataFrame:
            A processed DataFrame with 'source', 'target', and 'value' columns,
            ready for Sankey diagram visualization.
    """

    df_flow = results.postprocessing['df_monthly'].loc[results.postprocessing['df_monthly']['Run'] == run_id, :]

    df_flow = df_flow.groupby(['Technologies', 'Flow']).sum().rename(columns={'Monthly_flow': 'value'}).loc[:,
              ['value']].reset_index()

    # Swap target and source for positive values and take absolute value
    df_flow.rename(columns={'Technologies': 'target', 'Flow': 'source'}, inplace=True)
    df_flow.loc[df_flow['value'] > 0, ['target', 'source']] = df_flow.loc[
        df_flow['value'] > 0, ['source', 'target']].to_numpy()
    df_flow['value'] = abs(df_flow['value'])

    # Aggregate and clean data
    df_flow = df_flow.groupby(['target', 'source']).sum().reset_index()
    df_flow.loc[df_flow['target'] == df_flow['source'], 'source'] = 'IMP_' + df_flow.loc[
        df_flow['target'] == df_flow['source'], 'source'].astype(str)
    df_flow = df_flow[~df_flow['source'].str.startswith('IMP_RES')]

    # Drop CO2 flows except specified ones
    df_flow = df_flow[(~df_flow['source'].str.contains("CO2_")) | (df_flow['source'] == 'CO2_TO_DIESEL') | (
            df_flow['source'] == 'CO2_TO_JETFUELS')]
    df_flow = df_flow[(~df_flow['target'].str.contains("CO2_")) | (df_flow['target'] == 'CO2_TO_DIESEL') | (
            df_flow['target'] == 'CO2_TO_JETFUELS')]

    df_flow.sort_values('source', inplace=True)

    # Transform pkm & tkm into GWh
    techno_mob = df_flow.loc[df_flow['target'].str.startswith('MOB_'), :]['target'].unique().tolist()

    df_flow.loc[df_flow['target'].isin(techno_mob), 'value'] = (
        df_flow.loc[df_flow['target'].isin(df_flow.loc[df_flow['target'].isin(techno_mob), 'source']), :]
        .groupby('target')
        .sum()
        .reset_index()
        .sort_values('target')['value']
        .values
    )

    ## Add EUD
    EUD = results.parameters['end_uses_demand_year']
    EUD = EUD.loc[EUD['Run'] == run_id, :]
    EUD = EUD.loc[EUD['end_uses_demand_year'] > 0, :]
    EUD = EUD.reset_index().groupby('index0').sum().reset_index().loc[:, ['index0', 'end_uses_demand_year']]
    EUD = EUD.rename(columns={'index0': 'source', 'end_uses_demand_year': 'value'})
    EUD = EUD.loc[EUD['source'].str.contains('ELECTRICITY'), :]
    EUD['target'] = 'EUD_' + EUD['source']

    df_flow = pd.concat([df_flow, EUD]).reset_index().drop(columns='index')

    ## Aggregate EUD types
    EUD_types = results.sets['END_USES_TYPES_OF_CATEGORY']
    EUD_types_reverse = {item: key for key, values in EUD_types.items() for item in values}

    # Create a mask for rows where 'target' and 'source' need changes
    mask_target = df_flow['target'].isin(EUD_types_reverse.keys())
    mask_source = df_flow['source'].isin(EUD_types_reverse.keys())

    # Apply mapping to 'target' and 'source' columns
    df_flow.loc[mask_target, 'target'] = df_flow.loc[mask_target, 'target'].map(EUD_types_reverse)
    df_flow.loc[mask_source, 'source'] = df_flow.loc[mask_source, 'source'].map(EUD_types_reverse)

    # Ensure consistency: if 'target' changes, update corresponding 'source' if necessary
    for index, row in df_flow.iterrows():
        if row['target'] in EUD_types_reverse.values() and row['source'] in EUD_types_reverse.keys():
            df_flow.at[index, 'source'] = EUD_types_reverse[row['source']]

    if aggregate_mobility:
        ## Aggregation of mobility flows
        # Extract rows concerning mobility
        mob_flow = df_flow.loc[df_flow['target'].str.startswith('MOBILITY_'), :]
        mob_flow_2 = df_flow.loc[df_flow['target'].isin(
            df_flow.loc[df_flow['target'].str.startswith('MOBILITY_'), :]['source'].unique()), :]
        # Drop rows concerning mobility as they will be merged
        df_flow = df_flow.loc[~df_flow['target'].str.startswith('MOBILITY_') * ~df_flow['target'].isin(
            df_flow.loc[df_flow['target'].str.startswith('MOBILITY_'), :]['source'].unique()), :]
        # Aggregate value on type of technologies (source) and on type of mobility (target)
        mob_flow = mob_flow.groupby([mob_flow['source'].str.split('_', expand=True).loc[:, 0],
                                     mob_flow['target'].str.rsplit('_', n=1, expand=True).loc[:, 0]]).sum()
        mob_flow_2 = mob_flow_2.groupby(
            [mob_flow_2['target'].str.split('_', expand=True).loc[:, 0], mob_flow_2['source'].values]).sum()
        # Clean df
        mob_flow = mob_flow.drop(['source', 'target'], axis=1)
        mob_flow_2 = mob_flow_2.drop(['source', 'target'], axis=1)
        # Reset index
        mob_flow.reset_index(names=['source', 'target'], inplace=True)
        mob_flow_2.reset_index(names=['target', 'source'], inplace=True)
        # Concat dfs
        df_flow = pd.concat([df_flow, mob_flow, mob_flow_2]).reset_index().drop(columns='index')

    if aggregate_grid:
        ## Add EUD
        # TODO Aggregate flow of the different type of elec
        EUD = results.parameters['end_uses_demand_year']
        EUD = EUD.loc[EUD['end_uses_demand_year'] > 0, :]
        EUD = EUD.reset_index().groupby('index0').sum().reset_index().loc[:, ['index0', 'end_uses_demand_year']]
        EUD = EUD.rename(columns={'index0': 'source', 'end_uses_demand_year': 'value'})
        EUD = EUD.loc[EUD['source'].str.contains('ELECTRICITY'), :]
        EUD['source'] = "ELECTRICITY"
        EUD['target'] = 'EUD_' + EUD['source']

        ## Aggregation of grids flows
        techno_grids = (
        'EXP', 'TRAFO', 'COMP')  # TODO might be replaced by a sets: INFRASTRUCTURE_GAS_GRID INFRASTRUCTURE_ELEC_GRID
        # Extract all flows that have an input/output of ELECTRICITY
        df_elec = df_flow.loc[
                  df_flow['target'].str.contains('ELECTRICITY_') + df_flow['source'].str.contains('ELECTRICITY_'), :]
        # Exception for exports
        df_elec = df_elec.loc[~df_elec['target'].str.contains('EXPORT')]
        df_flow.loc[df_flow['target'].str.contains('EXPORT'), 'source'] = "ELECTRICITY"
        # Drop them from the main df
        df_flow = df_flow.drop(df_elec.index)
        # Remove the flows related to the grid infrastructure
        df_elec = df_elec.loc[~df_elec['target'].str.contains('|'.join(techno_grids)) * ~df_elec['source'].str.contains(
            '|'.join(techno_grids)), :]
        # Rename ELECTRICITY_XXX layers
        df_elec = df_elec.replace(results.sets['ELECTRICITY_LAYERS'].loc[:, 'ELECTRICITY_LAYERS'].values, 'ELECTRICITY')

        # Aggregation for NG
        df_ng = df_flow.loc[df_flow['target'].str.contains('NG_') + df_flow['source'].str.contains('NG_'), :]
        df_flow = df_flow.drop(df_ng.index)
        df_ng = df_ng.loc[~df_ng['target'].str.contains('|'.join(techno_grids)) * ~df_ng['source'].str.contains(
            '|'.join(techno_grids)), :]
        df_ng = df_ng.replace(results.sets['NG_LAYERS'].loc[:, 'NG_LAYERS'].values, 'NG')

        # Aggregation for H2
        df_h2 = df_flow.loc[df_flow['target'].str.contains('H2_') + df_flow['source'].str.contains('H2_'), :]
        df_flow = df_flow.drop(df_h2.index)
        df_h2 = df_h2.loc[~df_h2['target'].str.contains('|'.join(techno_grids)) * ~df_h2['source'].str.contains(
            '|'.join(techno_grids)), :]
        df_h2 = df_h2.replace(results.sets['H2_LAYERS'].loc[:, 'H2_LAYERS'].values, 'H2')

        df_flow = pd.concat([df_flow, df_elec, df_ng, df_h2]).reset_index().drop(columns='index')

    if aggregate_technology:
        # List of technology types to aggregate
        techno_list = ['COGEN', 'BOILER', 'HP', 'DIRECT_ELEC', 'PV', 'RENOVATION']

        # Define a regex pattern with non-capturing groups to match flows like NG_EHP, H2_EHP, IMP_H2_EHP, NG_HP, H2_HP, etc.
        exclude_pattern = r'(?:NG|H2|IMP_H2)_(?:EHP|HP)'

        # Create masks to identify rows with matching patterns in target and source
        exclude_mask_target = df_flow['target'].str.contains(exclude_pattern, regex=True)
        exclude_mask_source = df_flow['source'].str.contains(exclude_pattern, regex=True)

        # Iterate over technologies for aggregation, ensuring exclusions
        for tech in techno_list:
            # Replace only where the rows do not match the exclude pattern
            df_flow.loc[
                (df_flow['target'].str.contains(tech)) & ~exclude_mask_target, 'target'
            ] = tech

            df_flow.loc[
                (df_flow['source'].str.contains(tech)) & ~exclude_mask_source, 'source'
            ] = tech

    return df_flow


def plot_sankey(result: Result, aggregate_mobility: bool = True, aggregate_grid: bool = True,
                aggregate_technology: bool = True, run_id: int = 0, colors: Union[Colors, dict] = None) -> go.Figure:
    df_flow = generate_sankey_flows(result, aggregate_mobility=aggregate_mobility, aggregate_grid=aggregate_grid,
                                    aggregate_technology=aggregate_technology, run_id=run_id)
    return _create_sankey_figure(df_flow, Colors.cast(colors or default_colors))


def plot_distribution(result: list[Result]) -> None:
    return None


def plot_parametrisation(results, variable: str, category: str, labels: dict = None) -> go.Figure:
    """
    Plots the parametrization results by visualizing the specified variable over multiple runs, grouped by a given category.

    Parameters:
    -----------
    results : Result
        A Result object containing the processed output data. 

    variable : str
        The name of the variable to be plotted. This should correspond to a column in the 'df_annual' DataFrame 
        stored within the `results` object.

    category : str
        The grouping category for the plot. This should be a column in the 'df_annual' DataFrame, which will be 
        used to group and color the results (e.g., 'Sector', 'Category').

    labels : dict, optional
        A dictionary of custom labels to use in the plot for axis titles and hover information. This can be used to 
        provide more descriptive or human-readable labels for the plot. Default is an empty dictionary.

        Example:
        ```
        labels = {
            "Run": "Simulation Run",
            "variable": "Variable Name",
            "category": "Technology Sector"
        }
        ```

    Returns:
    --------
    go.Figure
        A Plotly Figure object. This can be displayed using `fig.show()` or saved to an HTML file
        using `fig.write_html()`.

    Example:
    --------
    To plot the annual investment costs for different sectors over multiple runs:

    ```
    plot_parametrisation(results, variable='C_inv_an', category='Sector', labels={'Run': 'Run Number', 'C_inv_an': 'Annual Investment Costs'})
    ```
    """
    labels = labels or {}
    df = results.postprocessing['df_annual']
    df_plot = df.groupby(['Run', category]).sum()
    df_plot['color'] = df_plot.index.get_level_values(1).map(lambda x: str(default_colors[x]))

    fig = px.area(df_plot.reset_index(), x="Run", y=variable, color=category, template = "simple_white", labels=labels)
    return fig


def plot_comparison(results, variable, category, labels=None, run1=None, run2=None) -> go.Figure:
    """
    Plots the parametrization results by visualizing the specified variable for two selected runs using a mirror bar plot.

    Parameters:
    -----------
    results : Result
        A Result object containing the processed output data.
    
    variable : str
        The name of the variable to be plotted. This should correspond to a column in the 'df_annual' DataFrame 
        stored within the `results` object.
    
    category : str
        The grouping category for the plot. This should be a column in the 'df_annual' DataFrame, which will be 
        used to group and color the results (e.g., 'Sector', 'Category').
    
    labels : dict, optional
        A dictionary of custom labels to use in the plot for axis titles and hover information. Default is an empty dictionary.
    
    run1 : int, optional
        The first run to compare in the mirror bar plot.
    
    run2 : int, optional
        The second run to compare in the mirror bar plot.

    Returns:
    --------
    go.Figure
        A Plotly Figure object. This can be displayed using `fig.show()` or saved to an HTML file
        using `fig.write_html()`.
    """
    # Define category color mapping (only for specific categories)
    category_colors = {
        "Electricity": "#808080",  # Gray (Coal)
        "Mobility": "#8B0000",  # Dark Red (Combined-Cycle Gas)
        "Electric Infrastructure": "#000000",  # Black (Oil)
        "Gas Infrastructure": "#B22222",  # Firebrick (Open-Cycle Gas)
        "Wind": "#0000FF",  # Blue (Onshore Wind)
        "PV": "#FFD700",  # Gold (Solar)
        "Geothermal": "#D3B9DA",  # Light Purple (Geothermal)
        "Hydro River & Dam": "#008080",  # Teal (Reservoir & Dam)
        "Industry": "#006400",  # Dark Green (Biomass)
        "Industrial Heat": "#006400",  # Dark Green (Biomass)
        "Domestic Heat": "#FFA500",  # Orange (Nuclear)
        "Hydro Storage": "#00CED1",  # Dark Turquoise (Pumped Hydro Storage)
        "Storage": "#ADD8E6",  # Light Blue (Offshore Wind AC)
        "Electrolysis": "#66CDAA",  # Medium Aquamarine (Run of River)
        "Carbon Capture": "#A52A2A"  # Brown (Lignite)
    }

    # Extract the 'df_annual' DataFrame from the results object
    df = results.postprocessing['df_annual'].reset_index()  # Bring the multi-index levels as columns

    # Filter the DataFrame based on the selected runs
    df_run1 = df[df['Run'] == run1]
    df_run2 = df[df['Run'] == run2]

    # Group by category and sum for each run
    df_run1_grouped = df_run1.groupby(category).sum()[variable]
    df_run2_grouped = df_run2.groupby(category).sum()[variable]

    # Ensure that both DataFrames have the same categories for comparison
    categories = df_run1_grouped.index.union(df_run2_grouped.index)

    # Align the two DataFrames to have the same categories
    df_run1_grouped = df_run1_grouped.reindex(categories, fill_value=0)
    df_run2_grouped = df_run2_grouped.reindex(categories, fill_value=0)
    max_value = max(df_run1_grouped.max(), df_run2_grouped.max())

    # Apply natural breaks (e.g., multiples of 5, 10, 50, 100)
    scale_factor = 10 ** (len(str(int(max_value))) - 1)
    natural_break = np.ceil(max_value / scale_factor) * scale_factor
    tick_step = natural_break / 5  # 5 intervals
    tickvals = np.arange(-natural_break, natural_break + tick_step, tick_step)
    ticktext = [abs(int(i)) for i in tickvals]

    # Calculate the common and additional values between the two runs
    common_values = np.minimum(df_run1_grouped, df_run2_grouped)
    additional_run1 = df_run1_grouped - common_values
    additional_run2 = df_run2_grouped - common_values

    # Fallback to Plotly's default color palette if the theme has no colors
    default_colors = [
        "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
        "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"
    ]

    # Use theme colors or fallback to the default Plotly color palette
    theme_colors = go.layout.Template().layout.colorway or default_colors

    # Fallback to theme colors for categories without predefined colors
    colors = [category_colors.get(cat, theme_colors[i % len(theme_colors)]) for i, cat in enumerate(categories)]

    # Calculate yshift dynamically based on the number of categories
    yshift_delta = max(10, 50 / len(categories))  # Adjusts dynamically; minimum shift is 10

    # Create the mirror bar plot
    fig = go.Figure()

    # Add common values (with transparency) for run1 (negative side)
    fig.add_trace(go.Bar(
        y=categories,
        x=-common_values,  # Plot common values for run1 (negative side)
        orientation='h',
        showlegend=False,
        opacity=0.5,  # Add transparency
        marker=dict(color=colors)  # Apply category colors or theme fallback
    ))

    # Add additional values (without transparency) for run1 (negative side)
    fig.add_trace(go.Bar(
        y=categories,
        x=-additional_run1,  # Plot additional values for run1 (negative side)
        orientation='h',
        showlegend=False,
        marker=dict(color=colors)  # Apply category colors or theme fallback
    ))

    # Add common values (with transparency) for run2 (positive side)
    fig.add_trace(go.Bar(
        y=categories,
        x=common_values,  # Plot common values for run2 (positive side)
        orientation='h',
        showlegend=False,
        opacity=0.5,  # Add transparency
        marker=dict(color=colors)  # Apply category colors or theme fallback
    ))

    # Add additional values (without transparency) for run2 (positive side)
    fig.add_trace(go.Bar(
        y=categories,
        x=additional_run2,  # Plot additional values for run2 (positive side)
        orientation='h',
        showlegend=False,
        marker=dict(color=colors)  # Apply category colors or theme fallback
    ))

    # Add annotations for the total values at each extremity (outside the bar)
    for i, category in enumerate(categories):
        # Run1 (negative side): Total value (common + additional)
        if df_run1_grouped[category] != 0:
            fig.add_annotation(
                x=-df_run1_grouped[category],  # Position at the end of the bar
                y=category,  # Corresponding category
                text=f'{df_run1_grouped[category]:.0f}',  # Rounded to whole numbers
                showarrow=False,
                xanchor="right",  # Align text outside the negative bar (left side)
                font=dict(size=12),
                xshift=-5  # Shift text outside the bar
            )

        # Run2 (positive side): Total value (common + additional)
        if df_run2_grouped[category] != 0:
            fig.add_annotation(
                x=df_run2_grouped[category],  # Position at the end of the bar
                y=category,  # Corresponding category
                text=f'{df_run2_grouped[category]:.0f}',  # Rounded to whole numbers
                showarrow=False,
                xanchor="left",  # Align text outside the positive bar (right side)
                font=dict(size=12),
                xshift=5  # Shift text outside the bar
            )

        # Plot the difference above the difference bar (outside, higher than the bar)
        if additional_run1[category] > 0:  # For run1 (negative side)
            mid_point_run1 = -common_values[category] - (additional_run1[category] / 2)  # Midpoint of the additional bar
            fig.add_annotation(
                x=mid_point_run1,  # Middle of the additional part for run1
                y=category,  # Corresponding category
                text=f'{abs(additional_run1[category]):.0f}',  # Difference (absolute value) rounded
                showarrow=False,
                bgcolor='rgba(255, 255, 255, 0.6)',  # Semi-transparent white background (RGBA format)
                #yshift=yshift_delta,  # Move the text higher above the bar
                font=dict(size=8)  # Smaller font for delta
            )

        if additional_run2[category] > 0:  # For run2 (positive side)
            mid_point_run2 = common_values[category] + (additional_run2[category] / 2)  # Midpoint of the additional bar
            fig.add_annotation(
                x=mid_point_run2,  # Middle of the additional part for run2
                y=category,  # Corresponding category
                text=f'{abs(additional_run2[category]):.0f}',  # Difference (absolute value) rounded
                showarrow=False,
                bgcolor='rgba(255, 255, 255, 0.6)',  # Semi-transparent white background (RGBA format)
                #yshift=yshift_delta,  # Move the text higher above the bar
                font=dict(size=8)  # Smaller font for delta
            )

    # Update layout
    fig.update_layout(
        template="plotly_white",
        title=f"Comparison {labels.get(variable, variable)} between Run {run1} and Run {run2}",
        xaxis=dict(
            title=labels.get(variable, variable) if labels else variable,
            range=[-natural_break, natural_break],  # Symmetrical x-axis limits
            tickvals=tickvals,  # Natural breaks (multiples of 5, 10, 50, 100)
            ticktext=ticktext,  # Symmetric labels
            zeroline=True  # Add zero line for mirror effect
        ),
        yaxis=dict(
            title=None,  # Remove y-axis title
            automargin=True,  # Automatically adjust margins for long labels
            ticklabelposition="outside",  # Ensure labels are placed outside the plot
            ticks="outside",  # Draw ticks outside the plot
            ticklen=20,  # Increase the tick length to add space between labels and plot
            tickcolor='rgba(0,0,0,0)'  # Make the tick marks fully transparent
        ),
        bargap=1 - 1 / 1.618,  # Make bars narrower
        barmode='relative'  # Use 'relative' to ensure stacking works for both positive and negative values
    )





    return fig

def plot_widget_annual_profile_td(
    df,
    day_col="DayOfYear",
    value_col="value",
    rolling_window=7,
    year_for_axis=2024,
    band_k=1.0
):
    """
    Widget to select two technologies and plot their annual profiles.
    """
    def plot_annual_profile(df, tech):
        dsub = df[df["tech_name"] == tech].copy()
        if dsub.empty:
            print(f"No data found for technology '{tech}'.")
            return

        # Aggregate per day and sort
        dplot = (
            dsub.groupby(day_col, as_index=False)[value_col]
                .sum()
                .sort_values(day_col)
                .reset_index(drop=True)
        )

        # Build a proper date axis, robust to dtype of `day_col`
        if is_integer_dtype(dplot[day_col]):
            start = pd.Timestamp(year_for_axis, 1, 1)
            days = dplot[day_col].astype(int).clip(lower=1)
            dplot["date"] = start + pd.to_timedelta(days - 1, unit="D")
        elif is_datetime64_any_dtype(dplot[day_col]) or is_period_dtype(dplot[day_col]):
            if is_period_dtype(dplot[day_col]):
                dplot["date"] = dplot[day_col].dt.to_timestamp().dt.normalize()
            else:
                dplot["date"] = pd.to_datetime(dplot[day_col]).dt.normalize()
            dplot[day_col] = dplot["date"].dt.dayofyear
        else:
            coerced_dt = pd.to_datetime(dplot[day_col], errors="coerce")
            if coerced_dt.notna().all():
                dplot["date"] = coerced_dt.dt.normalize()
                dplot[day_col] = dplot["date"].dt.dayofyear
            else:
                days = pd.to_numeric(dplot[day_col], errors="raise").astype(int)
                start = pd.Timestamp(year_for_axis, 1, 1)
                dplot["date"] = start + pd.to_timedelta(days - 1, unit="D")

        # Rolling stats
        roll = dplot[value_col].rolling(rolling_window, center=True, min_periods=1)
        dplot["rolling_mean"] = roll.mean()
        dplot["rolling_std"]  = roll.std(ddof=1).fillna(0)

        # Variability band
        lo = dplot["rolling_mean"] - band_k * dplot["rolling_std"]
        hi = dplot["rolling_mean"] + band_k * dplot["rolling_std"]

        # Plot
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.fill_between(dplot["date"], lo, hi, alpha=0.15, label=f"±{band_k:g} rolling std")
        ax.plot(dplot["date"], dplot["rolling_mean"], linewidth=2, label=f"Rolling {rolling_window}d mean")
        ax.scatter(dplot["date"], dplot[value_col], s=12, alpha=0.5, label="Daily")

        ax.set_title(f"Annual profile — {tech}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Daily production")
        xmin = pd.Timestamp(dplot["date"].min().year, 1, 1)
        xmax = pd.Timestamp(dplot["date"].max().year, 12, 31)
        ax.set_xlim(xmin, xmax)
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        ax.tick_params(axis="x", rotation=0)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.grid(True, alpha=0.3)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.legend(frameon=False)
        fig.tight_layout()
        plt.show()

    all_techs = sorted(pd.unique(df['tech_name']))
    pick1 = Dropdown(options=all_techs, description='Tech A:', layout={'width': '45%'})
    pick2 = Dropdown(options=all_techs, description='Tech B:', layout={'width': '45%'})
    btn = Button(description='Plot technologies operation', button_style='primary')
    out = Output()

    def on_click(_):
        out.clear_output(wait=True)
        with out:
            plot_annual_profile(df, pick1.value)
            plot_annual_profile(df, pick2.value)

    btn.on_click(on_click)
    display(VBox([HBox([pick1, pick2]), btn, out]))




def plot_sankey_td(ampl):
    """Plot annual energy Sankey diagram
    Parameters
    ----------
    Returns
    -------
    """

    F_t = ampl.get_variable("F_t").get_values().to_pandas(multi_index=True).reset_index().rename(
        columns={"index0": "tech_name", "index1": "h", "index2": "td", "F_t.val": "value"})
    lyrio = ampl.get_parameter("layers_in_out").get_values().to_pandas().reset_index().rename(
        columns={"index0": "tech_name", "index1": "flow_name", "layers_in_out": "value"})
    HOUR_OF_PERIOD = pd.DataFrame(ampl.get_entity("T_H_TD").get_values().to_list(), columns=['i', 'h', 'td']).set_index(
        'i')
    MOB_list = sorted(['MOB_PRIVATE', 'MOB_AVIATION', 'MOB_PUBLIC', 'MOB_FREIGHT_RAIL', 'MOB_FREIGHT_ROAD', 'MOB_FREIGHT_BOAT'])
    list_storage = ampl.get_set("STORAGE_TECH").get_values().to_pandas().index.values

    df_flow = F_t.groupby(['tech_name', 'td']).sum().drop(['h'], axis=1).join(HOUR_OF_PERIOD.groupby('td').count() / 24,
                                                                              on='td')  # Sum hourly profile for each TD + Merge occurence of TD per year
    df_flow = df_flow[df_flow['value'] != 0]  # Keep only non zero flow
    df_flow['value'] = df_flow['value'] * df_flow['h']  # kW * h per td

    df_flow = df_flow.merge(lyrio.rename(columns={'value': 'value_lyrio'}), on='tech_name')  # Merge lyrio flow
    df_flow = df_flow[df_flow['value_lyrio'] != 0]  # Keep only non zero flow
    df_flow['value'] = (df_flow['value_lyrio'] * df_flow['value'])  # kW of demand and supply * h per td

    df_flow.drop(['h', 'value_lyrio'], axis=1, inplace=True)  # Cleaning

    df_flow.rename(columns={'tech_name': 'target', 'flow_name': 'source'}, inplace=True)  # Rename
    df_flow.loc[df_flow['value'] > 0, ['target', 'source']] = df_flow.loc[
        df_flow['value'] > 0, ['source', 'target']].to_numpy()  # Transform negative flow as source
    df_flow['value'] = abs(df_flow['value'])  # Transform source flow to be positive

    df_flow = df_flow.groupby(['target', 'source']).sum().reset_index()  # Aggregate to yearly value
    df_flow.loc[df_flow['target'] == df_flow['source'], 'source'] = 'IMP_' + df_flow.loc[
        df_flow['target'] == df_flow['source'], 'source'].astype(str)  # Transform name imported resources
    df_flow = df_flow[~df_flow.loc[:, 'source'].str.startswith('IMP_RES').values]  # Remove node with IMP_RES

    # Drop CO2 flow
    df_flow = df_flow[~df_flow['source'].str.contains("CO2_")]
    df_flow = df_flow[~df_flow['target'].str.contains("CO2_")]

    df_flow.sort_values('source', inplace=True)

    # Transform pkm & tkm into GWh
    df_flow.loc[df_flow[df_flow['target'].isin(MOB_list)].index, 'value'] = \
    df_flow.loc[df_flow['target'].isin(df_flow.loc[df_flow['target'].isin(MOB_list), 'source']), :].sort_values(
        'target')['value'].values

    # check if there is HVC in the df_flow['target']
    if 'HVC' in df_flow['target'].values:
        # Transform kt into GWh
        df_flow.loc[df_flow['target'] == 'HVC', 'value'] = df_flow.loc[df_flow['target'].isin(
            df_flow.loc[df_flow['target'] == 'HVC', 'source']), :].groupby('target').sum().values


    df_flow = df_flow[df_flow['value'] > 1]  # Remove small flows

    node = np.unique(np.concatenate((df_flow['source'].unique(), df_flow['target'].unique())))  # Get the list of nodes


    # techno_color = pd.read_excel(os.getcwd()+'/ColorSankey.xlsx', index_col=False)
    # df_flow = df_flow.merge(techno_color,on=('target','source'))

    df_sankey = df_flow.replace(node, range(len(node))).infer_objects(copy=False)  # Rename techno into numbers

    opacity = 0.5

    fig = go.Figure(data=[go.Sankey(
        valueformat=".0f",
        valuesuffix="",  # "TWh",
        # Define nodes
        node=dict(
            pad=15,
            thickness=15,
            line=dict(color="black", width=0.5),
            label=node,
            color="cornflowerblue"
        ),
        # Add links
        link=dict(
            source=df_sankey['source'],
            target=df_sankey['target'],
            value=df_sankey['value'],
            label=df_sankey['target'],
            # color =  df_sankey['color'].apply(lambda h: hexToRGB(h,opacity))
        ))])

    fig.update_layout(title_text="Sankey", font_size=10, font_color="black", paper_bgcolor="white")
    fig.write_html(os.getcwd() + "/Sankey.html")
    fig.show()


def hexToRGB(hex, alpha):
    hex = hex.lstrip('#')
    r = int(hex[0:2], 16)
    g = int(hex[2:4], 16)
    b = int(hex[4:6], 16)

    if (alpha):
        return "rgba(%d, %d, %d, %.2f)" % (r, g, b, alpha)
    else:
        return "rgba(%d, %d, %d)" % (r, g, b)




def plot_widget_hourly_profile_td(df_ft, hour_col='h', td_col='td', value_col='value'):
    """
    Widget to select two technologies and plot their hourly profiles by Typical Day.
    """
    def plot_hourly_profile_by_td(df_ft, tech):
        dsub = df_ft[df_ft['tech_name'] == tech].copy()
        dplot = dsub.groupby([hour_col, td_col], as_index=False)[value_col].sum()
        tds = sorted(dplot[td_col].unique())

        plt.figure(figsize=(10, 5))
        for td in tds:
            dtd = dplot[dplot[td_col] == td].sort_values(hour_col)
            plt.plot(dtd[hour_col], dtd[value_col], label=f"TD {td}")

        plt.title(f"Hourly profile by Typical Day — {tech}")
        plt.xlabel("Hour of day")
        plt.ylabel(value_col)
        plt.xticks(range(0, 24, 2))
        plt.grid(True, alpha=0.3)
        plt.legend(title="Typical Day", ncols=2, fontsize='small')
        plt.tight_layout()
        plt.show()

    all_techs = sorted(df_ft['tech_name'].unique())
    pick1 = Dropdown(options=all_techs, description='Tech A:', layout={'width': '45%'})
    pick2 = Dropdown(options=all_techs, description='Tech B:', layout={'width': '45%'})
    btn = Button(description='Plot both', button_style='primary')
    out = Output()

    def on_click(_):
        out.clear_output(wait=True)
        with out:
            plot_hourly_profile_by_td(df_ft, pick1.value)
            plot_hourly_profile_by_td(df_ft, pick2.value)

    btn.on_click(on_click)
    return display(VBox([HBox([pick1, pick2]), btn, out]))
