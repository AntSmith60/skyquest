from continuum import *
'''
THROUGHLINE:
The Parchment is where we actually (finally!) get to see stuff. It is powered by (and totally encapsulates our use of) matplotlib.
It contains those visible elements that are not a part of the SkyQuest query per se - i.e. the chart title and axis.
It allows for fresh parchments to be laid down, and old parchments to be recalled as we create new queries, or switch between displaying charts and animating charts.
 
The parchment is supported by further affordances that handle our ability to restore old parhcments, and also for the actual mark-making.
'''

'''
AFFORDANCE:
Simply stores or recalls all elements of a chart - lets us restore the parchment if we wipe it in order to present the animated version; manages both content and format.
'''
class ChartedElements:
    def __init__(self):
        self.title = ''
        self.plot = []
        self.bg = []
        self.size = np.array([16,9])
        self.dpi = 200

    '''
    MECHANISM:
    Saves the format (geometry) of the parchment, in case we need to change it for video output
    '''
    def save_geometry(self, canvas):
        self.size = canvas.figure.get_size_inches()
        self.dpi = canvas.figure.get_dpi()

    '''
    MECHANISM:
    Restores the format (geometry) of the parchment
    '''
    def restore_geometry(self, canvas):
        canvas.figure.set_size_inches(*self.size)
        canvas.figure.set_dpi(self.dpi)
        canvas.updateGeometry()

    '''
    MECHANISM:
    Saves the chart content in case we need to clear the parchment for the animation
    This includes:
    - the line collections of the transit arcs, which get removed so they can be added piece-by-piece in the animation
    - the visible extent of the background daybands, which don't get removed but do get resized by the animation
    - x-axis ticks, which might be blanked at the end of an animation
    - the chart title. To be honest this ought to be right when an animation ends, but it will have been twiddled with so might as well save the original along with the foregoing
    '''
    def save_original_ax(self, ax):
        self.plot = []
        self.bg = []
        self.xticks = []

        for coll in ax.collections:
            self.plot.append(coll)
        for patch in ax.patches:
            xy = patch.get_xy()
            w = patch.get_width()
            h = patch.get_height()
            self.bg.append((xy, w, h))

        self.title = ax.title.get_text()
        self.xticks = [tick.get_text() for tick in ax.get_xticklabels()]

    '''
    MECHANISM:
    Simply reverses the original save
    '''
    def restore_original_ax(self, ax):
        for coll in self.plot:
            ax.add_collection(coll)
        for orig, patch in zip(self.bg, ax.patches):
            xy, w, h = orig
            patch.set_xy(xy)
            patch.set_width(w)
            patch.set_height(h)

        ax.title.set_text(self.title)
        ax.set_xticklabels(self.xticks)

'''
AFFORDANCE:
By 'inner' we mean the actual plot area of the chart, so that's the data we plot, the background elements, any guide lines and the grid. 
Lets us add/change/remove and show/hide such elements.
'''
class InnerChartElements():
    def __init__(self, ax):
        self.ax = ax

    '''
    MECHANISM:
    Inscribe a horizontal guide on the parchment, or modify its position if it has already been inscribed.
    '''
    def hguide(self, yvalue, inscription=None):
        if inscription is not None:
            inscription.set_ydata([yvalue])
        else:
            inscription = self.ax.axhline(
                y=yvalue,
                linestyle="--",
                color="gray",
                label=""
            )
        return inscription


    '''
    SKILL:
    Turns all marks of an inscription on or off
    '''
    @staticmethod
    def inscription_visibility(visible, inscriptions):
        for inscription in inscriptions:
            inscription.set_visible(visible)

    '''
    MECHANISM:
    Establish the look of the grid (when it is visible) or else sets the grid invisaible
    '''
    def set_grid(self, state, colour, alpha):
        # self.ax.set_axisbelow(False) # this would put the grid on top
        if state:
            self.ax.grid(True, color=colour, alpha=alpha)
        else:
            # NB if we pass color/alpha grid is forced on!
            self.ax.grid(False)

    '''
    MECHANISM:
    Adds the lines of a transit arc as a line collection.
    For the main plot this will be many segments of a full-day arc.
    During animation, this will be the first hour's segments only
    '''
    def add_lines(self, segments, colour_defs, linewidths, zorder):
        colours = []
        for colour_def in colour_defs:
            colours.append(self._resolve_rgba(colour_def))
        inscription = LineCollection(segments, colors=colours, linewidths=linewidths, zorder=zorder)
        self.ax.add_collection(inscription)
        return inscription, colours

    '''
    MECHANISM:
    Specifically for the animation, extends an arc's previous line collection with a new hour's segment
    '''
    @staticmethod
    def extend_line(collection, extension, colour, linewidth):
        latest_segments = collection.get_segments()
        latest_colors = collection.get_colors()
        latest_widths = collection.get_linewidths()

        # Extend the last segment with new coordinate
        last_segment = latest_segments[-1]
        extended = np.vstack([last_segment, extension[1]])
        latest_segments[-1] = extended

        # Update colour and width for the extended segment
        latest_colors[-1] = colour
        latest_widths[-1] = linewidth

        # Re-apply updated data
        collection.set_segments(latest_segments)
        collection.set_color(latest_colors)
        collection.set_linewidths(latest_widths)

    '''
    MECHANISM:
    Shrinks a line collection from its earliest point, until it is sooo short it is no longer a collection of lines (whereupon it is removed completely)!
    '''
    @staticmethod
    def decay_line(collection):
        segments = collection.get_segments()

        # Shrink the lone path gradually
        if len(segments[0]) > 2:
            segments[0] = segments[0][1:]  # Remove earliest point
            collection.set_segments(segments)
        else:
            # Once only two points remain, remove the whole collection
            collection.remove()
            return True

        return False

    '''
    MECHANISM:
    Adds a block (rectangle) to the parchment
    '''
    def add_block(self, extent, colour_def, linewidth, zorder):
        colour = self._resolve_rgba(colour_def)
        inscription = Rectangle(
            extent[0],
            extent[1][0],
            extent[1][1],
            color = colour,
            linewidth=0, 
            zorder=zorder
        )
        inscription = self.ax.add_patch(inscription)
        return inscription, colour


    '''
    SKILL:
    Updates the position and extent of a block on the parchment
    '''
    @staticmethod
    def set_block(inscription, extent):
        inscription.set_width(extent[1][0])
        inscription.set_xy(extent[0])

    '''
    MECHANISM:
    Shuffles blocks: i.e. shifts the end point of one block and the start point of its (right-hand) neighbour; juggling the widths as needed. This lets us see the bands grown and shrink as the days pass by.
    '''
    def shuffle_blocks(self, blocks, block, new_extent):
        shift = blocks[block].get_width() - new_extent[1][0]
        self.set_block(blocks[block], new_extent)

        if block >= len(blocks) - 1:
            return

        next_xy = blocks[block + 1].get_xy()
        next_start = next_xy[0] - shift
        blocks[block + 1].set_xy((next_start, next_xy[1]))

        next_width = blocks[block + 1].get_width() + shift
        blocks[block + 1].set_width(next_width) 

    '''
    MECHANISM:
    Shrinks background blocks from the left, specifically during the wind-down of an animation
    '''
    @staticmethod
    def decay_blocks(blocks, clip_at):
        for i in range(len(blocks)):
            xy = blocks[i].get_xy()
            width = blocks[i].get_width()
            if int(xy[0]) == clip_at:
                step = xy[0] - int(xy[0])
                blocks[i].set_width(width - step)
                blocks[i].set_xy([clip_at + 1, xy[1]])

    @staticmethod
    def _resolve_rgba(colour_def):
        if isinstance(colour_def, (list, tuple)):
            if len(colour_def) == 4:
                return tuple(colour_def)  # Already RGBA
            elif len(colour_def) == 2:
                return to_rgba(colour_def[0], alpha=colour_def[1])
        else:
            return to_rgba(colour_def)  # Single colour string or RGB tuple

'''
AFFORDANCE:
The parchment sets the overall look and feel of a chart, it orchestrates the ChartedElements and provides for video records. It is the visualisation of the chart.
'''
class Parchment(InnerChartElements):
    '''
    Matplot makes it awkward to base class axis handling as it uses orthognal method names
    (.set_xlim, .set_ylim rather than .x.set_lim .y.set_lim)
    I could introspect with getatttr, but that's worse than not base-classing!
    So here's a pair of axial twin classes for ya
    '''
    '''
    AFFORDANCE:
    Presents the y-axis and handles changes to its range
    '''
    class YAxis():
        def __init__(self, canvas, ax, ymin, ymax, label, font_family, text_colour):
            super().__init__()
            self.canvas = canvas
            self.ax = ax

            self.ymin = ymin
            self.ymax = ymax
            self.ax.set_ylim(self.ymin, self.ymax)

            font = FontProperties(family=font_family, size=24)
            self.ax.set_ylabel(label, fontproperties=font, color=text_colour)

            font = FontProperties(family=font_family, size=16)
            for label in self.ax.get_yticklabels():
                label.set_fontproperties(font)

        def update_yrange(self, ymin, ymax):
            self.ymin, self.ymax = ymin, ymax
            self.ax.set_ylim(self.ymin, self.ymax)

            self.canvas.draw_idle()


    '''
    AFFORDANCE:
    Presents the x-axis and handles changes to its tick labels
    '''
    class XAxis:
        def __init__(self, canvas, ax, label, font_family, text_colour):
            super().__init__()
            self.canvas = canvas
            self.ax = ax

            self.xmin = 0.0
            self.xmax = 24.0
            self.ax.set_xlim(self.xmin, self.xmax)

            font = FontProperties(family=font_family, size=24)
            self.ax.set_xlabel(label, fontproperties=font, color=text_colour)

            self.xticks = np.arange(int(self.xmin), int(self.xmax) + 1, 1)
            self.ax.set_xticks(self.xticks)
            self.labels = [f'{((h+12)%24):02}:00' for h in self.xticks]
            self.ax.set_xticklabels(self.labels)

            font = FontProperties(family=font_family, size=16)
            for label in self.ax.get_xticklabels():
                label.set_fontproperties(font)

        def ticklabels(self, labels):
            self.labels = labels
            self.ax.set_xticklabels(self.labels)

        def ticklabel(self, label, index):
            if self.labels[index] == label:
                return
            self.labels[index] = label
            self.ticklabels(self.labels)

        def blankticks(self):
            self.labels = ['--:00' for _ in self.xticks]
            self.ax.set_xticklabels(self.labels)

    def __init__(self):
        font_family = "Arial"
        face_colour = "black"
        text_colour = "white"

        self.dpi = 120
        self.canvas = FigureCanvas(Figure(figsize=(16, 9), dpi=self.dpi))
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.figure.clear()
        self.ax = self.canvas.figure.add_subplot(111)
        self.canvas.figure.subplots_adjust(left=0.07, right=0.97, top=0.94, bottom=0.08)

        self.ax.set_facecolor(face_colour)
        self.text_colour = text_colour

        self.ax.tick_params(colors=self.text_colour)
        self.ax.spines["bottom"].set_color(self.text_colour)
        self.ax.spines["top"].set_color(self.text_colour)
        self.ax.spines["left"].set_color(self.text_colour)
        self.ax.spines["right"].set_color(self.text_colour)

        font = FontProperties(family=font_family, size=26)
        self.ax.set_title(f"Transit Arc Plot", fontproperties=font, color=self.text_colour)

        super().__init__(self.ax)

        self.w_inches = 16
        self.h_inches = 9

        self.original_chart = ChartedElements()

        self.canvas.figure.patch.set_facecolor(face_colour)

        self.xaxis = self.XAxis(self.canvas, self.ax, "Hour (Local Time)", font_family, text_colour)
        self.yaxis = self.YAxis(self.canvas, self.ax, -30.0, 90.0, "Altitude (°)", font_family, text_colour)

    '''
    SKILL:
    Renders a new title for the chart
    '''
    def retitle(self, title):
        self.ax.title.set_text(title)

    '''
    MECHANISM:
    Saves the format and content of the current parchment, before clearing it for fresh duty.
    Changes the parchment format if we are writing a video file (to HD geometry)
    '''
    def fresh_parchment(self, outfile=None, fps=None):
        self.original_chart.save_geometry(self.canvas)

        writer = None
        if fps is not None:
            self.canvas.resize(int(self.w_inches * self.dpi), int(self.h_inches * self.dpi))
            writer = animation.FFMpegWriter(fps=fps)
            writer.setup(self.canvas.figure, outfile, dpi=self.dpi)

        self.canvas.draw()

        # Remove existing, storing current chart elements
        self.clear_plots(save_original=True)

        self.retitle("Waiting...")
        self.xaxis.blankticks()

        return writer

    '''
    MECHANISM:
    Clears any existing chart content that a new query will influence.
    I.e. remove line collectioons and super-slim background blocks (to a width of 0)
    '''
    def clear_plots(self, save_original=True):
        if save_original:
            self.original_chart.save_original_ax(self.ax)

        # remove elements that get refreshed by a new query
        for coll in reversed(self.ax.collections):
            coll.remove()

        for patch in self.ax.patches:
            patch.set_width(0)
            patch.set_xy([0, -90.0])

    '''
    MECHANISM:
    Signs-off the current parchment (closing the video file if we had it open) before clearing and restoring whatever went before.
    '''
    def restore_parchment(self, writer=None, end_frames=0):
        if writer is not None:
            for _ in range(end_frames):
                writer.grab_frame()
            writer.finish()

        self.clear_plots(save_original=False)

        self.original_chart.restore_geometry(self.canvas)
        self.original_chart.restore_original_ax(self.ax)

    '''
    SKILL:
    Ensures everything actually gets rendered.
    '''
    def redraw(self, idle=False):
        if idle:
            self.canvas.draw_idle()
        else:
            self.canvas.draw()
        QApplication.processEvents()
