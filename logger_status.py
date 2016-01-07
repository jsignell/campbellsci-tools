"""
Create a rough display of logger status


Julia Signell
2016-01-06
"""

import os
import time
import matplotlib.pyplot as plt
import matplotlib.patches
import mpld3

path = 'C:/Campbellsci/Loggernet/'
loggers = ['CR6', 'CR5000', 'CR1000', 'CL06_CR1000', 'Wash_Strm_CR200', 'Upper WS CR200']
places = zip([0]*len(loggers), range(0, 5*len(loggers),5))

fig, ax = plt.subplots(figsize=(10,6), subplot_kw={'xticks': [], 'yticks': []})
ax.hlines(35, -5, 55, linewidth=2)
ax.vlines(55, -5, 35, linewidth=2)
ax.set_xlim(-5,55)
ax.set_ylim(-5,len(loggers)*5+5)
ax.set_title(time.ctime())
mpld3.plugins.clear(fig)

#loggers
for logger, place in zip(loggers, places):
    fs = os.listdir(path)
    i = 0
    for f in fs:
        if logger in f:
            i = max(i, os.path.getmtime(path+f))
    t = time.time() - i
    hover_text = time.ctime(i)
    if 0 < t< 60*60:
        c = "#9ACD32"
    elif t < 60*60*24:
        c = "#FFFF2F"
    elif t < 60*60*24*7:
        c = "#FF7B24"
    else:
        c = "#CF1F0F"
    rect = matplotlib.patches.Rectangle(place, width=3, height=3, facecolor=c)
    ax.add_patch(rect)
    line = matplotlib.patches.Arrow(place[0]+3, place[1]+2, 15, 12-place[1], width=1, ec='w', fc='k')
    h=ax.add_patch(line)
    
    ax.annotate(logger, xy=(place[0],place[1]+3.5), size=12)
    tooltip = mpld3.plugins.PointLabelTooltip(h, labels=[hover_text])
    mpld3.plugins.connect(fig, tooltip)
    
ax.set_axis_off()

#make the computer
ax.annotate('Lidar Lab computer', xy=(19,20), size=12)
rect = matplotlib.patches.Rectangle((19,9), width=8, height=10, facecolor='#FFFFFF')
ax.add_patch(rect)
line = matplotlib.patches.Arrow(28,14, 10, 0, width=1, ec='w', fc='k')
ax.add_patch(line)
try:
    p = os.popen('df -h', 'r')
    for line in p.readlines():
        if line.startswith('C'):
            a = line.split()
            fill = int(a[5][0:-1])/100.
    rect = matplotlib.patches.Rectangle((19,9), width=8, height=10*fill, fc='#66FFFF', ec='none')
    h = ax.add_patch(rect)
    tooltip = mpld3.plugins.PointLabelTooltip(h, labels=['Used Disk Space = '+a[3]])
    mpld3.plugins.connect(fig, tooltip)
except:
    pass

# make a cloud
cloud_dims = zip([[40,13], [42,13.5], [44,14], [46,13]], [1.5, 2, 2.5, 1.5])
ax.annotate('CEE Cloud', xy=(40,18), size=12)
for place, rad in cloud_dims:
    circ = matplotlib.patches.Circle(place, radius=rad, fc='#3333EE', ec='none')
    ax.add_patch(circ)
ax.figure.canvas.draw()

mpld3.save_html(fig, path+'logger_status.html')
