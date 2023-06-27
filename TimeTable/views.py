from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from Auth.models import User, Level
from .models import Subject, Classroom, TimeTable
import html
from datetime import datetime,  timedelta
from itertools import groupby
from .helpers import get_timetable_data
import locale


locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')


# Create your views here.
@login_required( login_url = 'login')
def adminDashboard(request):

    return render(request, 'timetable/admin/home.html')


@login_required( login_url = 'login')
def adminDash(request):

    total_students = User.objects.filter( role_id = 3).count()
    total_teachers = User.objects.filter( role_id = 2).count()
    total_subjects = Subject.objects.count()
    total_classrooms = Classroom.objects.count()

    # students_by_levels = User.objects.filter( role_id = 3)
    students_by_levels = (
        User.objects
        .filter( role_id = 3)
        .values('level_id')
        .annotate(total=Count('id'))
        .values_list('total', flat=True)
    )
    # students_b = []

    levels = Level.objects.all()

    # if len(levels) > len(list(students_by_levels)):

    #     for i in range(len(levels)):

    #         if i < len(list(students_by_levels)):

    #             students_b.append(students_by_levels[i])

    #         students_b.append(0)

    tab = []
    for level in levels:
        tab.append(level.label)

    return render(request, 'timetable/admin/dash.html', {'total_students': total_students, 'total_teachers': total_teachers, 'total_subjects': total_subjects, 'total_classrooms': total_classrooms, 'levels_list' : tab, 'students_by_levels': list(students_by_levels)})


@login_required( login_url = 'login')
def userAccount(request):

    if request.method == 'POST':

        if request.POST.get('action') == 'edit':

            if request.POST.get('action-detail') == 'info':

                data = {
                    'id': request.POST.get('id'),
                    'lastname': request.POST.get('lastname'),
                    'firstname': request.POST.get('firstname'),
                    'phone': request.POST.get('phone'),
                    'email': request.POST.get('email'),
                    'level_id': request.POST.get('level_id'),
                }
                
                if User.objects.get(id = data.get('id')):
                                    
                    User.objects.filter(id = data.get('id')).update(**data)

                    return JsonResponse({'success': True, 'message': 'Mise à jour avec succès', 'data': data})
                
                return JsonResponse({'success': False, 'message': 'L\'élément est introuvable.'})

            if request.POST.get('action-detail') == 'password':

                data = {
                    'id': request.POST.get('id'),
                    'new_password': request.POST.get('new_password'),
                    'password': request.POST.get('password'),
                    'password_confirmation': request.POST.get('password_confirmation'),
                }
                
                if (data.get('new_password') != data.get('password_confirmation')):
                    
                    return JsonResponse({'success': False, 'message': 'Confirmation de mot passe échoué.'})

                user = User.objects.get(id = data.get('id'))

                if user:
                        if user.check_password(data.get('password')):

                            user.set_password(data.get('new_password'))
                            user.save()
                            return JsonResponse({'success': True, 'message': 'Mise à jour avec succès', 'data': data})

                        return JsonResponse({'success': False, 'message': 'Mot de passe incorrect.'})
                
                return JsonResponse({'success': False, 'message': 'L\'élément est introuvable.'})



        if request.POST.get('action') == 'del':

            if User.objects.get(id = request.POST.get('id')):
                                
                User.objects.filter(id = request.POST.get('id')).delete()

                return JsonResponse({'success': True, 'message': 'Supprimer avec succès'})
            
            return JsonResponse({'success': False, 'message': 'L\'élément est introuvable.'})
        

    levels = Level.objects.all()

    tabs = []

    for level in levels:
        tabs.append({"id": level.id, "level": level.label})

    return render(request, 'timetable/account.html', {'levels': levels})


@login_required( login_url = 'login')
def adminTeachers(request):

    if request.method == 'POST':

        if request.POST.get('action') == 'add':

            
            data = {
                'lastname': request.POST.get('lastname'),
                'firstname': request.POST.get('firstname'),
                'phone': request.POST.get('phone'),
                'email': request.POST.get('email'),
                'password': request.POST.get('password'),
                'role_id': 2,
            }

            if User.objects.filter(email = data.get('email')).exists():
                
                return JsonResponse({'success': False, 'message': 'L\'adresse email existe déjà.'})
                
            record = User.objects.create_user(**data)

            return JsonResponse({'success': True, 'message': 'Ajouter avec succès', 'data': data})
        
        
        if request.POST.get('action') == 'edit':

            
            data = {
                'id': request.POST.get('id'),
                'lastname': request.POST.get('lastname'),
                'firstname': request.POST.get('firstname'),
                'phone': request.POST.get('phone'),
                'email': request.POST.get('email'),
            }

            if User.objects.get(id = data.get('id')):
                                
                User.objects.filter(id = data.get('id')).update(**data)

                return JsonResponse({'success': True, 'message': 'Mise à jour avec succès', 'data': data})
            
            return JsonResponse({'success': False, 'message': 'L\'élément est introuvable.'})
        

        if request.POST.get('action') == 'del':

            if User.objects.get(id = request.POST.get('id')):
                                
                User.objects.filter(id = request.POST.get('id')).delete()

                return JsonResponse({'success': True, 'message': 'Supprimer avec succès'})
            
            return JsonResponse({'success': False, 'message': 'L\'élément est introuvable.'})
        


    users = User.objects.filter(role_id = 2).all()

    tabs = []

    for user in users:
        tabs.append({"id": user.id, "lastname": user.lastname, "firstname": user.firstname, "email": user.email, "phone": user.phone, "password": user.password})

    return render(request, 'timetable/admin/teachers.html', {'users': html.unescape(tabs)})


@login_required( login_url = 'login')
def adminSubjects(request):

    if request.method == 'POST':

        if request.POST.get('action') == 'add':

            
            data = {
                'label': request.POST.get('label'),
                'code': request.POST.get('code'),
                'total_time': request.POST.get('total_time'),
                'level_id': request.POST.get('level_id'),
            }
                
            Subject.objects.create(**data)

            return JsonResponse({'success': True, 'message': 'Ajouter avec succès', 'data': data})
        
        
        if request.POST.get('action') == 'edit':

            
            data = {
                'id': request.POST.get('id'),
                'label': request.POST.get('label'),
                'code': request.POST.get('code'),
                'total_time': request.POST.get('total_time'),
                'level_id': request.POST.get('level_id'),
            }

            if Subject.objects.get(id = data.get('id')):
                                
                Subject.objects.filter(id = data.get('id')).update(**data)

                return JsonResponse({'success': True, 'message': 'Mise à jour avec succès', 'data': data})
            
            return JsonResponse({'success': False, 'message': 'L\'élément est introuvable.'})
        

        if request.POST.get('action') == 'del':

            if Subject.objects.get(id = request.POST.get('id')):
                                
                Subject.objects.filter(id = request.POST.get('id')).delete()

                return JsonResponse({'success': True, 'message': 'Supprimer avec succès'})
            
            return JsonResponse({'success': False, 'message': 'L\'élément est introuvable.'})
        


    subjects = Subject.objects.all()
    levels = Level.objects.all()

    tab1 = []
    tab2 = []

    for subject in subjects:
        tab1.append({"id": subject.id, "label": subject.label, "code": subject.code, "level_id": subject.level.id, "level": subject.level.label, "total_time": subject.total_time})

    for level in levels:
        tab2.append({"id": level.id, "label": level.label, "description": level.description})


    return render(request, 'timetable/admin/subjects.html', {'subjects': html.unescape(tab1), 'levels': html.unescape(tab2)})


@login_required( login_url = 'login')
def adminLevels(request):

    if request.method == 'POST':

        if request.POST.get('action') == 'add':

            
            data = {
                'label': request.POST.get('label'),
                'description': request.POST.get('description'),
            }
                
            Level.objects.create(**data)

            return JsonResponse({'success': True, 'message': 'Ajouter avec succès', 'data': data})
        
        
        if request.POST.get('action') == 'edit':

            
            data = {
                'id': request.POST.get('id'),
                'label': request.POST.get('label'),
                'description': request.POST.get('description'),
            }

            if Level.objects.get(id = data.get('id')):
                                
                Level.objects.filter(id = data.get('id')).update(**data)

                return JsonResponse({'success': True, 'message': 'Mise à jour avec succès', 'data': data})
            
            return JsonResponse({'success': False, 'message': 'L\'élément est introuvable.'})
        

        if request.POST.get('action') == 'del':

            if Level.objects.get(id = request.POST.get('id')):
                                
                Level.objects.filter(id = request.POST.get('id')).delete()

                return JsonResponse({'success': True, 'message': 'Supprimer avec succès'})
            
            return JsonResponse({'success': False, 'message': 'L\'élément est introuvable.'})
        


    levels = Level.objects.all()

    tab = []

    for level in levels:
        tab.append({"id": level.id, "label": level.label, "description": '' if level.description is None else level.description})


    return render(request, 'timetable/admin/levels.html', {'levels': html.unescape(tab)})


@login_required( login_url = 'login')
def adminClassrooms(request):

    if request.method == 'POST':

        if request.POST.get('action') == 'add':

            
            data = {
                'label': request.POST.get('label'),
                'capacity': request.POST.get('capacity'),
                'status': True if request.POST.get('status') == 'on' else False,
                'description': request.POST.get('description'),
            }
                
            Classroom.objects.create(**data)

            return JsonResponse({'success': True, 'message': 'Ajouter avec succès', 'data': data})
        
        
        if request.POST.get('action') == 'edit':

            
            data = {
                'id': request.POST.get('id'),
                'label': request.POST.get('label'),
                'capacity': request.POST.get('capacity'),
                'status': True if request.POST.get('status') == 'on' else False,
                'description': request.POST.get('description'),
            }

            if Classroom.objects.get(id = data.get('id')):
                                
                Classroom.objects.filter(id = data.get('id')).update(**data)

                return JsonResponse({'success': True, 'message': 'Mise à jour avec succès', 'data': data})
            
            return JsonResponse({'success': False, 'message': 'L\'élément est introuvable.'})
        

        if request.POST.get('action') == 'del':

            if Classroom.objects.get(id = request.POST.get('id')):
                                
                Classroom.objects.filter(id = request.POST.get('id')).delete()

                return JsonResponse({'success': True, 'message': 'Supprimer avec succès'})
            
            return JsonResponse({'success': False, 'message': 'L\'élément est introuvable.'})
        


    classrooms = Classroom.objects.all()

    tab = []

    for classroom in classrooms:
        tab.append({"id": classroom.id, "label": classroom.label, "status": "off" if classroom.status is False else "on", "capacity": classroom.capacity, "description": '' if classroom.description is None else classroom.description})


    return render(request, 'timetable/admin/classrooms.html', {'classrooms': html.unescape(tab)})



@login_required( login_url = 'login')
@transaction.atomic
def adminTimetables(request):


    if request.method == "POST":

        data = []

        level_ids = request.POST.getlist('level_id')
        classroom_ids = request.POST.getlist('classroom_id')
        subject_ids = request.POST.getlist('subject_id')
        user_ids = request.POST.getlist('user_id')
        start_times = request.POST.getlist('start_time')
        end_times = request.POST.getlist('end_time')


        with transaction.atomic():

            for i in range(len(user_ids)):

                start = datetime.strptime(start_times[i], "%Y-%m-%dT%H:%M")
                end = datetime.strptime(end_times[i], "%Y-%m-%dT%H:%M")
                week_number = start.isocalendar()[1]

                try:

                    TimeTable.objects.create(
                        level_id = level_ids[i],
                        classroom_id = classroom_ids[i],
                        subject_id = subject_ids[i],
                        user_id = user_ids[i],
                        start_time = datetime.strftime(start, "%Y-%m-%d %H:%M"),
                        end_time = datetime.strftime(end, "%Y-%m-%d %H:%M"),
                        week = week_number
                    )

                except Exception as e:
                    
                    return JsonResponse({"success" : False, "message": "Erreur lors de l'enrégistrement", 'd': str(e)})

            return JsonResponse({"success" : True, "message": "Ajouté avec succès"})

    subjects = Subject.objects.all()
    levels = Level.objects.all()
    timetables = get_timetable_data()
    classrooms = Classroom.objects.all()
    users = User.objects.filter(role_id = 2).all()
    
    
    return render(request, 'timetable/admin/timetables.html', {'subjects': subjects,'levels': levels, 'classrooms': classrooms, 'teachers': users, 'timetables': timetables})


@login_required( login_url = 'login')
def userTimetable(request):

    current_timetable = get_timetable_data(request.user.level_id, True)
    others_timetable = get_timetable_data(request.user.level_id, False)

    return render(request, 'timetable/student/timetables.html', {'timetables' : current_timetable, 'others_timetables': others_timetable})