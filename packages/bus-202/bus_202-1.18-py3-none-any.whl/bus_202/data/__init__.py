import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent

class DataFrames:
    _sp1500_cross_sectional = None
    _sp1500_panel = None
    _ceo_comp = None
    _a1 = None
    _netflix_content = None
    _olympic_medals = None
    _world_cup_goals = None
    _midterm = None
    
    @property
    def sp1500_cross_sectional(self):
        if self._sp1500_cross_sectional is None:
            self._sp1500_cross_sectional = pd.read_excel(DATA_DIR / 'sp1500_cross_sectional.xlsx')
        return self._sp1500_cross_sectional
    
    @property
    def sp1500_panel(self):
        if self._sp1500_panel is None:
            self._sp1500_panel = pd.read_excel(DATA_DIR / 'sp1500_panel.xlsx')
        return self._sp1500_panel
    
    @property
    def ceo_comp(self):
        if self._ceo_comp is None:
            self._ceo_comp = pd.read_excel(DATA_DIR / 'ceo_comp.xlsx')
        return self._ceo_comp
    
    @property
    def a1(self):
        if self._a1 is None:
            self._a1 = pd.read_excel(DATA_DIR / 'a1.xlsx')
        return self._a1
    
    @property
    def netflix_content(self):
        if self._netflix_content is None:
            self._netflix_content = pd.read_excel(DATA_DIR / 'netflix_content.xlsx')
        return self._netflix_content
    
    @property
    def olympic_medals(self):
        if self._olympic_medals is None:
            self._olympic_medals = pd.read_excel(DATA_DIR / 'olympic_medals.xlsx')
        return self._olympic_medals
    
    @property
    def world_cup_goals(self):
        if self._world_cup_goals is None:
            self._world_cup_goals = pd.read_excel(DATA_DIR / 'world_cup_goals.xlsx')
        return self._world_cup_goals
    
    @property
    def midterm(self):
        if self._midterm is None:
            self._midterm = pd.read_excel(DATA_DIR / 'midterm.xlsx')
        return self._midterm

# Create a single instance
_data = DataFrames()

# Define module-level functions that return the data
def sp1500_cross_sectional():
    return _data.sp1500_cross_sectional

def sp1500_panel():
    return _data.sp1500_panel

def ceo_comp():
    return _data.ceo_comp

def a1():
    return _data.a1

def netflix_content():
    return _data.netflix_content

def olympic_medals():
    return _data.olympic_medals

def world_cup_goals():
    return _data.world_cup_goals

def midterm():
    return _data.midterm
