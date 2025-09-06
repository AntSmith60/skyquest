from continuum import *
'''
THROUGHLINE:
Herein we steward time so that no-one else needs to worry about the vagueries of time management.

Just like the ancient greeks did, we split our concept of time into the material itself (how much of it we have to work with) and the mechanics of it (the expressions of time).

There are 2 key underlying concepts that are woven throughout:
- All days start at noon and last for exactly 24 hours. This places midnight at the center of our inquiries, since astronomers are implicitly night-owls. Also note, 24hrs from noon may or may not be noon on the following day, since we display local times along with the vagueries of daylight saving.
- Days are divided into, at most, 9 bands of daytime, night-time, dawns and dusks (civil, nautical, astronomical). Never more than 9 (the sun only rises once per day).

Note that we have imported QWidget from the continuum in its own (alien) metaphor. We allow that metaphor (of layouts, labels and fonts) to pervade here out of kindness to the sanity of others reading this module... but the underlying data concepts and exposures are within our chrono-mytho metaphor; as you will see.
'''

'''
FIGURATION:
As the personification of time itself, Chronos sets the temporal limits of an inquiry.
'''
class Chronos(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()
        self.layout.setSpacing(4)
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # Date Inputs
        date_layout = QVBoxLayout()
        date_layout.setAlignment(Qt.AlignLeft)

        start_layout = QHBoxLayout()
        label_start = QLabel("Start Date:")
        label_start.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        start_layout.addWidget(label_start)

        # KNOWLEDGE: the denoted start of time, allowing for the entry of a (niave) date
        self.chronogenesis = QDateEdit(calendarPopup=True)
        self.chronogenesis.setDate(QDate.currentDate())
        self.chronogenesis.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        start_layout.addWidget(self.chronogenesis)
        date_layout.addLayout(start_layout)

        duration_layout = QHBoxLayout()
        label_duration = QLabel("Duration (days):")
        label_duration.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        duration_layout.addWidget(label_duration)

        # KNOWLEDGE: the denoted destiny, the time alloted to us by the Fates (or Moirai) - as a simple integer
        self.moira = QSpinBox()
        self.moira.setRange(1, 999)
        self.moira.setValue(7)
        self.moira.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        duration_layout.addWidget(self.moira)
        date_layout.addLayout(duration_layout)

        self.layout.addLayout(date_layout)

        # Navigation buttons
        font = QFont()
        font.setPointSize(20)

        nav_layout = QHBoxLayout()
        nav_layout.setAlignment(Qt.AlignLeft)

        self.back_button = QPushButton(" ◀ ")
        self.back_button.setFont(font)
        self.back_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        nav_layout.addWidget(self.back_button)

        self.forward_button = QPushButton(" ▶️ ")
        self.forward_button.setFont(font)
        self.forward_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        nav_layout.addWidget(self.forward_button)

        self.layout.addLayout(nav_layout)

        # External callback
        '''
        MECHANISM:
        For the fulfillment of our destiny. The quest itself is governed by The Observatory, which provides it (via callaback) to Chronos so that time-flux based impulses can be satisifed.
        '''
        self.telos = None

        # Connections
        self.back_button.clicked.connect(lambda: self.arche_flux(-1))
        self.forward_button.clicked.connect(lambda: self.arche_flux(1))
        '''
        IMPULSE:
        If something changes our destiny (our alloted time) we attempt to fulfill it through quest
        '''
        self.moira.valueChanged.connect(self._quest)
        '''
        IMPULSE:
        If a new aion begins then we  we attempt to fulfill our destiny through quest
        '''
        self.chronogenesis.dateChanged.connect(self._quest)

        self.setLayout(self.layout)

    '''
    BEHAVIOUR:
    A change in the chronogenesis implicitly invokes a new aion, a new quest
    '''
    def arche_flux(self, offset):
        self.chronogenesis.setDate(self.chronogenesis.date().addDays(offset))

    '''
    IMPULSE:
    Although we never directly see our destiny (it is elsewhere written in the stars) we can still reach it through quest; which is triggered by any change in time, or by The Observatory when a new query is presented.
    '''
    def _quest(self):
        if self.telos:
            self.telos()

    # KNOWLEDGE: the exact dawn of time (the first date)
    @property
    def arche_date(self):
        return self.chronogenesis.date().toPyDate()

    # KNOWLEDGE: our precise allotment of time
    @property
    def aion(self):
        return self.moira.value()

    # KNOWLEDGE: the end of days
    @property
    def eschatos(self): 
        return self.arche_date + timedelta(days=self.aion-1)

    '''
    BEHAVIOUR:
    A change in our destiny, our alloted time.
    '''
    def aion_flux(self, offset):
        new_destiny = self.moira.value() + offset
        new_destiny = min(999, max(1, new_destiny))
        self.moira.setValue(new_destiny)

# --- Kairos: Provides provides us with the mechanics of time ---

'''
AFFORDANCE:
Regarding the nature of time, whilst Chronos concerns sequence, Kairos concerns moment.
Through the mechanics of Kairos we attain fundamental knowledge of moments such as 'what time is it, here'; 'what daylight band is it?'

One day Kairos will also understand the Vantage that Tiphys has set to better help us understand what time it is, although right now it always thinks we are in London!
'''
class Kairos(Chronos):
    # KNOWLEDGE: reference for local time
    local_tz = ZoneInfo("Europe/London")
    
    # KNOWLEDGE: meaning of oblique twilight band codes (as revealed by Idmon) - note that twilight covers both ends of the day (dawn and dusk)
    day_bands = {
        0: "night",
        1: "astronomical_twilight",
        2: "nautical_twilight",
        3: "civil_twilight",
        4: "day",
        5: "apocalypse" # guardian value incase the event interface changes
    }

    def __init__(self):
        super().__init__()

    @classmethod
    def get_day_band(cls, event):
        return cls.day_bands.get(event, "apocalypse")

    '''
    MECHANISM:
    provides the universal time for a given offset from noon of a given date.
    We work from noon because midnight is always at the center of our focus.
    '''
    @classmethod
    def divine_universal_time(cls, base_date, hour_offset, minute_offset=0, second_offset=0):
        local_noon = datetime(base_date.year, base_date.month, base_date.day, 12, tzinfo=cls.local_tz)
        utc_anchor = cls.to_utc(local_noon)
        dt_utc = utc_anchor + timedelta(hours=int(hour_offset), minutes=int(minute_offset), seconds=int(second_offset))
        return dt_utc

    '''MECHANISM:
    provides the universal time for a given hour after noon on a given date
    Allows us to be agnostic to timezones and daylight saving concerns
    Slightly blunt since we only allow for hour-resolution, but that is all we ever use.
    '''
    @classmethod
    def true_hour(cls, base_date, hour_offset):
        dt_utc = cls.divine_universal_time(base_date, hour_offset)
        return dt_utc

    '''
    MECHANISM:
    Tells us what time it is at a given time!
    We can never really know what time it really is... because of daylight saving!
    So this answers the question, what time is it 'x' hours after noon on 'date', where we are asking from.
    '''
    @classmethod
    def what_time_is_it(cls, base_date, hour_offset):
        dt_utc = cls.divine_universal_time(base_date, hour_offset)
        dt_local = dt_utc.astimezone(cls.local_tz)
        return dt_local.strftime("%H:%M")

    '''
    MECHANISM:
    Finds the (fractional) hours separation between two UTC times
    '''
    @classmethod
    def utc_hours_difference(cls, t0, t1):
        t0_utc = cls.to_utc(t0, as_guardian=True) # let's be sure
        t1_utc = cls.to_utc(t1, as_guardian=True) # let's be sure
        return (t0_utc - t1_utc).total_seconds() / 3600

    '''
    MECHANISM:
    Convert any (not niave) time to UTC, allowing for daylight saving
    (can also check that a time **is** UTC)
    '''
    @classmethod
    def to_utc(cls, dt_local, as_guardian=False):
        if dt_local.tzinfo is None:
            # utterly niave usercode needs to know about it
            raise ValueError("OOPS:: Programme Error: Naive Time Deployed - FIX IT!")

        if as_guardian:
            if dt_local.tzname().upper() != 'UTC':
                # nb. we don't have a logger in this simple script! 
                # I know, CLI output is fine - leave me alone
                err_msg = f"OOPS:: Programme Error: Unexpected local time ({dt_local.tzname()}) - FIX IT if you wanna suppress this nag"
                print(err_msg)
                # raise ValueError(err_msg)

        return dt_local.astimezone(ZoneInfo("UTC"))
