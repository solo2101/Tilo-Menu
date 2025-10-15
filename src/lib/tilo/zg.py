#!/usr/bin/env python3
# Zeitgeist helpers for Tilo-Menu (Python 3)

from datetime import datetime
import sys

try:
    from zeitgeist import client, datamodel
    try:
        _iface = client.ZeitgeistDBusInterface()
    except Exception:
        print("Error: Could not connect to Zeitgeist.")
        _iface = None
except Exception:
    _iface = None
    datamodel = None  # type: ignore


def _get(name: str, maxres: int, result_type):
    if _iface is None or datamodel is None:
        return []
    try:
        # last 14 days
        time_range = datamodel.TimeRange.from_seconds_ago(14 * 24 * 3600)

        tmpl = datamodel.Event()
        tmpl.set_actor(f"application://{name}")

        results = _iface.FindEvents(
            time_range,                # (min_ts, max_ts) in ms
            [tmpl],
            datamodel.StorageState.Any,
            maxres,
            result_type,
        )
        return [datamodel.Event(r) for r in results]
    except Exception:
        return []


def get_recent_for_app(name: str, maxres: int = 10):
    if datamodel is None:
        return []
    return _get(name, maxres, datamodel.ResultType.MostRecentSubjects)


def get_most_used_for_app(name: str, maxres: int = 10):
    if datamodel is None:
        return []
    return _get(name, maxres, datamodel.ResultType.MostPopularSubjects)


if __name__ == "__main__":
    app = sys.argv[1] if len(sys.argv) > 1 else "pluma.desktop"
    events = get_recent_for_app(app, 10)
    print(f"Testing with {app}")
    for ev in events:
        try:
            ts = int(ev.timestamp) // 1000  # Zeitgeist uses msec
            print(datetime.fromtimestamp(ts).strftime("%Y-%m-%d"))
            for subj in ev.get_subjects():
                text = getattr(subj, "text", "")
                uri = getattr(subj, "uri", "")
                print(f" - {text} : {uri}")
        except Exception:
            continue
