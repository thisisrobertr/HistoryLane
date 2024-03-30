# HistoryLane

This is an application to extract browser history and display it in a graphical format.

---

##I. Dependencies

1. A somewhat-recent version of Python 3 (tested to work with 3.9+), and its standard library
2. Matplotlib (this program is backend-agnostic).
3. Some collection of the supported web browsers: Safari, Firefox (incl. Developer Edition), and Vivaldi.

---

##II. Usage

`python3 historylane.py [options]`

HistoryLane accepts the following options:

  -h, --help          show the help screen and exit.
  -b                  Generate a bar chart for each domain in browser history;
                      height is the value of a category
  -s                  Generate a scatterplot of website visits according to
                      two categories.
  -l                  Generate a line plot similar to the scatterplot of -s.
  -p                  Generate a pie chart representing the share of your web
                      browsing occupied by each website.
  -w W                Specify the web browser to analyze. Present options
                      include Apple Safari, Mozilla Firefox, and Vivaldi.
  -t T                The minimum threshold of visits a website must have to
                      be included in the final graph. Use this - as you like -
                      to reduce the number of results; it makes graphs cleaner
                      and more legible.
  -f OUTPUT_FILE      If supplied, the graph will be saved as an image to the
                      provided filename.
  -u USER_PROFILE     For Mozilla Firefox- or Google Chrome-based browsers,
                      this argument specifies the profile to use.
  -c USER_CATEGORY_A  The category by which to organize the x-axis. This value
                      also selects category in graphs (e.g., pie charts) where
                      only one value is used. Defaults to "counter," or the
                      number of visits to each site.
  -d USER_CATEGORY_B  This selects the category by which the y-axis is
                      organized.

### The -w option and one of -b, -v, -l, -s, or -p must be specified. If the browser is a version of Mozilla Firefox or Vivaldi, -u must be supplied to set the user profile. In Vivaldi, these are accessible by their usernames; Firefox lists them under more esoteric names in about:profiles.

### Macintosh users should note that macOS security will likely complain about full-disk access the first time you use this – HistoryLane requires that permission to access browser history data.

---

## III. Known Problems

- The graphs will frequently be very busy.
- Legends will occasionally overlap graphs or exceed the margins.
- The command-line interface is admittedly unwieldly
