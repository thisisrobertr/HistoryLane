import sqlite3
import os.path
import time
import json
import glob
import sys

USER_DIR = os.path.expanduser('~')  # Cross-platform courtesy of Python

# Apple Safari constants
SAFARI_HISTORY_DB = USER_DIR + '/Library/Safari/History.db'
SAFARI_EPOCH = 978307200  # midnight UTC on 1 January 2001, as per the usual epoch of midnight GMT on 1/1/70
SAFARI_EPOCH_WEBKIT = 116_444_73600 + 978307200  # Seconds between 1/1/1601 and 1/1/2001 - bridge Safari and Chrome

# Mozilla Firefox constants
if sys.platform == 'darwin':
    # Apple Macintosh
    FIREFOX_DIR = USER_DIR + '/Library/Application Support/Firefox'
elif sys.platform == 'win32':
    # Microsoft Windows
    FIREFOX_DIR = USER_DIR + '/AppData/Roaming/Mozilla/Firefox'
else:
    # UNIX arts-and-crafts
    FIREFOX_DIR = USER_DIR + '.mozilla/firefox'

# Vivaldi constants
if sys.platform == 'darwin':
    VIVALDI_DIR = USER_DIR + '/Library/Application Support/Vivaldi'
elif sys.platform == 'win32':
    VIVALDI_DIR = USER_DIR + '/AppData/Local/Vivaldi'
else:
    VIVALDI_DIR = USER_DIR + '.config/vivaldi'


class SafariHistory:
    # Allow browser-wide attributes.
    def __init__(self):
        self.maximum_counter = -1
        self.maximum_duration = -1
        self.entries = {}

def get_all_safari_data():
    # This was written before Safari had profiles, and they are thus not supported.
    
    # SQLITE3 Database Structures:
    # history_items table:
    #    index 0: ID, an integer
    #    index 1: URL, a TEXT
    #    index 2: domain_expansion, a TEXT
    #    index 3: visit_count, an INTEGER
    #    index 4: daily_visit_counters, a BLOB
    #    index 5: weekly_vision_counts, a BLOB
    #    index 6: autocomplete_triggers, a BLOB
    #    index 7: should_recompute_derived_visit_counts, an INTEGER
    #    index 8: visit_count_score, an INTEGER
    #    index 9: status_code, an INTEGER

    # history_visits table:
    #    index 0: id, an INTEGER (NB that IDs are not shared across tables
    #    index 1: history_item, an INTEGER
    #    index 2: visit_time, an INTEGER (expressed in seconds elapsed since midnight UTC on 1 January 2001
    #    index 3: title, a TEXT
    #    index 4: load_successful, a BOOLEAN
    #    index 5: http_non_get, a BOOLEAN
    #    index 6: synthesized, a BOOLEAN
    #    index 7: redirect_source, an INTEGER (presumably, an ID)
    #    index 8: redirect_destination, an INTEGER (also presumably an ID)
    #    index 9: origin, an INTEGER (also also presumably an ID)
    #    index 10: generation, an INTEGER
    #    index 11: attributes, an INTEGER
    #    index 12: score, an INTEGER

    cur = sqlite3.connect(SAFARI_HISTORY_DB).cursor()
    timestamp = (time.time() - 86400*14) - SAFARI_EPOCH

    # Enable fetching for the current day only

    visits = cur.execute('select * from history_visits where visit_time > ?', [timestamp]).fetchall() #where visit_time > ?', [timestamp]).fetchall()
    domains = cur.execute('select distinct domain_expansion from history_items').fetchall()

    results = SafariHistory()
    for i in domains:
        if i is not None:
            results.entries[i[0]] = []  # blunt instrument to prevent key None from creeping in.
    
    for i in range(len(visits) - 1):
        history_item = cur.execute('select * from history_items where id = ?', [visits[i][1]]).fetchall()[0]
        # https://www.
        # 01234567890123
        if history_item[2] is None:
            domain = history_item[1]
            if domain[4] == 's':  # secure connection
                domain = domain[8:]
            else:
                domain = domain[7:]

            domain = domain.split('/')[0]
            domain = os.path.splitext(domain)[0]
            domain = domain.replace('www.', '')

            duration = visits[i + 1][2] - visits[i][2]
            if duration > 600:
                # ten minutes
                duration = 0
            data =  {
                'URL': history_item[1],
                'title': visits[i][3],
                'time': visits[i][2] - timestamp,
                'counter': history_item[3],  # counter
                'duration': duration
            }

            if data['counter'] > results.maximum_counter: 
                results.maximum_counter = data['counter']

            if data['duration'] > results.maximum_duration:
                results.maximum_duration = data['duration']

            if domain not in results.entries:
                results.entries[domain] = [data]
            else:
                results.entries[domain].append(data)

        else:
            duration = visits[i + 1][2] - visits[i][2]

            data = {
                'URL': history_item[1],
                'title': visits[i][3],
                'time': visits[i][2] - timestamp,
                'counter': history_item[3],  # counter
                'duration': duration
            }

            if data['counter'] > results.maximum_counter: 
                results.maximum_counter = data['counter']

            if data['duration'] > results.maximum_duration:
                results.maximum_duration = data['duration']

            results.entries[history_item[2]].append(data)
             
    return results.entries

class VivaldiProfile:
    # Various bits of data are stored in ~/Library/Application Support/Vivaldi/
    # Separate directories are used for each profile
    # The salient pieces are as follows
    # The file "Preferenes" (no extension) stores user settings, including the profile name
    #   It is a vast JSON object; name is stored in the "name" key of the object under
    #      the "profile" key. Thus, using the python dictionary model, it may be accessed like so:
    #      preferences_json_object_name['profile']['name']

    # The file "History" (again, with no extension) is an SQLite3 database with the following structure
    #   (I have only described the relevant portions here; the overall structure is considerably more intricate)
    #
    #   The clusters_and_visits table is structured as follows:
    # 0:      cluster_id, an INTEGER (this refers, presumably, to an item in the "clusters" table)
    # 1:      visit_id, an INTEGER (this likewise presumably refers to an item in the "visits" table)
    # 2:      score, a NUMERIC (something, perhaps, to do with Vivaldi's history UI?)
    # 3:      engagement_score, a NUMERIC (will precipitate the rise of Skynet)
    # 4:      url_for_deduping, a LONGVARCHAR - this is the domain, with protocol, for a particular history entry
    # 5:      url_for_display, a LONGVARCHAR - this contains the website's full URL.
    
    #   The visits table is structured as follows:
    # 0:      id, an INTEGER (I suspect that it is relatively self-explanatory)
    # 1:      url, an INTEGER (purpose TBD)
    # 2:      visit_time, an INTEGER (the time of the visit, expressed using Chrome the timestamp format)
    # 3:      from_visit, an INTEGER (presumably some form of cross-referencing)
    # 4:      visit_duration, an INTEGER
    # 5:      none of the other fields seem to be of relevance
    
    #   The urls table is structured as follows:
    # 0:      id, an INTEGER, a unique intra-table ID.
    # 1:      url, a LONGVARCHAR, the URL in question
    # 2:      title, a LONGVARCHAR, the page's title
    # 3:      visit_count, an INTEGER, the number of visits to the URL in question
    # 4:      typed_count, an INTEGER,  the number of times the user has typed this URL into the address bar.
    # 5:      last_visit_time, an INTEGER, the time of the most recent visit (expressed in Chrome/WebKit time)
    # 6:      hidden, an INTEGER, which serves a purpose that I have not discerned.

    @staticmethod
    def get_all_profile_names():
        disk_profiles = glob.glob(VIVALDI_DIR + '/Profile*')
        profile_names = [None] * len(disk_profiles)
        for i in range(len(disk_profiles)):
            with open(disk_profiles[i] + '/Preferences') as f:
                name = json.load(f)['profile']['name']
                f.close()
            profile_names[i] = name

        return profile_names
    
    @staticmethod
    def __chrome_to_safari_time(t):
        result = t // 1_000_000  # microseconds to seconds
        result -= SAFARI_EPOCH_WEBKIT  # Webkit to Safari/Unix
        return result
    
    def __init__(self, path):
        self.maximum_counter = -1
        self.maximum_duration = -1
        self.cursor = sqlite3.connect(path + '/History').cursor()
        self.entries = None
        self.get_visits() # 3/13/24: this is an expensive operation, but necessary to do anything with this object. Include it here.
        
    def get_visits(self):
        visits = self.cursor.execute('select * from clusters_and_visits').fetchall()
        results = {}
        for counter, i in enumerate(visits):
            if i[4] not in results:
                # The domain has not yet been processed. An empty array with the proper key name must be added
                # so that calls to results[<something or other>].append() work as intended
                results[i[4]] = []
            
            # Because the relevant data are stored across three different tables, cross-referencing is necessary
            # This must, unfortunately, be done for each and every object - a real nuisance for performance.
            visit = self.cursor.execute('select * from visits where id = ?', [i[1]]).fetchall()[0]
            try:
                url_object = self.cursor.execute('select * from urls where url = ?', [i[5]]).fetchall()[0]
            except IndexError:
                # There is no such URL present in the database. We thus cannot fetch required data, and the visit
                # may as well not exist. Pass it by accordingly.
                continue

            time = VivaldiProfile.__chrome_to_safari_time(visit[2])
            data = {
                'URL': i[5],
                'title': url_object[2],
                'time': time,
                'counter': url_object[3],
                'duration': visit[4]  // 1_000_000  # microseconds to seconds.
            }
            if data['counter'] > self.maximum_counter:
                self.maximum_counter = data['counter']

            if data['duration'] > self.maximum_duration:
                self.maximum_duration = data['duration']

            results[i[4]].append(data)

        self.entries = results
        return results

def get_all_vivaldi_data():    
    # Timestamps, as mentioned use the Chrome/Webkit format. This means that they represent microseconds
    # elapsed since midnight UTC on January 1, 1601.
    profiles = {}

    for i in VivaldiProfile.get_all_profile_names():
        profiles[i] = None
        
    for counter, i in enumerate(profiles.keys()):
        p = VivaldiProfile(VIVALDI_DIR + '/Profile %d' % (counter + 1))
        profiles[i] = p

    return profiles

class FirefoxProfile:
    # Partial documentation on the Firefox history database format:
    # Times (called "dates") are expressed in microseconds since midnight UTC on 1 January 1970

    # The moz_historyvisits table is structured as follows:
    #       index 0: id, an INTEGER - a unique intra-table ID
    #       index 1: from_visit, an INTEGER - purpose obscure
    #       index 2: place_id, an INTEGER - this references the relevant row in the moz_places table, described below
    #       index 3: visit_date, an INTEGER - presumably, the date
    #       index 4: visit_type, an INTEGER - purpose obscure
    #       index 5: session, an INTEGER - purpose obscure
    #       index 6: source, an INTEGER - purpose obscure
    #       index 7: triggeringPlaceId, an INTEGER - purpose obscure

    # The moz_plaes table describes each website
    #       index 0: id, an INTEGER - an intra-table id.
    #       index 1: url, a LONGVARCHAR - contains the page's URL
    #       index 2: title, a LONGVARCHAR - contains the page's title
    #       index 3: rev_host, a LONGVARCHAR - contains a reversed version of the website's host.
    #       index 4: visit_count, an INTEGER - the number of visits to a particular site
    #       index 5: hidden, an INTEGER - purpose obscure
    #       index 6: typed, an INTEGER - indicates whether the user directly typed the URL.
    #       index 7: frecency, an INTEGER - purpose obscure.
    #       index 8: last_visit_date, an INTEGER - time of the most recent visit
    #       index 9: guid, a TEXT - purpose obscure
    #       index 10: foreign_count, an INTEGER - purpose obscure
    #       index 11: url_hash - a hash, using an unknown algorithm, of the URL.
    #       index 12: description, a TEXT - purpose obscure
    #       index 13: preview_image_url, a TEXT - purpose obscure
    #       index 14: site_name, a TEXT - seemlingly a repeat of the URL
    #       index 15: origin_id, an INTEGER - presumably, this is an ID in some other table
    #       index 16: recalc_frecency - the "frecency" of something or other.
    #       index 17: alt_frecency - purpose obscure
    #       index 18: recalc_alt_frecency - purpose obscure.

    @staticmethod
    def __mozilla_to_safari_time(t):
        return (t / 1_000_000) - SAFARI_EPOCH
    
    def __init__(self, path):
        self.cursor = sqlite3.connect(path + '/places.sqlite').cursor()
        self.maximum_counter = -1
        self.maximum_duration = -1
        self.entries = {}
        self.get_visits()  # 3/13/24: you'll have to do this anyway, so do it here.
        
    def get_visits(self):
        try:
            visits = self.cursor.execute('select * from moz_historyvisits').fetchall()
        except sqlite3.OperationalError:
            # no such table, which indicates that no history exists
            return {}
        
        try:
            for counter, i in enumerate(visits):
                metadata = self.cursor.execute('select * from moz_places where id = ?', [i[2]]).fetchall()[0]
                domain = ''.join(reversed(metadata[3]))
                if domain not in self.entries:
                    self.entries[domain] = []

                time = self.__mozilla_to_safari_time(i[3])
                data = {
                    'URL': None,
                    'title': metadata[2],
                    'time': time,
                    'counter': i[4],
                    'duration': self.__mozilla_to_safari_time(visits[counter + 1][3]) - time
                }

                if data['counter'] > self.maximum_counter:
                    self.maximum_counter = data['counter']

                if data['duration'] > self.maximum_duration:
                    self.maximum_duration = data['duration']

                self.entries[domain].append(data)
        except IndexError:
            pass

        return self.entries

def get_all_firefox_data():
    profiles = {}
    disk_profiles = glob.glob(FIREFOX_DIR + '/Profiles/*default')
    for counter, i in enumerate(disk_profiles):
        p = FirefoxProfile(i)
        p.entries = p.get_visits()
        profiles[i.split('/')[-1]] = p

    return profiles
