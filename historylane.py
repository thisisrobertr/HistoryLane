#!/usr/bin/env python3
# historylane.py
# written by Robert Ryder, July 2023

import sqlite3
import os.path
import time
import json
import glob
import argparse
import matplotlib.pyplot as plt
import sys

USER_DIR = os.path.expanduser('~')  # cross-platform despite its Unix-inflected appearance

# Apple Safari constants
SAFARI_HISTORY_DB = USER_DIR + '/Library/Safari/History.db'
SAFARI_EPOCH = 978307200  # midnight UTC on 1 January 2001
SAFARI_EPOCH_WEBKIT = 116_444_73600 + 978307200  # Seconds between 1/1/1601 and 1/1/2001

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
    VIVALDI_DIRECTORY = USER_DIR + '/Library/Application Support/Vivaldi'
elif sys.platform == 'win32':
    VIVALDI_DIRECTORY = USER_DIR + '/AppData/Local/Vivaldi'
else:
    VIVALDI_DIRECTORY = USER_DIR + '.config/vivaldi'

# Graphics parameters
LABEL_TRUNCATION = 40  # truncate long graph labels (such as URLs) at a certain number of characters.

class SafariHistory:
    # Allow browser-wide attributes.
    def __init__(self):
        self.maximum_counter = -1
        self.maximum_duration = -1
        self.entries = {}

def get_safari_data_individually():
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
    def __chrome_to_safari_time(t):
        result = t // 1_000_000  # microseconds to seconds
        result -= SAFARI_EPOCH_WEBKIT  # Webkit to Safari/Unix
        return result
    
    def __init__(self, path):
        self.maximum_counter = -1
        self.maximum_duration = -1
        self.cursor = sqlite3.connect(path + '/History').cursor()
        self.entries = None

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

def get_vivaldi_data_individually():    
    # Timestamps, as mentioned use the Chrome/Webkit format. This means that they represent microseconds
    # elapsed since midnight UTC on January 1, 1601.
    profiles = {}
    
    disk_profiles = glob.glob(VIVALDI_DIRECTORY + '/Profile*')
    for i in disk_profiles:
        # Create relevant keys
        with open(i + '/Preferences') as f:
            name = json.load(f)['profile']['name']  # i + '/Preferences')['profile']['name']
            f.close()

        profiles[name] = None

    for counter, i in enumerate(profiles.keys()):
        p = VivaldiProfile(VIVALDI_DIRECTORY + '/Profile %d' % (counter + 1))
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

def get_firefox_data_individually():
    profiles = {}
    disk_profiles = glob.glob(FIREFOX_DIR + '/Profiles/*default')
    for counter, i in enumerate(disk_profiles):
        p = FirefoxProfile(i)
        p.entries = p.get_visits()
        profiles[i.split('/')[-1]] = p

    return profiles

def generate_piechart(sites, axes, category='visits', th=0):
    visits = []
    visit_labels = []
    for i in sites:
        if len(sites[i]) < th:
            continue
        visits.append(len(sites[i]))
        visit_labels.append(i[:LABEL_TRUNCATION])

    axes.pie(visits, labels=visit_labels)

def generate_scatterplot(sites, axes, hcategory='counter', vcategory='duration', th=0):
    xaxis = []
    yaxis = []
    labels = []
    axes.xscale('log')
    axes.yscale('log')
    for i in sites:
        if len(sites[i]) < th: continue
        for j in sites[i]:
            xaxis.append(j[hcategory])
            yaxis.append(j[vcategory])
            labels.append(i[:LABEL_TRUNCATION])
        
        axes.scatter(xaxis, yaxis)

def generate_linechart(sites, axes, hcategory='counter', vcategory='duration', th=0):
    xaxis = []
    yaxis = []
    labels = []
    axes.xscale('log')
    axes.yscale('log')
    for i in sites:
        if len(sites[i]) < th: continue
        for j in sites[i]:
            xaxis.append(j[hcategory])
            yaxis.append(j[vcategory])
            labels.append(i[:LABEL_TRUNCATION])
        
        axes.plot(xaxis, yaxis)

def generate_barchart(sites, axes, label_by='title', th=0):
    axes.set_xticks([])
    axes.set_xticklabels([])
    axes.set_yscale('log')
    counter = 0
    for i in sites:
        if len(sites[i]) < th: continue
        axes.bar(counter, len(sites[i]), label=i[:LABEL_TRUNCATION])
        counter += 1

def generate_barchart_visits(sites, axes, category='counter', label_by='title', th=0):
    axes.set_xticks([])
    axes.set_xticklabels([])
    bars = []
    bar_labels = []
    counter = 0
    for i in sites:
        if len(sites[i]) < th: continue
        for j in sites[i]:
            bars.append(j[category])
            if j[label_by] is not None:
               bar_labels.append(j[label_by][:LABEL_TRUNCATION])
            else:
                bar_labels.append('')

        axes.bar(range(counter,counter+len(bars)), bars, label=bar_labels)
        counter += len(bars)
        bars = []
        bar_labels = []


POSSIBLE_CATEGORIES = ['counter', 'duration', 'time']

cmdline = argparse.ArgumentParser(sys.argv)
cmdline.add_argument('-b', action=argparse.BooleanOptionalAction,
                     help='Generate a bar chart for each domain in browser history; height is the value of a category')
cmdline.add_argument('-s', action=argparse.BooleanOptionalAction,
                     help='Generate a scatterplot of website visits according to two categories.')
cmdline.add_argument('-l', action=argparse.BooleanOptionalAction,
                     help='Generate a line plot similar to the scatterplot of -s.')
cmdline.add_argument('-p', action=argparse.BooleanOptionalAction,
                     help='Generate a pie chart representing the share of your web browsing occupied by each website.')
cmdline.add_argument('-v', action=argparse.BooleanOptionalAction,
                     help='Generate a bar chart of each URL visited.\n\tWarning: this will very likely be an extremely dense graph, and generating it is not fast.')
cmdline.add_argument('-w', dest='w', type=str,
                     help='Specify the web browser to analyze. Present options include Apple Safari, Mozilla Firefox, and Vivaldi.')
cmdline.add_argument('-t', dest='t', type=int, default=0,
                     help='The minimum threshold of visits a website must have to be included in the final graph. Use this - as you like - to reduce the number of results; it makes graphs cleaner and more legible.')
cmdline.add_argument('-f', dest='output_file', type=str,
                     help='If supplied, the graph will be saved as an image to the provided filename.')
cmdline.add_argument('-u', dest='user_profile', type=str,
                     help='For Mozilla Firefox- or Google Chrome-based browsers, this argument specifies the profile to use.')
cmdline.add_argument('-c', dest='user_category_a', type=str, default='counter',
                     help='The category by which to organize the x-axis. This value also selects category in graphs (e.g., pie charts) where only one value is used. Defaults to "counter," or the number of visits to each site.')
cmdline.add_argument('-d', dest='user_category_b', type=str, default='duration',
                     help='This selects the category by which the y-axis is organized.')

argv = cmdline.parse_args()

if argv.user_category_a not in POSSIBLE_CATEGORIES:
    raise RuntimeError('Please select one of counter, duration, or time for -c')

if argv.user_category_b not in POSSIBLE_CATEGORIES:
    raise RuntimeError('Please select one of counter, duration, or time for -d')

history = None

if argv.w is None:
    raise RuntimeError('Please select a supported browser with the -w option.')
elif argv.w.lower() == 'safari':
    if sys.platform != 'darwin':
        raise RuntimeError('Apple Safari is only supported on macOS.')
    history = get_safari_data_individually()
elif argv.w.lower() == 'firefox':
    if not hasattr(argv, 'user_profile'):
        raise RuntimeError('A profile is required when working with Mozilla Firefox. A list of profiles is available from Firefox\'s about:profiles page')
    history = get_firefox_data_individually()
    if argv.user_profile not in history:
        raise RuntimeError('The specified profile does not exist')
    history = history[argv.user_profile].entries
elif argv.w.lower() == 'vivaldi':
    if not hasattr(argv, 'user_profile'):
        raise RuntimeError('A user profile must be provided with -u when analyzing Google Chrome-based browsers')
    history = get_vivaldi_data_individually()
    if argv.user_profile not in history:
        raise RuntimeError('The specified user profile does not exist')
    history = history[argv.user_profile].entries
else:
    raise RuntimeError('Please select a supported browser with the -w option.')

if argv.b:
    generate_barchart(history, plt.subplots()[1], th=argv.t)
if argv.v:
    generate_barchart_visits(history, plt.subplots()[1], category=argv.user_category_a, th=argv.t)
if argv.s:
    generate_scatterplot(history, plt.subplots()[1], hcategory=argv.user_category_a, vcategory=argv.user_category_b, th=argv.t)
if argv.l:
    generate_linechart(history, plt.subplots()[1], hcategory=argv.user_category_a, vcategory=argv.user_category_b, th=argv.t)
if argv.p:
    generate_piechart(history, plt.subplots()[1], category=argv.user_category_a, th=argv.t)

plt.tight_layout()
plt.legend()

if argv.output_file:
    plt.savefig(argv.output_file)

plt.show()