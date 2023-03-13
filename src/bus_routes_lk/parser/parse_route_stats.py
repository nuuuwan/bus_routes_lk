import camelot
from utils import CSVFile, File, Log, Directory
import os

ROUTE_STATS_PATH_BASE = 'data/ntc-report-2022'
ROUTE_STATS_PDF_PATH = f'{ROUTE_STATS_PATH_BASE}.pdf'
ROUTE_STATS_CSV_PATH = f'{ROUTE_STATS_PATH_BASE}-all.csv'

PDF_TABLE_PAGES = '199-215'

log = Log('parse_route_stats')


def parse_int(x):
    try:
        return int(x)
    except ValueError:
        return 0


def parse_float(x):
    try:
        return float(x)
    except ValueError:
        return 0.0


def parse_str(x):
    return x.strip()


def parse_csv(csv_path):
    lines = File(csv_path).read_lines()
    n = len(lines)
    i = 5
    d_list = []
    while i < n:
        line = lines[i]
        if line.startswith('"') and not line.startswith('"Route No') and not line.startswith('"NormaL Bus Total'
        ):
            row_num = parse_int(line[1:])
            route_id = parse_str(lines[i + 1])
            location_start, location_end = lines[i + 2].split('-')[:2]
            location_start = parse_str(location_start).title()
            location_end = parse_str(location_end).title()

            route_grade = parse_str(lines[i + 3])
            distance_km = parse_float(lines[i + 6])
            daily_km = parse_float(lines[i + 7])

            d = dict(
                row_num=row_num,
                route_id=route_id,
                location_start=location_start,
                location_end=location_end,
                route_grade=route_grade,
                distance_km=distance_km,
                daily_km=daily_km,
            )
            d_list.append(d)
            i += 5
        i += 1
    log.debug(f'Parsed {len(d_list)} routes from {csv_path}.')

    return d_list


def parse():
    log.debug(f'Parsing {ROUTE_STATS_PDF_PATH}...')
    tables = camelot.read_pdf(ROUTE_STATS_PDF_PATH, pages=PDF_TABLE_PAGES)
    csv_path_list = []
    for i_table, table in enumerate(tables):
        csv_path = f'{ROUTE_STATS_PATH_BASE}-{i_table}.csv'
        table.to_csv(csv_path)
        log.info(f'Saved {csv_path}')
        csv_path_list.append(csv_path)
    return csv_path_list

def combine_rows(all_d_list):
    idx = {}
    for d in all_d_list:
        id = d['route_id'] + d['location_start'] + d['location_end']
        if id not in idx:
            idx[id] = []
        idx[id].append(d)

    new_all_d_list = []
    for d_list in idx.values():
        first_d = d_list[0]
        d = first_d | dict(
            distance_km=max([d2['distance_km'] for d2 in d_list]),
            daily_km=sum([d2['daily_km'] for d2 in d_list]),
        )
        new_all_d_list.append(d)
    return new_all_d_list


def combine():
    if os.path.exists(ROUTE_STATS_CSV_PATH):
      os.remove(ROUTE_STATS_CSV_PATH)
    all_d_list = []
    n_files = 0
    for child in Directory('data').children:
        if child.name.endswith('.csv'):
            d_list = parse_csv(child.path)
            all_d_list.extend(d_list)
            n_files += 1

    all_d_list = combine_rows(all_d_list)

    CSVFile(ROUTE_STATS_CSV_PATH).write(all_d_list)
    log.info(f'Combined {n_files} files into {ROUTE_STATS_CSV_PATH}.')


if __name__ == '__main__':
    combine()
