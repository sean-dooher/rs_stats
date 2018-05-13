from datetime import timedelta, datetime, date
from multiprocessing import Pool, cpu_count
from bs4 import BeautifulSoup
import argparse
import requests
import csv
import os

one_day = timedelta(days=1)


def get_url(name, date):
    return f"http://runetrack.com/history.php?user={name}" +\
        f"&m1={date.month}&d1={date.day}&y1={date.year}" +\
        f"&m2={date.month}&d2={date.day}&y2={date.year}"


def get_stats_from_day(name, date):
    print(date)
    try:
        response = requests.get(get_url(name, date))

        parsed = BeautifulSoup(response.content, 'html.parser')

        rows = parsed.findAll("tr", {'bgcolor':'#E0E0E0'}) + parsed.findAll("tr", {'bgcolor':'#C0C0C0'})

        def get_num(td):
            if td.text == '?':
                return None
            return int(td.text.replace(",", ""))

        skills = {}

        for row in rows:
            img = row.find("img")
            tds = row.findAll("td")
            skills[img.attrs['title']] = {'rank': get_num(tds[5]), 'level': get_num(tds[6]), 'xp': get_num(tds[7])}
    except:
        skills = []
    return date, skills


def add_stats_to_skills(skills, date, stats):
    for stat in stats:
        skills[stat] = skills.get(stat, {})
        skills[stat][date.isoformat()] = stats[stat]


def write_skill_to_csv(skill, data):
    with open(os.path.join('stat_history', f'{skill}.csv'), 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['date', 'rank', 'level', 'xp'])
        for date in data:
            writer.writerow([date, data[date]['rank'], data[date]['level'], data[date]['xp']])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("name", type=str,
                        help="Display name on RuneTrack")
    parser.add_argument("start", type=date, help="Start date")
    parser.add_argument("end", type=date,
                        default=datetime.now().date(), help="Start date")
    args = parser.parse_args()

    current = args.start
    end = args.end
    days = []

    while current != end:
        days.append(current)
        current_day = current + one_day

    os.makedirs("stat_history", exist_ok=True)
    with Pool(processes=cpu_count()) as pool:
        args = [(args.name, day) for day in days]
        results = pool.starmap(get_stats_from_day, args)

    skills = {}

    for date, stats in results:
        add_stats_to_skills(skills, date, stats)

    for skill in skills:
        write_skill_to_csv(skill, skills[skill])
