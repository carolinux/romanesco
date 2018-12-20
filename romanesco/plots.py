import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.ticker import ScalarFormatter 
import numpy as np

from datetime import datetime, timedelta

date_fmt = mdates.DateFormatter('%b %d')
date_hour_fmt = mdates.DateFormatter('%b %d %H:%M')

def heatmap_figure(x, y, w, h, style="plain"):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    if style == "dots":
        ax.scatter(x, y)
    elif style == "heatmap":
        heatmap, xedges, yedges = np.histogram2d(x, y, bins=50)
        extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
        ax.imshow(heatmap, extent=extent)

    ax.add_patch(Rectangle((0,0), w, h, facecolor="none"))
    ax.add_patch(Rectangle((0,h/2), w, 2, facecolor="none")) # center lines
    ax.add_patch(Rectangle((w/2,0), 2, h, facecolor="none")) # center lines
    ax.set_xlim([0,w])
    ax.set_ylim([0,h])
    return fig


def heatmap_figures(heatmap_dict, style="dots"):
    heatmap_data = heatmap_dict["data"]
    pitch_width = heatmap_dict["pitchWidth"]
    pitch_height = heatmap_dict["pitchHeight"]
    halftime = heatmap_dict["secondHalfStartTime"]
    centerx = pitch_width/2
    centery = pitch_height/2
    half1 = [ v for k,v in heatmap_data.iteritems() if k < halftime and v!=[-1,-1]]
    half2 = [ v for k,v in heatmap_data.iteritems() if k >= halftime and v!=[-1,-1]]
    x1 = [ t[0] for t in half1] 
    y1 = [ t[1] for t in half1] 
    x2 = [ t[0] for t in half2] 
    y2 = [ t[1] for t in half2] 
    x3 = [ centerx + (centerx - t[0]) for t in half2] 
    y3 = [ centery + (centery - t[1]) for t in half2] 
    fig1 = heatmap_figure(x1, y1, pitch_width, pitch_height, style=style)
    fig2 = heatmap_figure(x2, y2, pitch_width, pitch_height, style=style)
    fig3 = heatmap_figure(x3, y3, pitch_width, pitch_height, style=style) # this has the heatmap from 2nd half "unflipped"
    return fig1, fig2, fig3

def team_session_history_figure(df, team_session_id, metric="Distance", date_col="Date", agg="median"):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    df = df.groupby(date_col)[metric].agg(agg).reset_index()
    dates = map(lambda x: datetime.strptime(x,"%Y-%m-%d %H:%M:%S"), df[date_col].values)
    if len(dates) >= 1 and (dates[0] - dates[-1]) > timedelta(days=1):
        fmt = date_fmt
    else:
        fmt = date_hour_fmt
    ax.plot(dates, df[metric].values)
    ax.scatter(dates, df[metric].values)
    ax.set_xticks(dates)
    ax.set_yticklabels(ax.get_yticks()) # this fixes weird mpl behavior where it adds unwanted offsets
    ax.set_xlabel('date')
    ax.xaxis.set_major_formatter(fmt)
    ax.set_ylabel(metric)
    ax.set_title("Evolution of {} {}  over time for the team session {}".format(agg, metric, team_session_id))
    for tick in ax.get_xticklabels():
            tick.set_rotation(45)
    ax.grid()
    fig.tight_layout() # so that labels don't get cut off at the bottom
    return fig

