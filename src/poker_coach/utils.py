import pandas as pd
import seaborn as sns
from highlight_text import ax_text
from poker_coach.config import DATA_COLUMNS

#Helper function to analyze data with colors to visually compare the data. 
def rainbow(data, n=None, mode=None):
    if n is not None and mode=='sample':
        d = data.sample(n)
    elif n is not None and mode=='head':
        d = data.head(n)
    else:
        d = data
    cols = d.columns
    palette = sns.color_palette('pastel', len(cols)).as_hex()

    #formatting by ading commas and decimal places to the columns about money
    money_cols = [c for c in DATA_COLUMNS if c in d.columns]
    styles = d.style.format('{:,.2f}', subset=money_cols)

    #coloring each rows text
    for col, color in zip(cols, palette):
        styles = styles.set_properties(subset=[col],**{'background-color': 'black', 'color': color})
    return styles
