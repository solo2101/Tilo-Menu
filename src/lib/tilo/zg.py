#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
# This code is based on a python snipet by Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com> GPL
# Modified by Whise aka Helder Fraga 2010 <helderfraga@gmail.com>

# Find recently used items from Zeitgeist (synchronously)
# Part of the GnoMenu

from datetime import date
try:
    from zeitgeist import client, datamodel
    try:
        iface = client.ZeitgeistDBusInterface()
    except RuntimeError:
        print "Error: Could not connect to Zeitgeist."
        iface = None
except:
    iface = None



def _get(name,maxres, result_type):
    min_days_ago = 14
    time_range = datamodel.TimeRange.from_seconds_ago(min_days_ago * 3600 * 24)
    max_amount_results = maxres

    event_template = datamodel.Event()
    event_template.set_actor('application://%s'%name)

    results = iface.FindEvents(
        time_range, # (min_timestamp, max_timestamp) in milliseconds
        [event_template, ],
        datamodel.StorageState.Any,
        max_amount_results,
        result_type
    )

    # Pythonize the result
    results = [datamodel.Event(result) for result in results]
    return results

def get_recent_for_app(name,maxres):
    if iface == None:
        return []
    return _get(name,maxres, datamodel.ResultType.MostRecentSubjects)

def get_most_used_for_app(name,maxres):
    if iface == None:
        return []
    return _get(name,maxres, datamodel.ResultType.MostPopularSubjects)


if __name__ == "__main__":
    print "Testing with pluma.desktop"
    results = get_recent_for_app("pluma.desktop")
    for event in results:
        timestamp = int(event.timestamp) / 1000 # Zeitgeist timestamps are in msec
        print date.fromtimestamp(timestamp).strftime("%d %B %Y")
        for subject in event.get_subjects():
            print " -", subject.text, ":", subject.uri

