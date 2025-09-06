from continuum import *
from inscriptions import Inscriptions

'''
THROUGHLINE:
The ArtBoard is essentially a collection of inscription tools along with a scroll (of PARCHMENT).
'''

'''
AFFORDANCE:
The Inscription tools have an associated 'layer' which provides the UI elements of the tool. 
A basic layer provides a simple toggle that connects to the inscriptions's visibility control
'''
class Layer(QWidget):
    def __init__(self, visible, label, inscriber):
        self.label = label
        self.inscriber = inscriber
        super().__init__()
        self.layout = QHBoxLayout()
        self.toggle = QCheckBox(self.label)
        self.toggle.setChecked(visible)
        self.toggle.stateChanged.connect(lambda: self.inscriber.toggle_visibility())
        self.layout.addWidget(self.toggle)


'''
AFFORDANCE:
The ArtBoard controls presentation layers - whether or not we want to see groups of things, and what we want them to look like.
So, for example, we can turn the display of the lunar arc on or off; or we can set the range of altitudes we want to see.

One day we will extend this to allow selection of ink colours for the plotted arcs.

The ArtBoard also lets us kick-off the animated reveal of the chart, providing us with the tools to control that.

The ArtBoard comprises sets of layers that can be toggled on or off, with each layer being provisioned the inscription tools needed to draw the layer.
'''
class ArtBoard(QWidget):
    '''
    MECHANISM:
    Allows us to direct how the animation of a plot procedes - i.e. should each day accumulate in the plot, or should older days be erased as the animation procedes.
    '''
    class AnimationModeDialog(QDialog):
        def __init__(self, max_days, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Animation Options")
            layout = QVBoxLayout()

            # self.checkbox = QCheckBox("Use tracer style")
            # self.checkbox.setChecked(False)
            # layout.addWidget(self.checkbox)

            self.label = QLabel(f"Max arc days to display (1 to {max_days}):")
            layout.addWidget(self.label)

            self.input_field = QSpinBox(self)
            self.input_field.setRange(1, max_days)
            self.input_field.setValue(max_days)
            layout.addWidget(self.input_field)

            self.ok_button = QPushButton("OK")
            self.ok_button.clicked.connect(self.accept)
            layout.addWidget(self.ok_button)
            self.setLayout(layout)

        def get_values(self):
            # return self.input_field.value(), self.checkbox.isChecked()
            return self.input_field.value()

    '''
    AFFORDANCE:
    Extends a basic layer by also providing for a pair of values which are directly connected to the parchment's Y-axis
    '''
    class AltitudeRange(QWidget):
        def __init__(self, scroll_axis):
            super().__init__()
            self.scroll_axis = scroll_axis

            self.layout = QHBoxLayout()
            self.altmin_input = QDoubleSpinBox()
            self.altmin_input.setRange(-90.0, 90.0)
            self.altmin_input.setSingleStep(5.0)
            self.altmin_input.setValue(self.scroll_axis.ymin)
            # self.altmin_input.setPrefix("Min: ")
            self.altmin_input.valueChanged.connect(lambda: self.update_yrange())

            self.altmax_input = QDoubleSpinBox()
            self.altmax_input.setRange(-90.0, 90.0)
            self.altmax_input.setSingleStep(5.0)
            self.altmax_input.setValue(self.scroll_axis.ymax)
            # self.altmax_input.setPrefix("Max: ")
            self.altmax_input.valueChanged.connect(lambda: self.update_yrange())

            self.layout.addWidget(QLabel("Altitude Range:"))
            self.layout.addWidget(self.altmin_input)
            self.layout.addWidget(self.altmax_input)

        def update_yrange(self):
            altmin = self.altmin_input.value()
            altmax = self.altmax_input.value()
            if altmin >= altmax:
                new_altmin = altmax - 1.0

                # Temporarily block signals to prevent recursive triggering
                self.altmin_input.blockSignals(True)
                self.altmin_input.setValue(new_altmin)
                self.altmin_input.blockSignals(False)

                altmin = new_altmin

            self.scroll_axis.update_yrange(altmin, altmax)

    '''
    MECHANISM:
    Extends the basic inscription tool so that (complex) arcs can be inscribed.
    This tool adds one inscription for each arc to be displayed; we may have several arcs each day (e.g. all the planets) or we may end up with an arc for each of several days.
    We create one such tool for each set of arcs we provide - i.e. 2 such tools: the lunar arcs and, the transit arcs.
    '''
    class InscribeArc(Inscriptions.Inscribe):
        def __init__(self, scroll, title_render, group):
            super().__init__(scroll, title_render)
            self.layer = Layer(True, group, self)

        def add_inscription(self, segments, colour_defs, arc, day, zorder=2):
            inscription = self.make_arc_inscription(segments, colour_defs, arc, day, zorder)
            super().add_inscription(inscription)

    '''
    MECHANISM:
    Extends the basic inscription tool so that backgrounds can be inscribed.
    This is slightly different to inscribing arcs because we have one background - we don't accumulate the background day by day; rather we shift what is already there. Thus, you will note that the actual inscriptions are generated statically and then **modified** - rather than adding new inscriptions as we progress
    '''
    class InscribeBackground(Inscriptions.Inscribe):
        def __init__(self, scroll, title_render, bands=9):
            super().__init__(scroll, title_render)
            self.layer = Layer(True, "Day Bands", self)

            self.original_veil = []

            self.band_decor = [
                ("#bf7b00", 1.00), # day
                ("#5b6b91", 1.00), # civil twilight
                ("#38339e", 1.00), # nautical twilight
                ("#29007a", 1.00), # astronomical twilight
                ("#000047", 1.00), # night
                ("#29007a", 1.00), # astronomical dawn
                ("#38339e", 1.00), # nautical_dawn
                ("#5b6b91", 1.00), # civil dawn
                ("#bf7b00", 1.00)  # day
            ]

            extent = [[0,-90.0],[0,180.0]]
            for band in range(bands):
                self.add_inscription(scroll.add_block(extent, self.band_decor[band], 0, 1)[0])

        def update_inscription(self, extent, day, band=0):
            self.make_bg_inscription(extent, day, band)
            self.scroll.set_block(self.veil[band], extent)

    '''
    MECHANISM:
    Extends the basic inscription tool so that a value can be accepted that inscribes a horizontal guide on the parchment. 
    We only allow for one guide, so the inscription is created statically when we forge the tool and is updated (via the UI) when desired. It is not an animated inscription.
    '''
    class InscribeThreshold(Inscriptions.Inscribe):
        def __init__(self, scroll):
            super().__init__(scroll, None)
            self.value = 30.0
            self.layer = self.ThresholdLayer(True, "Threshold", self, self.value)
            inscription = self.scroll.hguide(self.value)
            self.add_inscription(inscription)

        '''
        AFFORDANCE:
        Extends a basic layer by also providing UI for a threshold value
        '''
        class ThresholdLayer(Layer):
            def __init__(self, visible, label, inscriber, value):
                super().__init__(visible, label, inscriber)
                self.value_ip = QDoubleSpinBox()
                self.value_ip.setRange(-90.0, 90.0)
                self.value_ip.setSingleStep(1.0)
                self.value_ip.setValue(value)
                self.value_ip.valueChanged.connect(inscriber.update_value)
                self.layout.addWidget(self.value_ip)

        def update_value(self, value):
            self.value = value
            if self.veil:
                self.scroll.hguide(self.value, self.veil[0])
            else:
                self.veil.append(self.scroll.hguide(self.value))
            self.scroll.redraw()


    '''
    MECHANISM:
    Extends the basic inscription tool so that we can control the parchment's grid display. Again, we never add further inscriptions to this tool (there is only 1 grid), and the grid itself is not animated.
    '''
    class InscribeGrid(Inscriptions.Inscribe):
        def __init__(self, scroll, grid_colour):
            super().__init__(scroll, None)
            self.layer = Layer(True, "Grid", self)
            self.grid_colour = grid_colour
            self.scroll.set_grid(self.visible, self.grid_colour, alpha=0.2)

        def show_hide(self, show=True):
            self.scroll.set_grid(show and self.visible, self.grid_colour, alpha=0.2)

        def draw_veil(self):
            # we can add additional items to turn on/off with 
            # the grid if we want...
            super().draw_veil()
            self.scroll.set_grid(self.visible, self.grid_colour, alpha=0.2)

    '''
    MECHANISM:
    Creates an ArtBoard with all of its complex tooling.
    '''
    def __init__(self, scroll, arc_groups):
        super().__init__()
        # PROSE: a provided scroll is pinned to the artboard
        self.scroll = scroll

        # It's part of the ArtBoard's duty to keep track of which day we're dealing with when we are plotting over multiple days. 
        self.date = None
        self.day = 0
        self.days = 0

        # UI components are added for the plot itself (the scroll PARCHMENT)
        self.plot_layout = QVBoxLayout()
        self.plot_layout.addWidget(self.scroll.canvas)
        self.setLayout(self.plot_layout)

        # and for the animation utility
        self.animate = QPushButton("Animate")
        self.animate.clicked.connect(self.do_animation)

        self.layout = QHBoxLayout()

        altitude_range = self.AltitudeRange(self.scroll.yaxis)
        self.layout.addLayout(altitude_range.layout)

        # Specialised inscription tooling is added for the threshold indicator, the background, and the grid
        self.threshold = self.InscribeThreshold(self.scroll)
        self.background = self.InscribeBackground(self.scroll, self.render_title)
        self.grid = self.InscribeGrid(self.scroll, self.scroll.text_colour)

        self.layout.addLayout(self.threshold.layer.layout)
        self.layout.addLayout(self.background.layer.layout)

        # then the inscription tooling and UI controls for each of the transit arcs are added. To keep the UI light the inscriptions are grouped into sets, with a UI control for each set: Background, Lunar arc, all (other) transit arcs
        self.inscription_sets = [self.background]
        self.arc_sets = {}
        for group_key, group_name in arc_groups.items():
            self.arc_sets[group_key] = self.InscribeArc(self.scroll, self.render_title, group_name)
            self.inscription_sets.append(self.arc_sets[group_key])
            self.layout.addLayout(self.arc_sets[group_key].layer.layout)
            QShortcut(QKeySequence(group_key[0].upper()), self).activated.connect(lambda: self.arc_sets[group_key].toggle_visibility())

        self.layout.addLayout(self.grid.layer.layout)
        self.layout.addWidget(self.animate)
        self.grid.draw_veil()

        '''
        I wanted to add these in the base inscriber class but that didnt work,
        so I bolted them in here. Sub-optimal for sure but life is just too short!!!
        '''
        QShortcut(QKeySequence('T'), self).activated.connect(lambda: self.threshold.toggle_visibility())
        QShortcut(QKeySequence('B'), self).activated.connect(lambda: self.background.toggle_visibility())
        QShortcut(QKeySequence('G'), self).activated.connect(lambda: self.grid.toggle_visibility())

        self.inscriptions = Inscriptions(self.scroll)
        self.animation_filter = None

    '''
    MECHANISM:
    Cleans-up the ArtBoard when we are ready to start plotting a new presentation
    '''
    def wipe(self, arc_name, date, days):
        self.arc_sets['main'].layer.label = arc_name
        self.date = date
        self.days = days
        self.animation_filter = AnimationFilter(self.scroll, self.inscription_sets)

        for inscription_set in self.inscription_sets:
            inscription_set.steps_by_day.clear()

    '''
    MECHANISM:
    Renders a title for the plot taking account of what is actually plotted (visible). 
    Note that a reference to this method is provided to the inscriptions that effect the title - so the title is re-rendered when such inscriptions are turned on or off.
    '''
    def render_title(self):
        parts = []

        '''
        We always have a layer for a set of arcs
        so the layer and arc_set keys are interchangeable
        But really, we should combine the layer and arc set concepts
        into a single data structure...!!!
        '''
        for key in self.arc_sets.keys():
            if self.arc_sets[key].visible:
                parts.append(f"{self.arc_sets[key].layer.label}")
        if self.background.visible:
            parts.append("Day Bands")

        if parts:
            if len(parts) == 1:
                current_title = parts[0]
            elif len(parts) == 2:
                current_title = " and ".join(parts)
            else:
                current_title = ", ".join(parts[:-1]) + " and " + parts[-1]
            current_title += ' '
        else:
            current_title = ''

        date_str = ''
        if self.date is not None:
            start_str = self.date.strftime("%d/%m/%Y")
            end_str = (self.date + timedelta(days=self.day)).strftime("%d/%m/%Y")
            if start_str == end_str:
                date_str = start_str
            else:
                date_str = f'[{start_str}:{end_str}]'

        current_title += date_str
        self.scroll.retitle(current_title)

        return current_title

    '''
    BEHAVIOUR:
    Initiates an animation, allowing a video render to be produced also.
    '''
    def do_animation(self):
        # !!! we oughta disable all dashboard controls
        self.animate.setEnabled(False)

        outfile = None
        outfile, _ = QFileDialog.getSaveFileName(
            self, "Save Animation As", "", "Video Files (*.mp4);;All Files (*)"
        )
        max_days = len(self.inscriptions.all_animation_steps) # which is number of days
        day_cap = max_days

        dialog = self.AnimationModeDialog(day_cap, self)
        if dialog.exec_() == QDialog.Accepted:
            day_cap = dialog.get_values()
        else:
            self.animate.setEnabled(True)
            return

        self.animation_filter._pre_animate(self.background)

        day_tracker = Inscriptions.DayTracker(day_cap, max_days)

        frame_out = FrameOut(self.scroll, outfile)

        self.inscriptions.animate(frame_out, day_tracker, self.background.veil, self.animation_filter)

        frame_out.close()
        self.animation_filter._post_animate()

        self.animate.setEnabled(True)

'''
AFFORDANCE:
Records the state of the chart display before we start messing with it in order to present the animation; resetting the initial state when the animation completes.
Having remembered the original state of the chart display it can also answer the question 'is this part of the animation'? whilst the animation is running; So only those thongs visible when we asked for the animation are included in the animation.
'''
class AnimationFilter:
    def __init__(self, scroll, layers):
        self.scroll = scroll
        self.layers = layers
        self.pre_animate_states = {}
        self.bg_layer = None

    def _pre_animate(self, bg_layer):
        self.bg_layer = bg_layer
        self.pre_animate_states = {}
        for i, layer in enumerate(self.layers):
            self.pre_animate_states[layer] = layer.visible
            if layer.visible and layer != self.bg_layer:
                layer.set_visibility(False)

    def _post_animate(self):
        for i, layer in enumerate(self.layers):
            if self.pre_animate_states[layer]:
                layer.set_visibility(True)
        self.scroll.redraw(idle=True)

    def is_animated(self, layer):
        if layer in self.pre_animate_states.keys():
            return self.pre_animate_states[layer]
        return True


#NB we still make direct matplotlib calls  on the writer object, probs wanna change that!!!
class FrameOut:
    def __init__(self, scroll, outfile):
        self.scroll = scroll
        self.fps = 50
        self.framerate = 1 / self.fps
        self.writer = None

        if outfile:
            self.writer = self.scroll.fresh_parchment(outfile, self.fps)
            self.scroll.redraw()
            for _ in range(self.fps):
                self.writer.grab_frame()
        else:
            self.scroll.fresh_parchment()

        self.now = time.perf_counter()

    def capture(self):
        self.scroll.redraw()
        if self.writer:
            self.writer.grab_frame()
        else:
            next_frametime = self.now + self.framerate
            sleep_time = max(0, next_frametime - self.now)
            self.now = next_frametime
            time.sleep(sleep_time)

    def close(self):
        self.scroll.restore_parchment(self.writer, self.fps)

