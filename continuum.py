# continuum.py
"""
THROUGHLINE:
Defines foundational imports and truths upon which the drama unfolds.

All our modules perform 'import *' from the continuum.
In a larger app we would split this into separate modules, and then use __init__.py to 'import *' from the core section only, with individual user modules then importing all from the extensions.

but it is kept simple for now, albeit less scalable.

NOTE:: This is THE CONTINUUM, it only hosts the external world and NEVER includes imports of app-local modules!

I know, its unusual to promote the use of 'import *' (and you may well hate the idea) but exactly what gets imported is somewhat restricted to exactly what we use and this appproach gives us a single point of truth with regards our reliance on the wider world..!
"""

# === PART 1: CORE ============================================================
# CONTINUUM: we use the standard sys module to get CLI arguments and issue exit codes.
import sys
# CONTINUUM: at the end of an animation we have a lot of matplotlib objects to clean-up, at which point we perform an explicit garbage collection. Not really something we should HAVE to do, but, well - matplotlib...
import gc
# CONTINUUM: The standard time module provides 'sleep', for when we want to pace an interactive animation
import time
# CONTINUUM: The standard math module provides 'ceil', which helps to chunk time into 1 hour bands
import math
# CONTINUUM: The NUMPY module is used a convenience to create small sequences, when needed - there no serious vectorised operations in this app
import numpy as np
# CONTINUUM: we use the convenience of the defaultdict to ensure we can always index every hour of every day in a given day range, since conceptually those indices are always valid (days always have 24 hours!) - even if we don't happen to have any data for a given time.
from collections import (
    defaultdict
)
# CONTINUUM: Dates and times pervade in this application, but you can pretty much always expect them to be standard datetime objects - EXCEPT where Idmon needs to work in Julian dates, but that's a complexity he keeps to himselff...
from datetime import (
    datetime, 
    timedelta
)
# CONTINUUM: when we add contextual time to a (naive) input date we do so as UTC, then convert to local time as needed (e.g. when display time axes); in general we can expect our datetime objects to be UTC
from zoneinfo import (
    ZoneInfo
)

# === PART 2: ASTRO ===========================================================
# CONTINUUM: All of our astronomical knowledge is drawn from skyfield, based on data downloads in './skyfield-data'
from skyfield.api import (
    Loader, 
    Star,
    Topos 
)
from skyfield.almanac import (
    dark_twilight_day, 
    find_discrete, 
    sunrise_sunset
)


# === PART 3: UI ==============================================================
# CONTINUUM: All GUI  is provided by PyQt5
from PyQt5.QtWidgets import (
    # Core app and behaviours
    QApplication, 
    QShortcut, QSizePolicy, 
    QWidget,

    # Layouts
    QFormLayout, 
    QHBoxLayout, 
    QVBoxLayout, 

    # Basic UI elements
    QCheckBox, QComboBox, 
    QDoubleSpinBox, 
    QLabel, QLineEdit, 
    QPushButton, 
    QSpinBox,

    # Dialogs
    QDateEdit, QDialog, QDialogButtonBox, 
    QFileDialog
)

from PyQt5.QtGui import (
    QFont, 
    QKeySequence
)
from PyQt5.QtCore import (
    QDate, 
    Qt 
)


# === PART 4: VISUALISATION ===================================================
# Backends, interactive and video export versions
# CONTINUUM: provides the interactive (on-screen) chart visualisation, in concert with GUI (PyQt5)
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas
)
# CONTINUUM: provides the chart visualisation when recording video frames
from matplotlib.backends.backend_agg import (
    FigureCanvasAgg
)

# core plotting tools
# CONTINUUM: provides the (FFMPEG) video writer
import matplotlib.animation as animation
# CONTINUUM: only required when we come to release canvas memory
import matplotlib.pyplot as plt

# CONTINUUM: lets us add figures to a canvas - we only ever work with 1 figure, but nevertheless matplot lib treats a canvas as containing a set of figures.
from matplotlib.figure import (
    Figure
)
# CONTINUUM: All of our actual plotted arcs are created as line collections, which helps when we want to animate the chart
from matplotlib.collections import (
    LineCollection
)
# CONTINUUM: the background visualisation of daylight/twilight bands is achieved by adding rectangles (behind the transit arcs) as so-called patches.
from matplotlib.patches import (
    Rectangle
)
# CONTINUUM: we use a single font family, but at a variety of sizes
from matplotlib.font_manager import (
    FontProperties
)
# CONTINUUM: we use colours with transparency when plotting the transit arcs, inversely relative to the moon illumination (which makes celestial objects less visible!).
from matplotlib.colors import (
    to_rgba
)

# Matplotlib style setting
import matplotlib.style as mplstyle
mplstyle.use('fast')
