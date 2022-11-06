#!/usr/bin/env python3
# TODO publish script as utility for getting ical events
# TODO show upcoming ical event + count of remaining events on rpi epaper screen
# TODO how to do this in limited rpi pico micropython/circuitpython/rust/c?
# TODO simplify the icalevents library so it has less dependencies...
import hashlib
import json
import os
import time
import urllib.request
from argparse import ArgumentParser
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, cast

from dateutil.tz import tzlocal
from icalevents.icalparser import Event, parse_events

try:
    from progressbar import progressbar

    if hasattr(progressbar, "ProgressBar"):
        progressbar = progressbar.ProgressBar()
except:
    progressbar = lambda x: x

# 15 minute cache
DEFAULT_CACHE_AGE = 60 * 15

start_date = (2022, 10, 29)
end_date = (2022, 11, 12)


# TODO add 15 minute local http cache in case of restarts/testing
# TODO store calendar URLs in a secure location
with open("calendar_links.json") as calendar_urls_file:
    calendar_urls = json.load(calendar_urls_file)
    assert isinstance(calendar_urls, list)
    for url in calendar_urls:
        assert isinstance(url, str)


def strhash(string: str) -> str:
    return hashlib.sha1(string.encode("utf-8")).hexdigest()


def cache_file_for(string: str) -> str:
    cache_dir = os.path.join(os.path.dirname(__file__), "calendar-cache")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, strhash(string))


def get_from_cache(
    url: str, cache: bool, cache_age: float
) -> Tuple[bool, Optional[str]]:
    if os.path.exists(cache_file_for(url)):
        with open(cache_file_for(url)) as cache_file:
            try:
                cache_entry = json.load(cache_file)
            except json.JSONDecodeError:
                return False, None

            too_old = cache_entry.get("time", 0) >= time.time() + cache_age
            if cache_entry.get("cached_calendar"):
                return too_old, cache_entry.get("cached_calendar")
    return False, None


def download_calendar(
    url: str, cache: bool = False, cache_age: float = DEFAULT_CACHE_AGE
) -> Optional[str]:
    too_old = True
    calendar_string = None
    if cache:
        too_old, calendar_string = get_from_cache(url, cache, cache_age)
        if not too_old and calendar_string is not None:
            print("loading cached calendar:", calendar_string)
            return calendar_string

    try:
        calendar_string = urllib.request.urlopen(url).read().decode("utf-8")
    except Exception as exc:
        print("error downloading", exc)
        if calendar_string is not None:
            return calendar_string

    if cache:
        with open(cache_file_for(url), "w") as cache_file:
            json.dump(
                {"time": time.time(), "cached_calendar": calendar_string}, cache_file
            )

    return calendar_string


def parse_date(date: Optional[str]) -> datetime:
    if date is None:
        return datetime.now(tz=tzlocal())
    try:
        date_int = int(date)
    except ValueError:
        return datetime.fromisoformat(date)
    return datetime.fromtimestamp(date_int)


def upcoming_events_to_json(
    calendar_strings: Dict[str, Optional[str]], start_date_str: Optional[str]
) -> str:
    start_date = parse_date(start_date_str)
    end_date = start_date + timedelta(days=1)
    print(start_date, end_date)
    upcoming = (None, timedelta(seconds=60 * 60 * 24))
    for url, calendar in calendar_strings.items():
        print(url)
        if calendar is None:
            continue
        for event in parse_events(calendar, start=start_date, end=end_date):
            event = cast(Event, event)
            # TODO print more info or save to JSON
            if event.all_day:
                print(
                    "ALL DAY",
                    event.start.strftime("%Y-%m-%d"),
                    event.summary,
                    event.location,
                )
            else:
                delta = cast(timedelta, event.start - start_date)
                if (
                    delta.total_seconds() >= 0
                    and upcoming[1].total_seconds() > delta.total_seconds()
                ):
                    upcoming = (event, delta)

                print(
                    event.start,
                    "\n\t",
                    event.start - start_date,
                    "\n\t",
                    event.summary,
                    event.location,
                )
            # End early once the first upcoming event is found
            if upcoming[0] is not None:
                continue

    if upcoming[0] is None:
        obj = {"summary": "none", "delta": ""}
    else:
        event, delta = upcoming
        obj = {"summary": event.summary, "delta": str(delta)}
    return json.dumps(obj)


def main():
    argparser = ArgumentParser(
        description="Show upcoming calendar events from .ical links"
    )

    argparser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="ISO format or UNIX timestamp. Example: '2022-11-02 10:34'",
    )
    end_date_or_duration_group = argparser.add_mutually_exclusive_group()
    end_date_or_duration_group.add_argument(
        "--end-date", type=str, help="Example: TODO"
    )
    end_date_or_duration_group.add_argument(
        "--duration", type=str, help="Example: TODO"
    )

    argparser.add_argument(
        "--output-file",
        type=str,
        default="upcoming.json",
        help="",
    )

    argparser.add_argument(
        "--no-cache",
        action="store_true",
        help="Set this option to prevent saving a local copy of the calendars",
    )

    args = argparser.parse_args()

    calendar_strings = {
        url: download_calendar(url, cache=not args.no_cache)
        for url in progressbar(calendar_urls)
    }
    out_json = upcoming_events_to_json(calendar_strings, args.start_date)
    print(out_json, "to", args.output_file)
    with open(args.output_file, "w") as upcoming_file:
        upcoming_file.write(out_json)


if __name__ == "__main__":
    main()
