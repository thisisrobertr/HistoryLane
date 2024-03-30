#!/usr/bin/env python3
# historylane.py
# written by Robert Ryder, July 2023
import browserhandler, chartgen
import argparse
import sys


POSSIBLE_CATEGORIES = ['counter', 'duration', 'time']

cmdline = argparse.ArgumentParser(sys.argv)
cmdline.add_argument('-b', action=argparse.BooleanOptionalAction,
                     help='Generate a bar chart for each domain in browser history; height is the value of a category')

cmdline.add_argument('-s', action=argparse.BooleanOptionalAction,
                     help='Generate a scatterplot of website visits according to two categories.')

cmdline.add_argument('-l',
                     action=argparse.BooleanOptionalAction,
                     help='Generate a line plot similar to the scatterplot of -s.')

cmdline.add_argument('-p',
                     action=argparse.BooleanOptionalAction,
                     help='Generate a pie chart representing the share of your web browsing occupied by each website.')

cmdline.add_argument('-w',
                     dest='w',
                     type=str,
                     help='Specify the web browser to analyze. Present options include Apple Safari, Mozilla Firefox, and Vivaldi.')

cmdline.add_argument('-t',
                     dest='t',
                     type=int,
                     default=10,
                     help='The minimum threshold of visits a website must have to be included in the final graph. Use this - as you like - to reduce the number of results; it makes graphs cleaner and more legible.')

cmdline.add_argument('-f',
                     dest='output_file',
                     type=str,
                     help='If supplied, the graph will be saved as an image to the provided filename.')

cmdline.add_argument('-u',
                     dest='user_profile',
                     type=str,
                     help='For Mozilla Firefox- or Google Chrome-based browsers, this argument specifies the profile to use.')

cmdline.add_argument('-c',
                     dest='user_category_a',
                     type=str,
                     default='counter',
                     help='The category by which to organize the x-axis. This value also selects category in graphs (e.g., pie charts) where only one value is used. Defaults to "counter," or the number of visits to each site.')

cmdline.add_argument('-d',
                     dest='user_category_b',
                     type=str,
                     default='duration',
                     help='This selects the category by which the y-axis is organized.')

argv = cmdline.parse_args()

if argv.user_category_a not in POSSIBLE_CATEGORIES:
    raise RuntimeError('Please select one of counter, duration, or time for -c')

if argv.user_category_b not in POSSIBLE_CATEGORIES:
    raise RuntimeError('Please select one of counter, duration, or time for -d')

history = None

# Decide whence to extract history data based on user input.
if argv.w is None:
    # No browser specified - can't do anything
    raise RuntimeError('Please select a supported browser with the -w option.')

elif argv.w.lower() == 'safari':
    # User has asked for Safari, but we're not on a mac.
    if sys.platform != 'darwin':
        raise RuntimeError('Apple Safari is only supported on macOS.')
    
    history = browserhandler.get_all_safari_data()
    
elif argv.w.lower() == 'firefox':
    # Firefox and Chrome-based browsers have history divided into distinct user profiles
    # If one of these is not specified, we don't know what to access. Insist that the user make this explicit.
    if not hasattr(argv, 'user_profile'):
        raise RuntimeError('A profile is required when working with Mozilla Firefox. A list of profiles is available from Firefox\'s about:profiles page')
    
    history = browserhandler.get_all_firefox_data()
    if argv.user_profile not in history:
        raise RuntimeError('The specified profile does not exist')
    
    history = history[argv.user_profile].entries
    
elif argv.w.lower() == 'vivaldi':
    if not hasattr(argv, 'user_profile'):
        raise RuntimeError('A user profile must be provided with -u when analyzing Google Chrome-based browsers')

    if argv.user_profile not in browserhandler.VivaldiProfile.get_all_profile_names():
        raise RuntimeError('The specified user profile does not exist')
    
    history = browserhandler.get_all_vivaldi_data()[argv.user_profile].entries
    #history = history[argv.user_profile].entries  # 3/13/24 - consolidated into one line - double-defining a variable is redundant and confusing
    
else:
    raise RuntimeError('Please select a supported browser with the -w option.')

# Generate the specified chart
if argv.b:
    chartgen.generate_barchart(history, th=argv.t) 
if argv.s:
    chartgen.generate_scatterplot(history, hcategory=argv.user_category_a, vcategory=argv.user_category_b, th=argv.t)
if argv.l:
    chartgen.generate_linechart(history, hcategory=argv.user_category_a, vcategory=argv.user_category_b, th=argv.t)
if argv.p:
    chartgen.generate_piechart(history, category=argv.user_category_a, th=argv.t)

chartgen.render_plot()
