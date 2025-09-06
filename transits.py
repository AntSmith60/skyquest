from continuum import *

'''
WORLD:
This is the entry script fot the SkyQuest app.

SkyQuest shows the astronomical info regarding the observability of celestial bodies from a given earth-bound observation point;  you'll need to look elsewhere (perhaps out of the window) for metereological impact.

![SkyQuest, screenshot](skyquest-screenshot.png)

It provdes a 24-hour daily view of how selected bodies transit across the skyline from the chosen vantage point. Multiple daily views can be stacked. The x-axis shows the local time of day, sensitive to daylight saving time. When showing multiple days, the x-axis reflects the last day drawn. The y-axis sets the plotted altitude range.

Daylight bands can also be shown which segment the day (through coloured background blocks) between day and night, along with the various periods of twilight and dawn (civil, nautical and astronmical) - which is again true to the last day plotted.

Celestial bodies can be selected for the plot, with the lunar arc, also, always available. The lunar arc is plotted in grey, at a brightness dictated by the moon-illumination on each plotted hour. The transit arcs of chosen objects are plotted with a degree of transparency dictated by the moon-illumination - i.e indicating how visible such onjects _may_ be (of course that's also a question of altitude and weather)

It is therefore possible to see the optimum time to observe specific objects in the night sky with regards daylight level, moon-illumination and altitude - for one or more days; from anywhere in the world. The current dataset (from skyfield) is good to just before John Lennon's 113th birthday; so that'll need an update at some point...

Once a plot has been created, it can be animated. Basically this clears the chart and re-draws it on an hour-by-hour and day-by-day basis; optionally generating a video file. SkyQuest maintains 2 views on the data: that which renders the overall plot in its entirety, and; that which renders the plot as a sequenced animation. This supports fast visibility toggling of aspects of the plot (e.g. turning the lunar arc on or off), and also allows those aspects to be excluded from the (reccorded) animation. The animation can proceed either:
- To the full accccumulation of the plot, or
- as a sliding time window across the full day-range of the plot; e.g. to show a full monthly cycle changing across a year

SkyQuest is well aware of just what it IS. There are a number of founding principals woven inherently into the source-code. You might want to argue that I should have been more absract in my modelling, to make the code more (re)useful; I'd counter, you know, life is finite.  Anyways, so we are clear:

- SkyQuest shows a (possibly stacked) day-by-day view, with a 'day' being the 24h hour period that follows noon on a given date.
- Altitudes (and illumation) of objects are plotted to an hourly resolution.
- Events (sunrise, onset of astronomical twilight, etc...) are plotted to a minute resolution.
- There are 9 such events in a day
- Video is output in HD resolution at 50fps - i.e. at a rate of 2 full animated days per second.

In-code, SkyQuest is presented as a cast of ancient greek mythological figures and concepts. Time is presented as both its fundamental material (Chronos) and its working mechanics (Kairos) with some influence of the fates (Moirai) also. Tiphys (helmsman of the Argonauts) provides the navigational support by caring for our home base vantage and our destination (selected celestial bodies). Idmon (the Argonaut's seer) connects us with our almanacs (from skyfield). Astreus (a Greek god of astrology) visualises Idmon's prophecies, through a rich collection of artboard, inscription tools, and parchment.
'''
world = True # I haven't properly coded semantic/lexical associations yet so this is just here to ensure the WORLD view gets extracted!

from aeonforge import Chronos, Kairos
from astraeus import Astraeus

# --- Tiphys: Navigator of Location ---
'''
FIGURATION:
Tiphys was the Argonaut's navigator, and here takes care of location based concepts - i.e where we are and where we are going.
'''
class Tiphys(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()

        self.location_button = QPushButton("Set Location")
        self.location_button.clicked.connect(self.open_location_dialog)
        self.layout.addWidget(self.location_button)

        self.layout.addWidget(QLabel("Target:"))
        self.target_selector = QComboBox()
        self.layout.addWidget(self.target_selector)

        self.setLayout(self.layout)

        # Internal store for lat/lon, initially unset
        self.homebase = self.HomeBase(self)
        self.latitude = self.homebase.get_location()["latitude"]
        self.longitude = self.homebase.get_location()["longitude"]


        '''
        KNOWLEDGE:
        Right now we have small, hand curated, list of celestial references. Really, this ought  to get loaded from a JSON file, with some kind of tool to support maintaing that by navigating the options within our almanac.
        '''
        self.targets = {
            "M42 (Orion Nebula)": (5.588139, -5.391111),
            "M27 (Dumbbell Nebula)": (19.993417, 22.721111),
            "M57 (Ring Nebula)": (18.893083, 33.029167),
            "M76 (Little Dumbbell)": (1.705278, 51.575278),
            "NGC 7000 (North America Nebula)": (20.971389, 44.528611),
            "IC 5070 (Pelican Nebula)": (20.85, 44.0),
            "NGC 6960 (Veil West)": (20.760556, 30.716667),
            "NGC 6992 (Veil East)": (20.933333, 31.716667),
            "NGC 7635 (Bubble Nebula)": (23.346667, 61.201667),
            "M8 (Lagoon Nebula)": (18.05, -24.383333),
            "M20 (Trifid Nebula)": (18.033333, -23.033333),
            "M16 (Eagle Nebula)": (18.3, -13.783333),
            "M17 (Swan Nebula)": (18.333333, -16.183333),
            "NGC 6888 (Crescent Nebula)": (20.2, 38.35),
            "IC 1318 (Sadr Region)": (20.333333, 40.5),
            "NGC 7023 (Iris Nebula)": (21.016667, 68.166667),
            "NGC 457 (Owl Cluster)": (1.325722, 58.290833),
            # NB. we group the planets together at the end so we can commprehend the list laters...
            #     also in order of reducing orbit
            "Neptune": "neptune barycenter",
            "Uranus": "uranus barycenter",
            "Saturn": "saturn barycenter",
            "Jupiter": "jupiter barycenter",
            "Mars": "mars",
            "Venus": "venus",
            "Mercury": "mercury",
            "Planets": "all planet arcs"
        }

        for name in self.targets:
            self.target_selector.addItem(name)

    def open_location_dialog(self):
        if self.homebase.exec_() == QDialog.Accepted:
            location = self.homebase.get_location()
            self.latitude = location["latitude"]
            self.longitude = location["longitude"]

    '''
    KNOWLEDGE:
    From where we are looking
    '''
    @property
    def vantage(self):
        return {
            "latitude": self.latitude,
            "longitude": self.longitude
        }

    '''
    MECHANISM:
    gives us a list of dicts of the things we want to observe. These things may either be planets (with their skyfield-internal id) or objects designated by ra/dec values.
    Tiphys is a little surly in these regards, currently lettting us choose either all the planets, or **a** planet or single object. However, he supplies the info as a list, so with a little further care, we could provide for much richer queries.
    '''
    @property
    def destination(self):
        name = self.target_selector.currentText()
        value = self.targets[name]

        if isinstance(value, str):
            # Planet identifier, defer to Idmon to resolve
            if name.lower() == "planets":
                planet_items = list(self.targets.items())[-8:-1]  # exclude "Planets" itself
                return [
                    {"name": pname, "skyfield_id": pval}
                    for pname, pval in planet_items
                ]
            else:
                return [{
                    "name": name,
                    "skyfield_id": value
                }]
        else:
            # Fixed celestial coordinate
            return [{
                "name": name,
                "ra_hours": float(value[0]),
                "dec_degrees": float(value[1])
            }]


    '''
    MECHANISM:
    Although ancient, Tiphys is fully up-to-date with GDPR type concerns. The vantage (home location) is hidden behind a buttton so it isn't captured by any screen grabs.
    This could be quite lovely if it were to open a map-picker interface
    '''
    class HomeBase(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Set Observer Location")

            layout = QFormLayout()
            self.lat_input = QLineEdit("54.489285")
            self.lon_input = QLineEdit("-0.768364")
            layout.addRow("Latitude:", self.lat_input)
            layout.addRow("Longitude:", self.lon_input)

            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(self.accept)
            button_box.rejected.connect(self.reject)
            layout.addWidget(button_box)

            self.setLayout(layout)

        def get_location(self):
            return {
                "latitude": float(self.lat_input.text()),
                "longitude": float(self.lon_input.text())
            }


# --- Idmon: Oracle of Celestial Motion ---
'''
FIGURATION:
Idmon was a seer for the Argonauts, in fact he foresaw his own death on the voyage but went along anyway...
This quest is a little easier for him, he consults the almanacs to tell us where things are on a given hour. 
He always tracks the sun and the moon and informs us about the daylight, twilight and night-time bands for any given date; along with the moon-illumination at each hour of a given date.
Obvs, we also get the altitude data for observed objects on a (24) hourly basis for any given date.
He's kind of micro-managed, so if we want data for multiple days, or multiple target objects on a given date, he has to be re-consulted.
'''
class Idmon:
    def __init__(self):
        # KNOWLEDGE: this retrieves the almanac, which must have been downloaded
        self.loader = Loader('./skyfield-data')
        self.ts = self.loader.timescale()
        self.ephemeris = self.loader('de421.bsp')
        self.moon = self.ephemeris['moon']

        self.observer = None
        self.obs = None
        self.date = None
        self.day_hours = []
        self.location = self.ephemeris['earth']

    '''
    BEHAVIOUR:
    Does the heavy-lifting needed to consult the almanac for a number of things on a given date. This takes account of the fact that the vantage point shifts (with respect to the heavens) over the course of a day due to the earth's rotation. 
    Note that because the lunar arc is always available to the plot, **and** because we use the moon-illumination when plotting other arcs, Idmon provides those as soon as the heavy-lifting has been achieved.
    '''
    def set_transit(self, vantage, date):
        self.date = date
        self.observer = Topos(latitude_degrees=vantage["latitude"], longitude_degrees=vantage["longitude"])
        self.location = self.ephemeris['earth'] + self.observer

        # Time range: 24 hrs
        self.day_hours = range(0, 25)
        
        # Step 1: Build UTC datetime list
        dt_utcs = [Kairos.true_hour(date, h) for h in self.day_hours]
        
        # Step 2: Skyfield time array
        t_array = self.ts.utc(dt_utcs)
        
        # Step 3: Batched observatory positions
        self.obs = self.location.at(t_array)

        # Moon
        moon_app = self.obs.observe(self.moon).apparent()
        moon_alts = moon_app.altaz()[0].degrees.tolist()
        arc_moon = (self.day_hours, moon_alts)

        # Illumination
        illum_values = moon_app.fraction_illuminated(self.ephemeris["sun"]).tolist()

        return arc_moon, illum_values

    '''
    MECHANISM:
    Provides the altitude of a given target at each hour of the transit date; handles both planetary and star type targets.
    '''
    def get_transit_arc(self, destination):
        if "skyfield_id" in destination:
            self.target = self.ephemeris[destination["skyfield_id"]]
        else:
            self.target = Star(
                ra_hours=destination["ra_hours"],
                dec_degrees=destination["dec_degrees"]
            )

        target_app = self.obs.observe(self.target).apparent()
        target_alts = target_app.altaz()[0].degrees.tolist()
        arc_target = (self.day_hours, target_alts)

        return arc_target

    '''
    MECHANISM:
    Works out the daily event times, e.g. sunrise et al. on the transit date
    provides a list of (9) start/end times-of-day periods consulting Kairos to prescribe the type of the time-period (day, night, etc...)
    Whilst it doesn't attemt to differentiate between dusks and dawns that is to our advantage because neither do we! All that matters to us is the daylight level: true night, astronomical twilight, nautical twilght, etc.. whichever end of the day we find those levels.
    Logically speaking we get 9 of these per day. We can cope with fewer (like we might see near the poles) but we have a deeply grounded faith that no day (24 hour period) will see the sun rise twice. I think that's reasonable.
    '''
    def get_twilight_bands(self):
        # Anchor: local noon on the given date
        utc_anchor = Kairos.true_hour(self.date, 0)
        utc_end = Kairos.true_hour(self.date, 24)

        # Skyfield time range... in a format that supports Julian dates which allows simplified (and vectorised) calculations. 
        t0 = self.ts.utc(utc_anchor)
        t1 = self.ts.utc(utc_end)

        # Get twilight transitions
        f = dark_twilight_day(self.ephemeris, self.observer)
        times, events = find_discrete(t0, t1, f, epsilon=60 / 86400)

        # Build bands
        bands = []

        if not times:
            return [(0.0, 24.0, Kairos.get_day_band(4))]  # Default daylight

        # First segment: from 12.0 to first transition
        end = Kairos.utc_hours_difference(times[0].utc_datetime(), utc_anchor)
        bands.append((0.0, end, Kairos.get_day_band(events[-1])))

        # Intermediate bands
        for i in range(len(times) - 1):
            start = Kairos.utc_hours_difference(times[i].utc_datetime(), utc_anchor)
            end = Kairos.utc_hours_difference(times[i+1].utc_datetime(), utc_anchor)
            bands.append((start, end, Kairos.get_day_band(events[i])))

        # Final segment
        start = Kairos.utc_hours_difference(times[-1].utc_datetime(), utc_anchor)
        bands.append((start, 24.0, Kairos.get_day_band(events[-1])))
        return bands

# --- Main Storyteller UI ---
'''
AFFORDANCE:
On this quest everybody works within The Observatory.
It allows queries to be resolved on a day-by-day basis. Each of the attendants concentrate on a given day, as sequenced by the query presented.
Each of the key players provide their own control panels: vantage and targets from Tiphys; date and range from Chronos; Various plot settings from Astreus.  The observatory itself presents the master control (the hosios - attending the prophet Idmon - button).
'''
class Observatory(QWidget):
    def __init__(self, app_name):
        super().__init__()
        self.setWindowTitle(app_name)
        self.layout = QVBoxLayout()

        self.tiphys = Tiphys()
        self.layout.addWidget(self.tiphys)

        self.astraeus = Astraeus()

        chronos_row = QHBoxLayout()
        self.chronos = Chronos()
        chronos_row.addWidget(self.chronos)
        self.chronos.telos = self.present_query
        QShortcut(QKeySequence(Qt.Key_Left), self).activated.connect(lambda: self.chronos.arche_flux(-1))
        QShortcut(QKeySequence(Qt.Key_Right), self).activated.connect(lambda: self.chronos.arche_flux(1))
        # QShortcut(QKeySequence(Qt.Key_Down), self).activated.connect(lambda: self.chronos.aion_flux(-1))
        # QShortcut(QKeySequence(Qt.Key_Up), self).activated.connect(lambda: self.chronos.aion_flux(1))

        chronos_row.addLayout(self.astraeus.artboard.layout)

        chronos_container = QWidget()
        chronos_container.setLayout(chronos_row)
        self.layout.addWidget(chronos_container)


        self.hosios_button = QPushButton("Summon the Oracle")
        self.hosios_button.clicked.connect(self.present_query)
        self.layout.addWidget(self.hosios_button)

        self.layout.addWidget(self.astraeus.artboard)

        self.setLayout(self.layout)

        self.idmon = Idmon()

    '''
    BEHAVIOUR:
    THIS is the telos, the fulfillment of our destiny. 
    Sets up the specific observation requested then steps through the day range to marshal the skills of Idmon and Astraeus to build-up the results.
    Finally calling on Astraeus to complete the works and present the plot
    '''
    def present_query(self):
        # Right now we only have 1 grouped option, the planets
        # so Tiphys doesn't bother to give us a name for a group of destinations!!!
        name = "Major Planets"
        if len(self.tiphys.destination) == 1:
            name = self.tiphys.destination[0]["name"]

        date = self.chronos.arche_date
        days = self.chronos.aion
        self.astraeus.commence_presentation(name, date, days)
        for day in range(days):
            # Set transit
            moon_arc, illumination = self.idmon.set_transit(self.tiphys.vantage, date)

            twilight = self.idmon.get_twilight_bands()

            # get target arcs
            target_arcs = []
            for arc_num, destination in enumerate(self.tiphys.destination):
                target_arc = self.idmon.get_transit_arc(destination)
                target_arcs.append(target_arc)

            labels = [Kairos.what_time_is_it(date, h) for h in range(25)]

            # Draw arcs and such
            self.astraeus.draw_day(
                day,
                labels,
                target_arcs,
                moon_arc,
                illumination,
                twilight
            )

            # step to next day of intest
            date += timedelta(days=1)

        self.astraeus.complete_presentation()

# --- Run the Quest ---
'''
BEHAVIOUR:
Powers-up the observatory and allows it to run until explicitly stopped by the user exiting the main app by mouse or keyboard.
'''
def main():
    app = QApplication(sys.argv)
    window = Observatory("Sky Quest")
    app.setFont(QFont("Quattrocento Sans", 16))
    QShortcut(QKeySequence(Qt.Key_Escape), window).activated.connect(window.showNormal)
    window.showMaximized()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()