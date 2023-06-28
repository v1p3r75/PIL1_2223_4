from django.db.models import Q
from datetime import datetime, timedelta
from .models import TimeTable

def get_timetable_by_level():

    timetable_entries = TimeTable.objects.select_related('level', 'user', 'classroom', 'subject')

    # Créez un dictionnaire pour stocker les données groupées par filière, semaine et jour
    grouped_timetable = {}

    # Parcourez les emplois du temps et groupez les données
    for entry in timetable_entries:
        level_label = entry.level.label
        week_number = entry.start_time.isocalendar()[1]
        day_name = entry.start_time.strftime('%A')

        if level_label not in grouped_timetable:
            grouped_timetable[level_label] = {}

        if week_number not in grouped_timetable[level_label]:
            grouped_timetable[level_label][week_number] = []

        day_data = {
            'user': entry.user,
            'level': level_label,
            'classroom': entry.classroom.label,
            'subject': entry.subject.label,
            'start_time': str(entry.start_time),
            'end_time': str(entry.end_time),
        }
        grouped_timetable[level_label][week_number].append({day_name: day_data})

    # Affichez les données groupées par filière, semaine et jour
    result = []

    for level_label, level_data in grouped_timetable.items():
        level_info = {'level': level_label, 'weeks': []}
        
        for week_number, week_data in level_data.items():
            week_info = {'week': week_number, 'days': []}

            for day_data in week_data:
                day_name, day_info = list(day_data.items())[0]
                day_info['day_name'] = day_name.capitalize()
                week_info['days'].append(day_info)

            level_info['weeks'].append(week_info)

        result.append(level_info)

    return result

def get_timetable_global():


    timetable_entries = TimeTable.objects.select_related('level', 'user', 'classroom', 'subject')

    # Créez un dictionnaire pour stocker les données groupées par semaine et jour
    grouped_timetable = {}

    # Parcourez les emplois du temps et groupez les données
    for entry in timetable_entries:
        week_number = entry.start_time.isocalendar()[1]
        day_name = entry.start_time.strftime('%A')

        if week_number not in grouped_timetable:
            grouped_timetable[week_number] = []

        day_data = {day_name: {
            'user': entry.user,
            'level': entry.level.label,
            'classroom': entry.classroom.label,
            'subject': entry.subject.label,
            'start_time': str(entry.start_time),
            'end_time': str(entry.end_time),
        }}
        grouped_timetable[week_number].append(day_data)

    # Affichez les données groupées par semaine et jour
    result = []

    for week_number, week_data in grouped_timetable.items():
        week_info = {'week': week_number, 'days': []}
        
        for day_data in week_data:
            day_name, day_info = list(day_data.items())[0]
            day_info['day_name'] = day_name.capitalize()
            week_info['days'].append(day_info)

        result.append(week_info)

    return result


def get_timetable_data(level_id : int | None = None, current_week : bool = False, week = None):

    # Récupérez les emplois du temps avec les informations associées pour toutes les semaines
    if current_week:

        start_date = datetime.now().date() - timedelta(days = datetime.now().date().weekday() - 0)
        end_date = start_date + timedelta(days = 6)
        timetable_entries = TimeTable.objects\
            .filter(Q(start_time__date__gte = start_date, end_time__date__lte = end_date), level_id = level_id)\
            .select_related('level', 'user', 'classroom', 'subject')
    else:
        timetable_entries = TimeTable.objects.filter(level_id = level_id, week = week).select_related('level', 'user', 'classroom', 'subject')

    # Créez un dictionnaire pour stocker les données groupées par semaine et jour
    grouped_timetable = {}

    # Parcourez les emplois du temps et groupez les données
    for entry in timetable_entries:
        week_number = entry.start_time.isocalendar()[1]
        day_name = entry.start_time.strftime('%A')

        if week_number not in grouped_timetable:
            grouped_timetable[week_number] = []

        day_data = {day_name: {
            'user': entry.user,
            'level': entry.level.label,
            'classroom': entry.classroom.label,
            'subject': entry.subject.label,
            'start_time': str(entry.start_time),
            'end_time': str(entry.end_time),
        }}
        grouped_timetable[week_number].append(day_data)

    # Affichez les données groupées par semaine et jour
    result = []

    for week_number, week_data in grouped_timetable.items():
        week_info = {'week': week_number, 'days': []}
        
        for day_data in week_data:
            day_name, day_info = list(day_data.items())[0]
            day_info['day_name'] = day_name.capitalize()
            week_info['days'].append(day_info)

        result.append(week_info)

    return result