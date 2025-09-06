from continuum import *

from artboard import ArtBoard
from parchment import Parchment

'''
THROUGHLINE:
There's quite a lot to do in terms of dislaying, animating and recording the plots that arise from the queries, so there are a number of layered concepts at play:
- ASTREUS is the master-scribe that orchestrates everything to do with the plot visualisation.
- He is equipped with an ARTBOARD (GUI) that allows visual elements to be turned on or of and provides:
- INSCRIPTION tools for adding elements to the plot; where each tool provides for the animation of the added inscriptions
- and whereby the inscriptions are laid down on a PARCHMENT for the final visualisation
'''

'''
FIGURATION:
Astraeus derives from the Greek word for 'star' and is said to be the father of the winds - so very much a key player in any astronomical quest.
In this quest he creates the charts that answer the queries presented in The Observatory, which calls for the presentation to be started/completed - and for the days of interest to be drawn-in.
'''
class Astraeus():
    def __init__(self):
        # KNOWLEDGE: a look-up table that lets us plot the moon's arc relative to its illumination
        self.greyscale = np.array([f"#{i:02x}{i:02x}{i:02x}" for i in range(256)])

        self.scroll = Parchment()
        
        # KNOWLEDGE: we always allow for the lunar arc, plus 1 or more celsatial bodies
        arc_sets = {}
        arc_sets['lunar'] = 'Lunar Path'
        arc_sets['main'] = 'Transit Arc'
        self.artboard = ArtBoard(self.scroll, arc_sets)
        self.inscriptions = self.artboard.inscriptions

        # KNOWLEDGE: the colours we use to plot celestial arcs. Fixed here but one will be managed by the ArtBoard
        self.target_colours = [
            '#5757e5',  # Neptune
            '#1f991f',  # Uranus
            '#df41e5',  # Saturn
            '#39e5e5',  # Jupiter
            '#ff4040',  # Mars
            '#e5cd45',  # Venus
            '#92cc7c'   # Mercury
        ]

    '''
    MECHANISM:
    Sets-up the ArtBoard with a fresh parchment for the new plot (clearing any animation)
    '''
    def commence_presentation(self, arc_name, date, days):
        self.artboard.wipe(arc_name, date, days)
        self.inscriptions.all_animation_steps = defaultdict(lambda: defaultdict(list))
        self.scroll.fresh_parchment()

    def _collate_animation(self, day, inscriber):
        for hour, steps in inscriber.steps_by_day[day].items():
            self.inscriptions.all_animation_steps[day][hour].extend(steps)

    '''
    BEHAVIOUR:
    Draws the entire plot for a single day: the background day bands, each transit arc, the title and the axes.
    The title includes the (overall) day range and so needs updating for each plotted day, as does the x-axis as the time-of-day hour labels change when we have daylight saving.
    '''
    def draw_day(self, day, local_hours, arc_data, moon_arc, moon_illumination, twilight_data):
        self.draw_day_bands(day, twilight_data, self.artboard.background)

        # note that we expect all arcs to provide 24hrs of hourly data
        for arc_num, (arc, inscriber) in enumerate(
            [(moon_arc, self.artboard.arc_sets['lunar'])] + 
            [(arc_data[i], self.artboard.arc_sets['main']) for i in range(len(arc_data))]
        ):
            arc_display_num = arc_num - 1
            if arc_num > 0 and len(arc_data) == 1:
                arc_display_num = 4
            self.plot_arc_day(
                day=day,
                arc_num=arc_display_num,
                inscriber=inscriber,
                arc_data=arc,
                illumination_data=moon_illumination
            )

        self._collate_animation(day, self.artboard.background)
        for key in self.artboard.arc_sets.keys():
            self._collate_animation(day, self.artboard.arc_sets[key])

        # CONTEXTUAL LABELS
        # -----------------
        '''
        We COULD draw this section once after plotting all of the days
        But for animation purposes we do it for each day...
        '''
        self.artboard.day = day
        current_title = self.artboard.render_title()

        self.inscriptions.all_animation_steps[day][0].append({
            "parent": self,
            "arc": 0,
            "day": day,
            "type": "title",
            "title": current_title,
            "chart_band": 0,
            "zorder": 1
        })

        self.scroll.xaxis.ticklabels(local_hours)
        for hour, label in enumerate(local_hours):
            self.inscriptions.all_animation_steps[day][hour].append({
                "parent": self,
                "arc": 0,
                "day": day,
                "type": "ticks",
                "label": label,
                "index": hour,
                "chart_band": hour,
                "zorder": 1
            })

    '''
    MECHANISM:
    Adds the day/twilight colour-bands to the inscriptions
    '''
    def draw_day_bands(self, day, twilight_data, inscriber):
        # ylim is not dependant on what we plot, its is chosen via the UI
        # so we can use fixed limits for the height of our twilight indication
        bottom, top = -90.0, 90.0
        for j, band in enumerate(twilight_data):
            start, end, event = band
            width = end - start
            height = top - bottom
            extent = [(start,bottom),(width,height)]
            inscriber.update_inscription(extent, day=day, band=j)

    '''
    MECHANISM:
    Adds (all) the transit arcs to the inscriptions for a given day
    '''
    def plot_arc_day(self, day, arc_num, inscriber, arc_data, illumination_data):
        segments, colour_defs = [], []
        hours, altitudes = arc_data
        for h1, h2, alt1, alt2, illum in zip(
            hours[:-1], hours[1:], 
            altitudes[:-1], altitudes[1:], 
            illumination_data[:-1]
        ):
            segments.append([[h1, alt1], [h2, alt2]])

            if arc_num < 0: # ie. lunar arc
                # Use greyscale based on illumination
                grey = self.greyscale[int(illum * 255)]
                colour_defs.append((grey, None))
            else:
                colour_index = arc_num % len(self.target_colours)
                colour = self.target_colours[colour_index]
                # Fade target arc based on moon brightness
                alpha = 0.6 - (illum * 0.4)
                colour_defs.append((colour, alpha))

        inscriber.add_inscription(segments, colour_defs, arc=max(0,arc_num), day=day, zorder=2)

    '''
    MECHANISM:
    Finalises a presentation by adding the threshold inscription and calling on the ArtBoard's draw_veil methods to set what is (or isn't) visible. Thereafter calling on the parchment to do the draw.
    '''
    def complete_presentation(self):
        # set visibilities
        # ----------------
        self.artboard.background.draw_veil()
        for key in self.artboard.arc_sets.keys():
            self.artboard.arc_sets[key].draw_veil()
        self.artboard.threshold.draw_veil()

        # AND show it all
        # ---------------
        self.scroll.redraw()

