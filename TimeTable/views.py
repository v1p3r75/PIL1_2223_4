from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from Auth.models import User, Level
from .models import Subject, Classroom, TimeTable
import html
from datetime import datetime
from .helpers import generate_password, send_notification, get_timetable_data, get_timetable_global, get_timetable_by_level, get_student_stat, get_timetable_user, get_teacher_info
import locale
import os
from django.conf import settings
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

def must_admin(view_func):

    def wrapper(request, *args, **kwargs):

        if request.user.role.id != 1:

            return studentDash(request)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


# Create your views here.
@login_required
@must_admin
def adminDashboard(request):

    return render(request, 'timetable/admin/home.html')

@login_required
def studentDashboard(request):

    return render(request, 'timetable/student/home.html')


@login_required
def studentDash(request):

    total_hours = get_student_stat('week_total_hourse', request.user.level.id)
    total_students_subjects = get_student_stat('total_subjects', request.user.level.id)
    weeks_days = get_student_stat('week_days', request.user.level.id)


    return render(request, 'timetable/student/dash.html', {'total_hours': total_hours, 'total_students_subjects': total_students_subjects, 'most': weeks_days[0], 'least': weeks_days[1]})

@login_required
def teacherDash(request):

    total_hours = get_teacher_info('week_total_hourse', request.user.id)
    total_students_subjects = get_teacher_info('total_subjects', request.user.id)
    weeks_days = get_teacher_info('week_days', request.user.id)


    return render(request, 'timetable/student/dash.html', {'total_hours': total_hours, 'total_students_subjects': total_students_subjects, 'most': weeks_days[0], 'least': weeks_days[1]})

@login_required
@must_admin
def adminDash(request):

    total_students = User.objects.filter( role_id = 3).count()
    total_teachers = User.objects.filter( role_id = 2).count()
    total_subjects = Subject.objects.count()
    total_classrooms = Classroom.objects.count()
    

    students_by_levels = (
        User.objects
        .filter( role_id = 3)
        .values('level_id')
        .annotate(total=Count('id'))
        .values_list('total', flat=True)
    )

    subjects_by_levels = (
        Subject.objects
        .values('level_id')
        .annotate(total=Count('id'))
        .values_list('total', flat=True)
    )

    students_array = []
    subjects_array = []

    levels = Level.objects.all()

    if len(levels) > len(students_by_levels):

        for i in range(len(levels)):

            if i <= len(students_by_levels) - 1:
                students_array.append(i)
                subjects_array.append(i)
            else:
                students_array.append(0)
                subjects_array.append(0)

    tab = []
    for level in levels:
        tab.append(level.label)

    return render(request, 'timetable/admin/dash.html', {'total_students': total_students, 'total_teachers': total_teachers, 'total_subjects': total_subjects, 'total_classrooms': total_classrooms, 'levels_list' : tab, 'students_by_levels': students_array, 'teachers_by_levels': [total_teachers] * len(levels), 'subjects_by_levels': subjects_array})


@login_required
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
                
                user = User.objects.get(id = data.get('id'))

                if user:
                                    
                    User.objects.filter(id = data.get('id')).update(**data)

                    if 'image' in request.FILES:

                        image = request.FILES['image']
                        file_extension = '.' + image.name.split('.')[-1].lower()
                        # Définir le chemin d'accès où enregistrer l'image
                        path = request.POST.get('lastname')  + '-' + request.POST.get('id') + file_extension
                        image_path = os.path.join(settings.MEDIA_ROOT, 'images', path)
                        # Enregistrer l'image dans le dossier spécifié
                        with open(image_path, 'ab+') as file:
                            for chunk in image.chunks():
                                file.write(chunk)

                        User.objects.filter(id = data.get('id')).update(image_path = path)

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


@login_required
@must_admin
def adminTeachers(request):

    if request.method == 'POST':

        if request.POST.get('action') == 'add':

            
            data = {
                'lastname': request.POST.get('lastname'),
                'firstname': request.POST.get('firstname'),
                'phone': request.POST.get('phone'),
                'email': request.POST.get('email'),
                'password': generate_password(),
                'role_id': 2,
            }

            if User.objects.filter(email = data.get('email')).exists():
                
                return JsonResponse({'success': False, 'message': 'L\'adresse email existe déjà.'})
                
            record = User.objects.create_user(**data)

            send_notification("Votre compte a été crée", [record.email],\
                                "mail/users_added.html",\
                                {"user": str(record), "password": data.get("password"), "role": record.role.label})

            return JsonResponse({'success': True, 'message': 'Ajouter avec succès', 'data': data})
        
        
        if request.POST.get('action') == 'edit':

            
            data = {
                'id': request.POST.get('id'),
                'lastname': request.POST.get('lastname'),
                'firstname': request.POST.get('firstname'),
                'phone': request.POST.get('phone'),
                'email': request.POST.get('email'),
            }

            user = User.objects.get(id = data.get('id'))

            if user:
                
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
        tabs.append({"id": user.id, "lastname": user.lastname, "firstname": user.firstname, "email": user.email, "phone": user.phone if user.phone is not None else "", "image": user.image_path})

    return render(request, 'timetable/admin/teachers.html', {'users': html.unescape(tabs)})

@login_required
@must_admin
def adminColaborators(request):

    if request.method == 'POST':

        if request.POST.get('action') == 'add':

            
            data = {
                'lastname': request.POST.get('lastname'),
                'firstname': request.POST.get('firstname'),
                'phone': request.POST.get('phone'),
                'email': request.POST.get('email'),
                'password':  generate_password(),
                'role_id': 1,
            }

            if User.objects.filter(email = data.get('email')).exists():
                
                return JsonResponse({'success': False, 'message': 'L\'adresse email existe déjà.'})
                
            record = User.objects.create_user(**data)

            send_notification("Votre compte a été crée", [record.email],\
                                "mail/users_added.html",\
                                {"user": str(record), "password": data.get("password"), "role": record.role.label})

            return JsonResponse({'success': True, 'message': 'Ajouter avec succès', 'data': data})
        
        
        if request.POST.get('action') == 'edit':

            
            data = {
                'id': request.POST.get('id'),
                'lastname': request.POST.get('lastname'),
                'firstname': request.POST.get('firstname'),
                'phone': request.POST.get('phone'),
                'email': request.POST.get('email'),
            }

            user = User.objects.get(id = data.get('id'))

            if user:
                
                User.objects.filter(id = data.get('id')).update(**data)

                return JsonResponse({'success': True, 'message': 'Mise à jour avec succès', 'data': data})
            
            return JsonResponse({'success': False, 'message': 'L\'élément est introuvable.'})
        

        if request.POST.get('action') == 'del':

            if User.objects.get(id = request.POST.get('id')):
                                
                User.objects.filter(id = request.POST.get('id')).delete()

                return JsonResponse({'success': True, 'message': 'Supprimer avec succès'})
            
            return JsonResponse({'success': False, 'message': 'L\'élément est introuvable.'})
        


    users = User.objects.filter(role_id = 1).all()

    tabs = []

    for user in users:
        tabs.append({"id": user.id, "lastname": user.lastname, "firstname": user.firstname, "email": user.email, "phone": user.phone if user.phone is not None else "", "image": user.image_path})

    return render(request, 'timetable/admin/colaborators.html', {'users': html.unescape(tabs)})

@login_required
@must_admin
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


@login_required
@must_admin
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

@login_required
@must_admin
def adminStudents(request):

    if request.method == 'POST':
        
        user = User.objects.get(id = request.POST.get('id'))

        if user:
            if user.is_active == True:
                user.is_active = False
                user.save()
            else:
                user.is_active = True
                user.save()

            return JsonResponse({'success': True, 'message': 'Effectué avec succès'})
        
        
        return JsonResponse({'success': False, 'message': 'Une erreur s\'est produite'})


    students = User.objects.filter(role_id = 3).all()

    tabs = []

    for user in students:
        tabs.append({"id": user.id, "lastname": user.lastname, "firstname": user.firstname, "email": user.email, "phone": user.phone if user.phone is not None else "", 'level': user.level.label, 'status': 1 if user.is_active is True else 0, "image": user.image_path})


    return render(request, 'timetable/admin/students.html', {'students': tabs})

@login_required
@must_admin
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



@login_required
@must_admin
@transaction.atomic
def adminTimetables(request):


    if request.method == "POST":

        if request.POST.get('action') == 'add':

            level_ids = request.POST.getlist('level_id')
            classroom_ids = request.POST.getlist('classroom_id')
            subject_ids = request.POST.getlist('subject_id')
            user_ids = request.POST.getlist('user_id')
            start_times = request.POST.getlist('start_time')
            end_times = request.POST.getlist('end_time')


            with transaction.atomic():

                subjects = []

                for i in range(len(user_ids)):

                    start = datetime.strptime(start_times[i], "%Y-%m-%dT%H:%M")
                    end = datetime.strptime(end_times[i], "%Y-%m-%dT%H:%M")
                    week_number = start.isocalendar()[1]

                    try:

                        if end > start:

                            is_exist = TimeTable.objects.filter(start_time = start, end_time = end)
                            classroom = Classroom.objects.get(id = classroom_ids[i])

                            if is_exist:

                                return JsonResponse({"success": False, "message": f"Un emploi du temps est déjà programmé de {start} à {end}."})
                            
                            if not classroom.status:

                                return JsonResponse({"success": False, "message": f"La salle de classe {classroom.label} n'est pas disponible pour le moment."})

                        
                            TimeTable.objects.create(
                                level_id = level_ids[i],
                                classroom_id = classroom_ids[i],
                                subject_id = subject_ids[i],
                                user_id = user_ids[i],
                                start_time = datetime.strftime(start, "%Y-%m-%d %H:%M"),
                                end_time = datetime.strftime(end, "%Y-%m-%d %H:%M"),
                                week = week_number
                            )
                            subject = Subject.objects.get(id = subject_ids[i]).label
                            if subject not in subjects:
                                subjects.append(subject)
                        else:

                            return JsonResponse({"success": False, "message": f"{start} à {end} n'est pas correcte. Veillez le corriger et réessayer."})
                        

                    except Exception as e:
                        
                        return JsonResponse({"success" : False, "message": "Erreur lors de l'enrégistrement", 'd': str(e)})

                users = User.objects.filter(Q(level_id = level_ids[i]) | Q(id = user_ids[i]))
                list_users = []
                for user in users:
                    list_users.append(user.email)

                send_notification("Nouvel d\'emploi du temps",\
                                  list_users,\
                                "mail/timetable_added.html",\
                                {"subjects": subjects})
                
                return JsonResponse({"success" : True, "message": "Ajouté avec succès"})

        if request.POST.get('action') == 'edit':
            
            ids = request.POST.getlist('id')
            level_ids = request.POST.getlist('level_id')
            classroom_ids = request.POST.getlist('classroom_id')
            subject_ids = request.POST.getlist('subject_id')
            user_ids = request.POST.getlist('user_id')
            start_times = request.POST.getlist('start_time')
            end_times = request.POST.getlist('end_time')

            with transaction.atomic():
                
                subjects = []

                for i in range(len(user_ids)):

                    start = datetime.strptime(start_times[i], "%Y-%m-%dT%H:%M")
                    end = datetime.strptime(end_times[i], "%Y-%m-%dT%H:%M")
                    week_number = start.isocalendar()[1]

                    try:

                        if end > start:

                            classroom = Classroom.objects.get(id = classroom_ids[i])
          
                            if not classroom.status:

                                return JsonResponse({"success": False, "message": f"La salle de classe {classroom.label} n'est pas disponible pour le moment."})


                            try:

                                timetable = TimeTable.objects.filter(id = ids[i])

                                timetable.update(
                                    level_id = level_ids[i],
                                    classroom_id = classroom_ids[i],
                                    subject_id = subject_ids[i],
                                    user_id = user_ids[i],
                                    start_time = datetime.strftime(start, "%Y-%m-%d %H:%M"),
                                    end_time = datetime.strftime(end, "%Y-%m-%d %H:%M"),
                                    week = week_number
                                )

                            except IndexError:

                                TimeTable.objects.create(
                                    level_id = level_ids[i],
                                    classroom_id = classroom_ids[i],
                                    subject_id = subject_ids[i],
                                    user_id = user_ids[i],
                                    start_time = datetime.strftime(start, "%Y-%m-%d %H:%M"),
                                    end_time = datetime.strftime(end, "%Y-%m-%d %H:%M"),
                                    week = week_number
                                )

                            subject = Subject.objects.get(id = subject_ids[i]).label
                            if subject not in subjects:
                                subjects.append(subject)
                        else:

                            return JsonResponse({"success": False, "message": f"{start} à {end} n'est pas correcte. Veillez le corriger et réessayer."})


                    except Exception as e:
                        
                        return JsonResponse({"success" : False, "message": "Erreur lors de la mise à jour", 'd': str(e)})

                users = User.objects.filter(Q(level_id = level_ids[i]) | Q(id = user_ids[i]))
                list_users = []
                for user in users:
                    list_users.append(user.email)

                send_notification("Modification d\'emploi du temps",\
                                  list_users,\
                                "mail/timetable_updated.html",\
                                {"subjects": subjects})
                
                return JsonResponse({"success" : True, "message": "Mise à jour avec succès"})

        if request.POST.get('action') == 'del':
                                
            if TimeTable.objects\
                .filter(week = request.POST.get('id'), level_id = request.POST.get('level_id'))\
                .delete():

                return JsonResponse({'success': True, 'message': 'Supprimer avec succès'})
            
            return JsonResponse({'success': False, 'message': 'Une erreur s\'est produite.'})
        
        if request.POST.get('action') == 'del-item':
            try:

                timetable = TimeTable.objects.filter(id = request.POST.get('id')).delete()
                return JsonResponse({"success" : True, "message": "Supprimer avec succès"})


            except Exception as e:
                        
                return JsonResponse({"success" : False, "message": "Erreur lors de la suppression", 'd': str(e)})

    subjects = Subject.objects.all()
    levels = Level.objects.all()
    timetables = get_timetable_by_level()
    classrooms = Classroom.objects.all()
    users = User.objects.filter(role_id = 2).all()
    
    
    return render(request, 'timetable/admin/timetables.html', {'subjects': subjects,'levels': levels, 'classrooms': classrooms, 'teachers': users, 'timetables': timetables})


@login_required
def userTimetable(request):

    current_timetable = get_timetable_data(request.user.level_id, True)
    others_timetable = get_timetable_global()

    return render(request, 'timetable/student/timetables.html', {'timetables' : current_timetable, 'others_timetables': others_timetable, 'current_week': True})

@login_required
def teacherTimetable(request):

    current_timetable = get_timetable_user(request.user.id, True)
    others_timetable = get_timetable_global()

    return render(request, 'timetable/student/timetables.html', {'timetables' : current_timetable, 'others_timetables': others_timetable, 'current_week': True})

@login_required
def teacherWeek(request, week):

    current_timetable = get_timetable_user(request.user.id, False, week)
    others_timetable = get_timetable_global()

    return render(request, 'timetable/student/timetables.html', {'timetables' : current_timetable, 'others_timetables': others_timetable, 'current_week': True})


@login_required
@must_admin
def adminViewTimetable(request, level, week):

    current_timetable = get_timetable_data(level, False, week)
    others_timetable = get_timetable_global()

    return render(request, 'timetable/student/timetables.html', {'timetables' : current_timetable, 'others_timetables': others_timetable, 'current_week': True})

@login_required
def timeTableWeek(request, week):

    week_timetable = get_timetable_data(request.user.level_id, False, week = week)
    others_timetable = get_timetable_global()

    return render(request, 'timetable/student/timetables.html', {'timetables' : week_timetable, 'others_timetables': others_timetable})

@login_required
def faq(request):

    return render(request, 'timetable/student/faq.html')