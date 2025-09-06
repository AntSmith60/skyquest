from continuum import *
'''
THROUGHLINE:
Inscriptions are chart elements that:
- contain a 'veil', a collection of marks on the parchment
- provide (UI) tooling to draw or hide the veil (or otherwise effect its apppearance)
- maintains the animation sequence for the veil's marks
- provides the means to execute the animation sequence
'''

'''
AFFORDANCE:
Inscriptions add 'stuff' to the presentation which can then be shown on the parchment. either as a complete charted element, or as an animated sequencce.

They work with the PARCHMENT to make this stuff visible, but the main concern of an inscription is to granularise the inscribed 'thing' so that it can be revealed step-by-step when an animation is requested.

The main affordance describes what an inscription IS and provides the main animation logic
'''
class Inscriptions():
    '''
    AFFORDANCE:
    Inscriptions are sets of marks that can be made on a parchment.
    The full set lives in the 'veil' which may or may not be drawn at any given point (determined by the inscription's visible state)
    That's all there is to it for simple inscriptions like the grid or the guides.
    
    More complex (or compound) inscriptions like transit arcs and the background are also created as animateable groups - i.e. per-hour per-day segments. Unlike the veil (which is completely on or off) these can be revealed step-by-step (when we animate). 
    
    Effectively the inscriptions provides 2 views on the same displayable 'thing': the entire thing (line or background) turned on or off as a whole, and; a segmented version turned on or off on an hour-by-hour basis.
    '''
    class Inscribe():
        def __init__(self, scroll, title_render):
            self.scroll = scroll
            self.visible = True
            self.title_render = title_render

            self.veil = []
            self.steps_by_day = defaultdict(lambda: defaultdict(list))

        '''
        MECHANISM:
        Adds a set of marks to the inscription's veil (the overall view of the chart)
        '''
        def add_inscription(self, inscription):
            self.veil.append(inscription)


        '''
        MECHANISM:
        Updates previous inscriptions, but only in a simple well-defined way; i.e. when we know exactly what we are dealing with. So we may change the value of an existing guideline, or the extent of a known background band.
        '''
        def update_inscription(self, inscription):
            raise NotImplementedError("Basic inscription tools don't know how to update an inscription (only adds them)")

        '''
        MECHANISM:
        Adds segemented lines to the animation view, returning an inscription set that can then also be added to the veil - i.e. presumes the data is already suitably segmented (by the hour), which it will be when it comes to transit arcs that are derived on an hourly basis.
        '''

        def make_arc_inscription(self, segments, colour_defs, arc, day, zorder):
            linewidths = 4
            inscription, colours = self.scroll.add_lines(segments, colour_defs, linewidths, zorder)

            colour = colours[-1]
            for i, segment in enumerate(segments):
                if i < len(colours):
                    colour = colours[i]

                chart_band = int(segment[0][0])
                step = {
                    "parent": self,
                    "arc": arc,
                    "day": day,
                    "segment": segment,
                    "color": colour,
                    "linewidth": linewidths,
                    "type": "line",
                    "chart_band": chart_band,
                    "zorder": zorder
                }
                self.steps_by_day[day][chart_band].append(step)

            return inscription

        '''
        MECHANISM:
        Creates the animation steps for the background. These either grow the day bands from nothing to full width (day zero) or else shuffles the boundary between the day bands (on subsequent days).
        Note that the inscriptions themselves are already added, here we create the animation steps that adjust them.
        '''
        def make_bg_inscription(self, extent, day, band):
            zorder = 1

            if day == 0:
                start = extent[0][0]
                total_width = extent[1][0]

                this_width = min (total_width, 1 - (start - int(start)))
                start_band = int(start)
                end_band = int(start + total_width)
                for chart_band in range(start_band, end_band + 1):
                    animated_extent = [[start, extent[0][1]], [this_width, extent[1][1]]]

                    step = {
                        "parent": self,
                        "arc": 0,
                        "day": day,
                        "type": "dayband",
                        "band": band,
                        "extent": animated_extent,
                        "chart_band": chart_band,
                        "zorder": zorder
                    }

                    self.steps_by_day[day][chart_band].append(step)
                    this_width = min(this_width + 1.0, total_width)

            else:
                chart_band = int(extent[0][0] + extent[1][0])
                step = {
                    "parent": self,
                    "arc": 0,
                    "day": day,
                    "type": "bandshift",
                    "band": band,
                    "extent": extent,
                    "chart_band": chart_band,
                    "zorder": zorder
                }
                self.steps_by_day[day][chart_band].append(step)
                
        '''
        MECHANISM:
        Shows or hides the inscription's veil, updating the overall plot title if needed
        '''
        def set_visibility(self, visible, redraw=True):
            self.visible = visible
            if self.title_render:
                self.title_render()
            self.draw_veil()
            if redraw:
                self.scroll.redraw()

        '''
        MECHANISM:
        For the UI which operates in terms of toggle rather than absolute state
        '''
        def toggle_visibility(self):
            self.set_visibility(not self.visible)

        '''
        SKILL:
        Directs the parchment to make or erase the marks of this veil (i.e avoids direct low-level calls into matplotlib at this point)
        '''
        def draw_veil(self):
            if not self.veil:
                return
            self.scroll.inscription_visibility(self.visible, self.veil)


    def __init__(self, scroll):
        self.scroll = scroll

        self.all_animation_steps = defaultdict(lambda: defaultdict(list))

    '''
    AFFORDANCE:
    Keeps track of the days during an animation, providing the key mechanisms for a controlled unwind at the end of the animated day range (if needed)
    '''
    class DayTracker:
        def __init__(self, day_cap, days):
            self.day_cap = day_cap
            self.days = days

            self.full_accumulation = self.day_cap == self.days
            self.end_of_days = False
            self.day = 0

        '''
        MECHANISM:
        Keeps track of days both through the day-range of the animation, and through the unwind period atthe end off an animation
        '''
        def step_day(self):
            if self.day == self.days - 1 and not self.full_accumulation:
                self.end_of_days = True
                self.day_cap -= 1
            else:
                self.day += 1

        '''
        DISPOSITION:
        A simple yes or no to the question 'are there more days to present': whether those days are the main animation, or days in the unwind period.
        '''
        @property
        def more_days(self):
            return self.day < self.days and self.day_cap >= 0

        '''
        DISPOSITION:
        Indicates if we ought to be erasing earlier arcs from teh plot as the animation procedes.
        '''
        @property
        def too_many_days(self):
            return self.day >= self.day_cap

        '''
        DISPOSITION:
        Indicates if this is the final day of the end of days
        '''
        @property
        def final_day(self):
            return self.end_of_days and self.day_cap == 0

    '''
    AFFORDANCE:
    An intermediary between the animator and the PARCHMENT.
    Collects references to the marks that are made so they can be progressively removed later if required.
    '''
    class ArcLimiter:
        def __init__(self, scroll):
            self.scroll = scroll
            self.current_collections = defaultdict(lambda: {
                "parent": None,
                "arc": 0,
                "collections": []
            })

        '''
        MECHANISM:
        Removes all of the marks made in the (current) oldest hour of the animated chart
        '''
        def expire(self, parent, arc):
            key = (parent, arc)
            group = self.current_collections[key]
            if group["collections"]:
                oldest_collection = group["collections"][0]
                if self.scroll.decay_line(oldest_collection):
                    group["collections"].pop(0)

        '''
        MECHANISM:
        Adds the animated marks to the PARCHMENT, remembering all the marks made in the given hour so they can later be expired.
        '''
        def extend(self, parent, arc, hour, segment, color, linewidth, zorder):
            key = (parent, arc)
            group = self.current_collections[key]
            if hour == 0:
                inscription, _ = self.scroll.add_lines([segment], [color], linewidth, zorder)
                group["collections"].append(inscription)
            else:
                latest_collection = group["collections"][-1]
                self.scroll.extend_line(latest_collection, segment, color, linewidth)

    '''
    BEHAVIOUR:
    Executes the animation of the current (complete) plot.
    '''
    def animate(self, frame_out, day_tracker, bg_veil, animation_filter):
        # PROSE: Remember what was visible before the animation so we can restore that state later. Then turn all the veils of so we have a blank slate for the animation to begin.
        current_arcs = self.ArcLimiter(self.scroll)

        # animate by day...
        while day_tracker.more_days:
            # ... by hour...
            for hour in range(25):
                steps = self.all_animation_steps[day_tracker.day][hour]
                bg_update_needed = False
                # ...by step...
                for step in steps:
                    # only animate that which was visible
                    if not animation_filter.is_animated(step["parent"]):
                        continue

                    # remove any expired line segments / collections
                    if day_tracker.too_many_days and step["type"] == "line":
                        current_arcs.expire(step["parent"], step["arc"])

                    # if we are currently unwinding the animation, just get on with it, no need to look for any steps that might want adding
                    if day_tracker.end_of_days:
                        continue

                    # otherwise perform the animated steps, which includes:
                    # - update title (specifically so the date range is accurate)
                    if step["type"] == "title":
                        self.scroll.retitle(step["title"])

                    # - update x-axis ticks, which change on daylight saving days
                    elif step["type"] == "ticks":
                        self.scroll.xaxis.ticklabel(step["label"], step["index"])

                    # - add the transit arcs for the hour
                    elif step["type"] == "line":
                        current_arcs.extend(step["parent"], step["arc"], hour, step["segment"],  step["color"], step["linewidth"], step["zorder"])

                    # - grow the day bands as the animation procedes. So on day 1 we see the daybands expand from nothing
                    elif step["type"] == "dayband":
                        self.scroll.set_block(bg_veil[step["band"]], step["extent"])

                    # - shuffle the day bands on subsequent days
                    elif step["type"] == "bandshift":
                        self.scroll.shuffle_blocks(bg_veil, step["band"], step["extent"])

                # At the end of each hour now...
                # on the final day of the unwind, erase the background and the x-tick labels (since time is evapourating..!) on an hour-by-hour basis
                if day_tracker.final_day:
                    self.scroll.decay_blocks(bg_veil, hour)
                    self.scroll.xaxis.ticklabel("--:00", hour)

                # display/record the animation of this hour
                frame_out.capture()

            # at the end of day, step to the next day, if there is one
            day_tracker.step_day()

    @staticmethod
    def iter_anim_steps(animation_steps):
        for day in range(len(animation_steps)):
            for hour in sorted(animation_steps[day]):
                for step in animation_steps[day][hour]:
                    yield day, hour, step

