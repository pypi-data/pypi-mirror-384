from pathlib import Path
from typing import Union

import pandas as pd


class Color:
    """
    Utility class to represent colors.
    """
    __color: str

    def __init__(self, color: str):
        self.__color = color

    @staticmethod
    def cast(color: Union['Color', str]):
        """
        Cast Color or str to Color.

        Args:
            color (Color or str): The color to cast

        Returns:
            The argument itself if it is an instance of Color, a new instance of Color otherwise
        """

        return color if isinstance(color, Color) else Color(color)

    def __is_fallback(self) -> bool:
        return fallback_color == self

    def __or__(self, other):
        return Color.cast(other) if self.__is_fallback() else self

    def __eq__(self, __value):
        return self.__color == Color.cast(__value).__color

    def __str__(self):
        return self.__color

    def rgba(self, alpha: float = None):
        """
        Provides the RGBA representation of a color, using the given `alpha` value when provided.

        Args:
            alpha (float, optional): The alpha transparency value (0.0 to 1.0).

        Returns:
            str: The RGBA color string in the format "rgba(r, g, b, a)".
        """

        color = self.__color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        a = alpha if alpha is not None else int(color[6:8], 16) if len(color) == 8 else 1.0
        return f"rgba({r}, {g}, {b}, {a:.2f})"


fallback_color = Color("#000000")
"""Fallback colors in plots.
"""


class Colors:
    """
    Utility class to represent a dict of [Color][energyscope.colors.Color]s with fallback mechanism.
    
    Colors can be accessed as in a regular dict.  
    If the key is not found, will try to fall back removing the text after the last underscore until it finds a match.  
    If no match can be found, [energyscope.colors.fallback_color][] will be used.
    
    Ex: colors['RES_WIND_ONSHORE'] will 
      1. look for the key 'RES_WIND_ONSHORE' and return the corresponding value if exists
      1. if 'RES_WIND_ONSHORE' is not found, look for 'RES_WIND' and return the corresponding value if exists
      1. if 'RES_WIND' is not found, look for 'RES' and return the corresponding value if exists
      1. if 'RES' is not found, return [energyscope.colors.fallback_color][]
    
    Examples:
        Examples should be written in doctest format, and should illustrate how
        to use the function.

        >>> colors = Colors({"ELECTRICITY_LV": "#0000FF", "ELECTRICITY": "#FF0000"})
        >>> print(colors["ELECTRICITY_LV"])
        >>> print(colors["ELECTRICITY_OTHER"]) # will fall back to the color of "ELECTRICITY"
        >>> print(colors["UNKNOWN"]) # will fall back to `fallback_color`
        #0000FF
        #FF0000
        #000000

    """
    __colors: dict[str, Color]
    __fallback: Color

    def __init__(self,
                 colors: dict[str, Union[Color, str]] = None,
                 fallback: Union[Color, str] = fallback_color):
        if colors:
            self.__colors = {k: Color.cast(c) for k, c in colors.items()}
        else:
            __colors = default_colors
        self.__fallback = Color.cast(fallback)

    @staticmethod
    def from_csv(filepath: Union[str, Path]) -> 'Colors':
        """
        Creates a Colors object from a CSV file.
        
        Args:
            filepath (str or Path): the path to the CSV file  
                The CSV file must contain the following columns: Name and Color.  
                All the others columns will be ignored.
        
        Returns:
            the Colors object 
        """
        df = pd.read_csv(filepath, usecols=['Name', 'Color'])
        return Colors({row['Name']: row['Color'] for _, row in df.iterrows()})

    @staticmethod
    def cast(colors: Union['Self', dict]):
        """
        Cast Colors or dict to Colors.

        Args:
            colors (Colors or dict): The colors to cast

        Returns:
            The argument itself if it is an instance of Colors, a new instance of Colors otherwise
        """

        return colors if isinstance(colors, Colors) else Colors(colors)

    def __getitem__(self, key: str) -> Color:
        if not key:
            return fallback_color
        if key in self.__colors:
            return self.__colors[key]
        else:
            return self[key.rpartition('_')[0]]

    def __or__(self, colors: Union['Self', dict[str, Color]]) -> 'Self':
        return Colors(self.__colors | colors.__colors) if isinstance(colors, Colors) else Colors(self.__colors | colors)


default_colors = Colors({
    "GASOLINE": "#808080",
    "BIO_DIESEL": "#6B8E23",
    "DIESEL": "#D3D3D3",
    "URANIUM": "#66ff33",
    "NG": "#FFD700",
    "SNG": "#FFE100",
    "LFO": "#8B008B",
    "COAL": "#A0522D",
    "HYDRO": "#00CED1",
    "WASTE": "#FA8072",
    "SOLAR": "#FFFF00",
    "GEOTHERMAL": "#FF0000",
    "H2": "#FF00FF",
    "RES_WIND": "#FFA500",
    "HEAT_HT": "#DC143C",
    "ELECTRICITY": "#00BFFF",
    "EUD_ELECTRICITY": "#00BFFF",
    "ETHANOL": "#E1DA00",
    "AMMONIA": "#C3DA00",
    "METHANOL": "#A5DA00",
    "DME": "#87DA00",
    "CO2": '#545454',
    "WOOD": "#CD853F",
    "WET_BIOMASS": "#b37b44",
    "PLANT": "#d4904e",
    "HEAT": "#B51F1F",
    "MOB": "#FF69B4",

    # Categories
    "Electricity": "#00BFFF",  # Light Blue
    "Mobility": "#8B0000",  # Dark Red (Combined-Cycle Gas)
    "Electric Infrastructure": "#000000",  # Black (Oil)
    "Gas Infrastructure": "#B22222",  # Firebrick (Open-Cycle Gas)
    "Wind": "#0000FF",  # Blue (Onshore Wind)
    "WIND": "#0000FF",  # Blue (Onshore Wind)
    "PV": "#FFD700",  # Gold (Solar)
    "Geothermal": "#D3B9DA",  # Light Purple (Geothermal)
    "Hydro River & Dam": "#008080",  # Teal (Reservoir & Dam)
    "Industry": "#006400",  # Dark Green (Biomass)
    "Low Temperature Heat": "#FFA500",  # Orange (Nuclear)
    "Hydro Storage": "#00CED1",  # Dark Turquoise (Pumped Hydro Storage)
    "Storage": "#ADD8E6",  # Light Blue (Offshore Wind AC)
    "Electrolysis": "#66CDAA",  # Medium Aquamarine (Run of River)
    "Carbon Capture": "#A52A2A"  # Brown (Lignite)
})
"""Default colors used in plots.
"""
