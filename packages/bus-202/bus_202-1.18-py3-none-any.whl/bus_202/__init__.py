import pandas as pd
from pathlib import Path
from .data_visualization.trim import trim
from .data_visualization.boxplot import boxplot
from .data_visualization.histogram import histogram
from .data_visualization.scatter import scatter
from .data import (
    sp1500_cross_sectional, sp1500_panel, 
    ceo_comp, a1, netflix_content, 
    olympic_medals, world_cup_goals,
    midterm)
from .stats.ci import ci
from .stats.reg import reg

__all__ = [
    'trim', 'boxplot', 'histogram', 'ci', 
    'sp1500_cross_sectional', 'sp1500_panel', 
    'ceo_comp', 'a1', 'netflix_content', 
    'olympic_medals', 'world_cup_goals', 
    'midterm']
