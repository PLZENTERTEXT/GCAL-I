from __future__ import print_function
import datetime
import pickle
import json
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from colorama import init, Fore, Style
import re
import shutil

init(autoreset=True)  # Auto reset colors after each print

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
DEFAULT_TASK = "Work"

HEX_TO_COLOR = {
    '#a4bdfc': 'Lavender',
    '#7ae7bf': 'Sage',
    '#dbadff': 'Grape',
    '#ff887c': 'Flamingo',
    '#fbd75b': 'Banana',
    '#ffb878': 'Tangerine',
    '#46d6db': 'Peacock',
    '#e1e1e1': 'Graphite',
    '#5484ed': 'Blueberry',
    '#51b749': 'Basil',
    '#dc2127': 'Tomato'
}

terminal_width = shutil.get_terminal_size().columns

def colored_input(prompt):
    return input(Fore.CYAN + prompt + Style.RESET_ALL)

def print_ascii_art():
    # ANSI escape codes
    BLUE = "\033[94m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    WHITE = "\033[97m"
    RESET = "\033[0m"

    G = [
        "  _____ ",
        " / ____|",
        "| |  __ ",
        "| | |_ |",
        "| |__| |",
        " \\_____|"
    ]

    C1 = [
        "   _____ ",
        "  / ____|",
        " | |     ",
        " | |     ",
        " | |____ ",
        "  \\_____|"
    ]

    A = [
        "          ",
        "     /\\   ",
        "    /  \\  ",
        "   / /\\ \\ ",
        "  / ____ \\",
        " /_/    \\_\\"
    ]

    L = [
        "  _      ",
        " | |     ",
        " | |     ",
        " | |     ",
        " | |____ ",
        "|______|"
    ]

    DASH = [
        "         ",
        "         ",
        "  ______ ",
        " |______|",
        "         ",
        "         "
    ]

    I = [       
        "  _____ ",
        " |_   _|",
        "   | |  ",
        "   | |  ",  
        "  _| |_ ",
        " |_____|",
    ]


    # Combine lines with colors
    for i in range(6):
        line = (
            BLUE + G[i] + RESET + "  " +
            RED + C1[i] + RESET + "  " +
            YELLOW + A[i] + RESET + "  " +
            BLUE + L[i] + RESET + "  " +
            WHITE + DASH[i] + RESET + "  " +
            GREEN + I[i] + RESET
        )
        print(line)

def parse_period_or_range():
    """
    Prompts user to input either:
    - A period in YYYY-MM format (e.g. 2024-09), or
    - A date range as YYYY-MM-DD for start and end date
    Returns start_date, end_date (both datetime with tzinfo)
    """
    while True:
        user_input = colored_input(
            "Enter period (YYYY-MM) OR date range start (YYYY-MM-DD): ").strip()
        # If input matches YYYY-MM format (period)
        if re.match(r"^\d{4}-\d{2}$", user_input):
            year, month = map(int, user_input.split('-'))
            # Creates a datetime object for the first day of the month
            start_date = datetime.datetime(year, month, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=+8)))
            # Get last day of month
            if month == 12: # December 24 -> January 25
                # Creates a datetime object for January 1st of the next year, then subtracts one day → December 31st
                end_date = datetime.datetime(year + 1, 1, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=+8))) - datetime.timedelta(days=1)
            else:
                end_date = datetime.datetime(year, month + 1, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=+8))) - datetime.timedelta(days=1)
            return start_date, end_date
        # Else, try to parse date range input
        else:
            try:
                start_date = datetime.datetime.strptime(user_input, '%Y-%m-%d').replace(
                    tzinfo=datetime.timezone(datetime.timedelta(hours=+8)))
                end_date_str = colored_input('Please enter end date (YYYY-MM-DD): ').strip()
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').replace(
                    tzinfo=datetime.timezone(datetime.timedelta(hours=+8)))
                if end_date < start_date:
                    print(Fore.RED + "End date cannot be before start date. Try again." + Style.RESET_ALL)
                    continue
                return start_date, end_date
            except Exception:
                print(Fore.RED + "Invalid input format. Please try again." + Style.RESET_ALL)


def get_inputs():
    print(Fore.WHITE + "\n" + "="*terminal_width + "\n")
    print(Fore.GREEN + 'This program calculates how much time you have spent on a task in Google Calendar, sorted by color.\n' + Style.RESET_ALL)
    print(Fore.WHITE + "="*terminal_width + "\n")
    # Get color to task mapping
    if os.path.exists('tasks.json'):
        print(Fore.YELLOW + '[*] Using existing task mapping at \'tasks.json\'.' + Style.RESET_ALL)
        with open('tasks.json', 'r') as file:
            color_to_task = json.load(file)
    else:
        color_to_task = {}
        print(Fore.YELLOW + 'You do not have a task mapping yet.' + Style.RESET_ALL)
        for hex, color in HEX_TO_COLOR.items():
            task = colored_input(f'Enter task corresponding to \'{color}\': ')
            color_to_task[color] = task
        with open('tasks.json', 'w') as file:
            json.dump(color_to_task, file)

    start_date, end_date = parse_period_or_range()
    t_range = end_date - start_date + datetime.timedelta(days=1) 
    # + datetime.timedelta(days=1):
    # Adds 1 day to include the end_date itself in the range

    return start_date, end_date, t_range, color_to_task


def get_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service


def get_events(startdate, enddate, service):
    tmin = startdate.isoformat()
    # We add 1 day to enddate to include full last day in API query
    tmax = (enddate + datetime.timedelta(days=1)).isoformat()
    event_results = service.events().list(calendarId='primary', timeMax=tmax, timeMin=tmin,
                                          singleEvents=True, orderBy='startTime').execute()
    return event_results.get('items', [])


def map_colorId_to_task(service, color_to_task):
    colorId_to_hex = {}
    colorId_to_task = {}
    colors = service.colors().get().execute()
    for id, color in colors['event'].items():
        colorId_to_hex[id] = color['background']
    for id, hex in colorId_to_hex.items():
        # Default to "Work" if color hex not in mapping
        task_name = color_to_task.get(HEX_TO_COLOR.get(hex, ""), DEFAULT_TASK)
        colorId_to_task[id] = task_name
    return colorId_to_task


def analyze(events, colorId_to_task, trange):
    task_to_time = {}

    for event in events:
        try:
            # Determine task name, fallback to Work
            colorId = event.get('colorId')
            task = colorId_to_task.get(colorId, DEFAULT_TASK)

            if task not in task_to_time:
                task_to_time[task] = datetime.timedelta(0)

            # Check if event has dateTime or date only (all-day event)
            start = event['start']
            end = event['end']

            if 'dateTime' in start and 'dateTime' in end:
                start_time = datetime.datetime.fromisoformat(start['dateTime'])
                end_time = datetime.datetime.fromisoformat(end['dateTime'])
                event_duration = end_time - start_time
            elif 'date' in start and 'date' in end:
                # Date-only event: count as full 24h * number of days
                start_date = datetime.datetime.fromisoformat(start['date']).replace(tzinfo=datetime.timezone(datetime.timedelta(hours=+8)))
                end_date = datetime.datetime.fromisoformat(end['date']).replace(tzinfo=datetime.timezone(datetime.timedelta(hours=+8)))
                # Google Calendar all-day end date is exclusive, so subtract 1 day
                day_count = (end_date - start_date).days
                event_duration = datetime.timedelta(days=day_count)
            else:
                # Unexpected format, ignore event duration
                print(Fore.RED + f"Warning: event '{event.get('summary','Unknown')}' has unsupported time format." + Style.RESET_ALL)
                event_duration = datetime.timedelta(0)

            task_to_time[task] += event_duration

        except Exception as e:
            print(Fore.RED + f"Error processing event: {event.get('summary', 'Unknown')} - {e}" + Style.RESET_ALL)

    # Calculate averages
    total_days = trange.days if trange.days > 0 else 1  # Avoid zero division

    result = {}
    for task, total_time in task_to_time.items():
        total_hours = total_time.total_seconds() / 3600
        result[task] = {
            'total hours': total_hours,
            'daily average': total_hours / total_days,
            'weekly average': total_hours / (total_days / 7),
            'monthly average': total_hours / (total_days / 30),
            'yearly average': total_hours / (total_days / 365),
        }
    return result


def print_results(task_to_time, start_date, end_date):
    total_days = (end_date - start_date).days + 1

    print(Fore.GREEN + '\n========== Results ==========' + Style.RESET_ALL)
    print(f'From: {Fore.YELLOW}{start_date.date()}{Style.RESET_ALL}')
    print(f'To  : {Fore.YELLOW}{end_date.date()}{Style.RESET_ALL}')
    print(f'Total days: {Fore.YELLOW}{total_days}{Style.RESET_ALL}\n')

    def print_section(title, key):
        print(Fore.CYAN + f'--------- {title} ---------' + Style.RESET_ALL)
        for task, values in task_to_time.items():
            hours = values[key]
            print(f'{task:<20} {hours:6.2f} hours')
            # Left-align the text with 20 characters of space
            # Hours total width is 6 characters, 2 digits after the decimal point

    print_section('Total hours spent', 'total hours')
    print()
    print_section('Daily average', 'daily average')
    print()
    print_section('Weekly average', 'weekly average')
    print()
    print_section('Monthly average', 'monthly average')
    print()
    print_section('Yearly average', 'yearly average')
    print()

def main():
    print_ascii_art()
    start_date, end_date, t_range, color_to_task = get_inputs()
    service = get_service()
    events = get_events(start_date, end_date, service)
    colorId_to_task = map_colorId_to_task(service, color_to_task)
    task_time_averages = analyze(events, colorId_to_task, t_range)
    print_results(task_time_averages, start_date, end_date)


if __name__ == '__main__':
    main()
