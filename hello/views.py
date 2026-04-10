from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail, EmailMessage, get_connection
import requests
from django.conf import settings
from django.db.models import Sum, Q
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from datetime import datetime, timedelta
import random
import re
import string
from .models import Course, Curriculum, Activity, Faculty, Section, Schedule, Room
from .forms import CourseForm, CurriculumForm
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# Helper function to check if user is admin
def is_admin(user):
    return user.is_staff and user.is_superuser

def admin_login(request):
    """Handle admin login with custom template"""
    # If user is already authenticated, redirect based on role
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        elif request.user.is_staff:
            return redirect('staff_dashboard')
        else:
            # Regular user - logout and show error
            logout(request)
            messages.error(request, 'You do not have admin privileges.')
            return render(request, 'hello/login.html')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user has staff privileges
            if user.is_staff:
                login(request, user)
                
                # Set session expiry
                if not remember_me:
                    request.session.set_expiry(0)
                
                # Redirect based on user role
                if user.is_superuser:
                    return redirect('admin_dashboard')
                else:
                    return redirect('staff_dashboard')
            else:
                messages.error(request, 'You do not have admin privileges.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'hello/login.html')

def admin_logout(request):
    """Handle admin logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('admin_login')

@login_required
def add_schedule(request):
    """Add a new schedule entry"""
    if request.method == 'POST':
        try:
            # Extract schedule data from POST
            course_id = request.POST.get('course')
            section_id = request.POST.get('section')
            faculty_id = request.POST.get('faculty')
            room_id = request.POST.get('room')
            day = request.POST.get('day')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')

            # Get related objects
            course = Course.objects.get(id=course_id)
            section = Section.objects.get(id=section_id)
            faculty = Faculty.objects.get(id=faculty_id) if faculty_id else None
            room = Room.objects.get(id=room_id) if room_id else None

            # Check for duplicate course on same day
            existing_course = Schedule.objects.filter(
                section=section,
                course=course,
                day=int(day)
            ).exists()
            
            if existing_course:
                return JsonResponse({
                    'success': False,
                    'errors': [f'{course.course_code} is already scheduled on {dict(Schedule.DAY_CHOICES)[int(day)]}. A course cannot have multiple sessions on the same day.']
                })

            # Create new schedule
            schedule = Schedule(
                course=course,
                section=section,
                faculty=faculty,
                room=room,
                day=int(day),
                start_time=start_time,
                end_time=end_time
            )
            # Quick server-side enforcement of allowed window (07:30 - 21:30)
            try:
                def _tmin(tstr):
                    h, m = map(int, tstr.split(':'))
                    return h * 60 + m

                min_allowed = 7 * 60 + 30
                max_allowed = 21 * 60 + 30
                if start_time and end_time:
                    smin = _tmin(start_time)
                    emin = _tmin(end_time)
                    if smin < min_allowed or emin > max_allowed:
                        return JsonResponse({
                            'success': False,
                            'errors': [f'Schedule times must be within 07:30 and 21:30. Received {start_time} - {end_time}']
                        })
            except Exception:
                # fall back to model validation for parsing errors
                pass

            # Validate and save (duration will be calculated automatically in save method)
            schedule.full_clean()
            schedule.save()

            # Log activity
            log_activity(
                user=request.user,
                action='add',
                entity_type='schedule',
                entity_name=f"{course.course_code} - {section.name}",
                message=f'Created schedule: {course.course_code} for {section.name} on {dict(Schedule.DAY_CHOICES)[int(day)]}'
            )

            return JsonResponse({
                'success': True,
                'message': 'Schedule created successfully'
            })
            
        except Course.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Course not found']
            })
        except Section.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Section not found']
            })
        except Faculty.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Faculty not found']
            })
        except Room.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Room not found']
            })
        except ValidationError as e:
            error_messages = []
            if hasattr(e, 'error_dict'):
                for field, errors in e.error_dict.items():
                    for error in errors:
                        error_messages.append(error.message)
            else:
                error_messages = [str(e)]
            
            return JsonResponse({
                'success': False,
                'errors': error_messages
            })
        except Exception as e:
            import traceback
            print(f"Error creating schedule: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [f'Error creating schedule: {str(e)}']
            })
            
    return JsonResponse({
        'success': False,
        'errors': ['Invalid request method']
    })

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_dashboard(request):
    """
    Admin dashboard - displays summary statistics and recent activities
    ONLY accessible by superusers (admins)
    """
    from django.db.models import Sum
    import json
    
    # Get counts from database
    faculty_count = Faculty.objects.count()
    section_count = Section.objects.count()
    
    # Get all curricula for forms
    curricula = Curriculum.objects.all()
    
    # Get faculty list with their total units
    faculty_list = Faculty.objects.all().order_by('last_name', 'first_name')
    
    # Get section list with schedule status
    section_list = Section.objects.all().order_by('year_level', 'semester', 'name')
    
    # Get room list for schedule creation
    room_list = Room.objects.all().order_by('campus', 'room_number')
    
    # Calculate total units for each section (counting unique courses only)
    for section in section_list:
        # Get unique course IDs for this section to avoid double-counting
        unique_course_ids = section.schedules.values_list('course', flat=True).distinct()
        
        # Sum credit units for unique courses only
        calculated_units = Course.objects.filter(id__in=unique_course_ids).aggregate(total=Sum('credit_units'))['total'] or 0
        
        # Add as a temporary attribute (not the property)
        section.calculated_total_units = calculated_units
        
        # Use the actual status field from the database
        section.has_schedule = (section.status == 'complete')
    
    # Get all activities from last 2 days
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Get activities and separate by date
    today_activities = Activity.objects.filter(
        timestamp__date=today
    ).order_by('-timestamp')[:10]

    yesterday_activities = Activity.objects.filter(
        timestamp__date=yesterday
    ).order_by('-timestamp')[:10]

    # Create recent_activities dictionary for template
    recent_activities = {}
    if today_activities:
        recent_activities['Today'] = today_activities
    if yesterday_activities:
        recent_activities['Yesterday'] = yesterday_activities
    
    # Get courses - show only courses handled by logged-in faculty member
    try:
        faculty_profile = Faculty.objects.get(user=request.user)
        # Get courses from schedules assigned to this faculty member
        scheduled_courses = Course.objects.filter(
            schedules__faculty=faculty_profile
        ).distinct().order_by('course_code')
    except Faculty.DoesNotExist:
        # Pure admins with no faculty profile see all courses
        scheduled_courses = Course.objects.all().order_by('course_code')
    
    # Generate time slots from 7:30 AM to 9:30 PM (30-minute intervals)
    time_slots = []
    time_slots.append("07:30")
    for hour in range(8, 22):
        for minute in ['00', '30']:
            if hour == 21 and minute == '30':
                break
            time_slots.append(f"{hour:02d}:{minute}")
    time_slots.append("21:30")
    
    # Days of the week
    days = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday')
    ]
    
    # Get schedules - filter by logged-in admin's faculty profile if they have one
    try:
        faculty_profile = Faculty.objects.get(user=request.user)
        # If logged-in admin has a faculty profile, show only THEIR schedules
        schedules = Schedule.objects.filter(faculty=faculty_profile).select_related(
            'course', 'section', 'faculty', 'room'
        )
    except Faculty.DoesNotExist:
        # If no faculty profile, show all schedules (for pure admin accounts)
        schedules = Schedule.objects.select_related(
            'course', 'section', 'faculty', 'room'
        ).all()
    
    # Try to get faculty profile for current user (may not exist for pure admin accounts)
    try:
        current_faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        current_faculty = None
    
    context = {
        'user': request.user,
        'faculty': current_faculty,
        'faculty_count': faculty_count,
        'section_count': section_count,
        'faculty_list': faculty_list,
        'section_list': section_list,
        'room_list': room_list,
        'recent_activities': recent_activities,
        'scheduled_courses': scheduled_courses,
        'time_slots': time_slots,
        'days': days,
        'schedules': schedules,
        'curricula': curricula,
        'all_courses': Course.objects.all().order_by('course_code'),
    }
    
    return render(request, 'hello/dashboard.html', context)

def log_activity(user, action, entity_type, entity_name, message):
    """Helper function to log activities"""
    Activity.objects.create(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_name=entity_name,
        message=message
    )

def generate_password(length=12):
    """Generate a random password with at least one uppercase, lowercase, digit, and special character"""
    # Ensure password has at least one of each required type
    password_chars = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*")
    ]
    
    # Fill the rest with random characters
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password_chars += [random.choice(all_chars) for _ in range(length - 4)]
    
    # Shuffle to avoid predictable pattern
    random.shuffle(password_chars)
    return ''.join(password_chars)

# ===== FACULTY VIEWS =====

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def faculty_view(request):
    """Faculty management page"""
    # Get all faculty members
    faculties = Faculty.objects.all().order_by('last_name', 'first_name')
    
    # Get all courses for specialization selection
    courses = Course.objects.all().order_by('course_code')
    
    # Try to get faculty profile for current user (may not exist for pure admin accounts)
    try:
        current_faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        current_faculty = None
    
    context = {
        'user': request.user,
        'faculty': current_faculty,
        'faculties': faculties,
        'courses': courses,
    }
    
    return render(request, 'hello/faculty.html', context)

def add_faculty(request):
    """Add new faculty member with proper email validation and sending"""
    if request.method == 'POST':
        if not request.user.is_authenticated or not is_admin(request.user):
            return JsonResponse({
                'success': False,
                'errors': ['Authentication required. Please login again and try.']
            }, status=401)

        try:
            # Get form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            gender = request.POST.get('gender')
            role = request.POST.get('role')
            employment_status = request.POST.get('employment_status')
            highest_degree = request.POST.get('highest_degree', '')
            prc_licensed = request.POST.get('prc_licensed') == 'on'
            specialization_ids = request.POST.getlist('specialization')
            
            # Normalize and validate email domain
            email = email.strip().lower()
            if not email.endswith('@tip.edu.ph'):
                return JsonResponse({
                    'success': False,
                    'errors': ['Only @tip.edu.ph email addresses can be used to create an account.']
                })

            # Check if email already exists (case-insensitive)
            if Faculty.objects.filter(email__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['This email is already registered.']
                })

            password = generate_password()
            username = email

            # Check if username already exists, which is same as email in this flow
            if User.objects.filter(username__iexact=username).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['This username is already taken.']
                })

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Set user permissions based on role
            if role == 'admin':
                user.is_staff = True
                user.is_superuser = True
            else:
                user.is_staff = True
                user.is_superuser = False
            
            user.save()
            
            # Create Faculty record
            faculty = Faculty.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                gender=gender,
                employment_status=employment_status,
                highest_degree=highest_degree,
                prc_licensed=prc_licensed
            )
            
            # Add specializations
            if specialization_ids:
                courses = Course.objects.filter(id__in=specialization_ids)
                faculty.specialization.set(courses)
            
            # Send email with a password reset invitation link using configured SMTP backend
            email_sent = False
            try:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                reset_url = request.build_absolute_uri(reset_path)

                subject = 'Your ASSIST Account Invitation'
                message = f'''Hello {first_name},

Your ASSIST account has been created successfully.

Username: {username}

To complete your account setup and choose a secure password, click the link below:
{reset_url}

If you cannot click the link, copy and paste it into your browser.

If you did not request this account, please contact the administrator immediately.

Best regards,
ASSIST Administration Team'''

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )

                email_sent = True
                message_text = f'Faculty added successfully. An invitation email has been sent to {email}.'
            except Exception as e:
                print(f"Error sending invitation email: {str(e)}")
                email_sent = False
                message_text = (
                    'Faculty added successfully, but email could not be sent. '
                    'Please check your SMTP settings and credentials.'
                )
            
            # Log activity
            log_activity(
                user=request.user,
                action='add',
                entity_type='faculty',
                entity_name=f"{first_name} {last_name}",
                message=f'Added faculty: {first_name} {last_name} ({role}) - Email {"sent" if email_sent else "failed"}'
            )
            
            return JsonResponse({
                'success': True,
                'message': message_text,
                'credentials': {
                    'username': username,
                    'password': password
                } if not email_sent else None
            })
            
        except Exception as e:
            import traceback
            print(f"Error adding faculty: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [f'Error adding faculty: {str(e)}']
            })
    
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_faculty(request, faculty_id):
    """Edit existing faculty member"""
    faculty = get_object_or_404(Faculty, id=faculty_id)
    
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            
            # Validate email domain
            if '@' not in email or '.' not in email.split('@')[1]:
                return JsonResponse({
                    'success': False,
                    'errors': ['Please enter a valid email address with a proper domain (e.g., user@gmail.com)']
                })
            
            # Check if email is taken by another faculty
            if Faculty.objects.filter(email=email).exclude(id=faculty_id).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['This email is already registered to another faculty member.']
                })
            
            faculty.first_name = request.POST.get('first_name')
            faculty.last_name = request.POST.get('last_name')
            faculty.email = email
            faculty.gender = request.POST.get('gender')
            faculty.employment_status = request.POST.get('employment_status')
            faculty.highest_degree = request.POST.get('highest_degree', '')
            faculty.prc_licensed = request.POST.get('prc_licensed') == 'on'
            
            # Update specializations
            specialization_ids = request.POST.getlist('specialization')
            if specialization_ids:
                courses = Course.objects.filter(id__in=specialization_ids)
                faculty.specialization.set(courses)
            else:
                faculty.specialization.clear()
            
            # Update User account
            if faculty.user:
                role = request.POST.get('role')
                faculty.user.email = faculty.email
                faculty.user.first_name = faculty.first_name
                faculty.user.last_name = faculty.last_name
                
                if role == 'admin':
                    faculty.user.is_staff = True
                    faculty.user.is_superuser = True
                else:
                    faculty.user.is_staff = True
                    faculty.user.is_superuser = False
                
                faculty.user.save()
            
            faculty.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='edit',
                entity_type='faculty',
                entity_name=f"{faculty.first_name} {faculty.last_name}",
                message=f'Edited faculty: {faculty.first_name} {faculty.last_name}'
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    # Return faculty data for editing
    specialization_ids = list(faculty.specialization.values_list('id', flat=True))
    role = 'admin' if faculty.user and faculty.user.is_superuser else 'staff'
    
    return JsonResponse({
        'id': faculty.id,
        'first_name': faculty.first_name,
        'last_name': faculty.last_name,
        'email': faculty.email,
        'gender': faculty.gender,
        'role': role,
        'employment_status': faculty.employment_status,
        'highest_degree': faculty.highest_degree,
        'prc_licensed': faculty.prc_licensed,
        'specialization': specialization_ids
    })

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_faculty(request, faculty_id):
    """Delete faculty member"""
    if request.method == 'POST':
        faculty = get_object_or_404(Faculty, id=faculty_id)
        faculty_name = f"{faculty.first_name} {faculty.last_name}"
        faculty_email = faculty.email
        
        # Remember linked user (if any) so we can clean up that specific account
        linked_user = getattr(faculty, 'user', None)

        # Unassign faculty from any schedules (preserve schedule records)
        Schedule.objects.filter(faculty=faculty).update(faculty=None)

        # Delete the Faculty record
        faculty.delete()

        # Clean up all User accounts associated with this email
        # This handles both the linked user and any orphaned users with the same email
        try:
            User.objects.filter(email__iexact=faculty_email.strip().lower()).delete()
        except Exception:
            # Don't fail the whole operation if user deletion has an issue
            pass

        log_activity(
            user=request.user,
            action='delete',
            entity_type='faculty',
            entity_name=faculty_name,
            message=f'Deleted faculty: {faculty_name} and cleaned up associated user account(s) with email {faculty_email}'
        )

        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def get_faculty_schedule(request, faculty_id):
    """Get schedule data for a specific faculty member"""
    try:
        faculty = get_object_or_404(Faculty, id=faculty_id)
        
        # Get all schedules for this faculty
        schedules = Schedule.objects.filter(faculty=faculty).select_related(
            'course', 'section', 'room'
        ).order_by('day', 'start_time')
        
        # Format schedule data
        schedule_data = []
        for schedule in schedules:
            schedule_item = {
                'day': schedule.day,
                'start_time': schedule.start_time,
                'end_time': schedule.end_time,
                'duration': schedule.duration,
                'course_code': schedule.course.course_code,
                'course_title': schedule.course.descriptive_title,
                'course_color': schedule.course.color,
                'room': schedule.room.name if schedule.room else 'TBA',
                'section_name': schedule.section.name,
            }
            schedule_data.append(schedule_item)
        
        # Get faculty specializations
        specializations = []
        for course in faculty.specialization.all():
            specializations.append({
                'course_code': course.course_code,
                'descriptive_title': course.descriptive_title,
                'color': course.color
            })
        
        return JsonResponse({
            'success': True,
            'schedules': schedule_data,
            'specializations': specializations,
            'total_units': faculty.total_units
        })
    except Exception as e:
        import traceback
        print(f"Error in get_faculty_schedule: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    
    # ===== ROOM VIEWS =====

@login_required(login_url='admin_login')
def room_view(request):
    """Room management page"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('admin_login')
    
    # Get all rooms
    rooms = Room.objects.all().order_by('campus', 'room_number')
    
    # Try to get faculty profile for current user (may not exist for pure admin accounts)
    try:
        current_faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        current_faculty = None
    
    context = {
        'user': request.user,
        'faculty': current_faculty,
        'rooms': rooms,
    }
    
    return render(request, 'hello/room.html', context)

@login_required(login_url='admin_login')
def add_room(request):
    """Add new room"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            room_number = request.POST.get('room_number')
            capacity = int(request.POST.get('capacity', 40))
            campus = request.POST.get('campus')
            room_type = request.POST.get('room_type')
            
            room = Room.objects.create(
                name=name,
                room_number=room_number,
                capacity=capacity,
                campus=campus,
                room_type=room_type
            )
            
            log_activity(
                user=request.user,
                action='add',
                entity_type='room',
                entity_name=room.name,
                message=f'Added room: {room.name} - {room.get_campus_display()} Campus'
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def edit_room(request, room_id):
    """Edit existing room"""
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        try:
            room.name = request.POST.get('name')
            room.room_number = request.POST.get('room_number')
            room.capacity = int(request.POST.get('capacity'))
            room.campus = request.POST.get('campus')
            room.room_type = request.POST.get('room_type')
            
            room.save()
            
            log_activity(
                user=request.user,
                action='edit',
                entity_type='room',
                entity_name=room.name,
                message=f'Edited room: {room.name} - {room.get_campus_display()} Campus'
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    return JsonResponse({
        'id': room.id,
        'name': room.name,
        'room_number': room.room_number,
        'capacity': room.capacity,
        'campus': room.campus,
        'room_type': room.room_type,
    })

@login_required(login_url='admin_login')
def delete_room(request, room_id):
    """Delete room"""
    if request.method == 'POST':
        room = get_object_or_404(Room, id=room_id)
        room_name = room.name
        
        room.delete()
        
        log_activity(
            user=request.user,
            action='delete',
            entity_type='room',
            entity_name=room_name,
            message=f'Deleted room: {room_name}'
        )
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def get_room_schedule(request, room_id):
    """Get schedule data for a specific room"""
    try:
        room = get_object_or_404(Room, id=room_id)
        
        # Get all schedules for this room
        schedules = Schedule.objects.filter(room=room).select_related(
            'course', 'section', 'faculty'
        ).order_by('day', 'start_time')
        
        # Format schedule data
        schedule_data = []
        courses_map = {}
        
        for schedule in schedules:
            schedule_item = {
                'day': schedule.day,
                'start_time': schedule.start_time,
                'end_time': schedule.end_time,
                'duration': schedule.duration,
                'course_code': schedule.course.course_code,
                'course_title': schedule.course.descriptive_title,
                'course_color': schedule.course.color,
                'section_name': schedule.section.name,
                'faculty': f"{schedule.faculty.first_name} {schedule.faculty.last_name}" if schedule.faculty else 'TBA',
                # Add room information for display
                'room_name': room.name,
                'room_number': room.room_number,
                'campus': room.campus
            }
            schedule_data.append(schedule_item)
            
            # Track unique courses for sidebar
            if schedule.course.course_code not in courses_map:
                courses_map[schedule.course.course_code] = {
                    'course_code': schedule.course.course_code,
                    'descriptive_title': schedule.course.descriptive_title,
                    'color': schedule.course.color,
                    'lecture_hours': schedule.course.lecture_hours,
                    'laboratory_hours': schedule.course.laboratory_hours,
                    'credit_units': schedule.course.credit_units
                }
        
        # Convert courses_map to list
        courses_list = list(courses_map.values())
        
        return JsonResponse({
            'success': True,
            'schedules': schedule_data,
            'courses': courses_list,
            'room_info': {
                'name': room.name,
                'room_number': room.room_number,
                'campus': room.get_campus_display(),
                'room_type': room.get_room_type_display(),
                'capacity': room.capacity
            }
        })
    except Exception as e:
        import traceback
        print(f"Error in get_room_schedule: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    
@login_required(login_url='admin_login')
def schedule_view(request):
    """Schedule management page - shows sections"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('admin_login')
    
    # Get all sections with their schedules
    sections = Section.objects.select_related('curriculum').all()
    
    # Calculate total units for each section
    for section in sections:
        unique_course_ids = section.schedules.values_list('course', flat=True).distinct()
        total = Course.objects.filter(id__in=unique_course_ids).aggregate(
            total=Sum('credit_units')
        )['total'] or 0
        section.calculated_total_units = total
    
    # Get data needed for the create schedule modal
    all_courses = Course.objects.all().order_by('course_code')
    faculty_list = Faculty.objects.all().order_by('last_name', 'first_name')
    section_list = Section.objects.all().order_by('year_level', 'semester', 'name')
    room_list = Room.objects.all().order_by('campus', 'room_number')
    
    # Try to get faculty profile for current user (may not exist for pure admin accounts)
    try:
        current_faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        current_faculty = None
    
    context = {
        'user': request.user,
        'faculty': current_faculty,
        'sections': sections,
        'all_courses': all_courses,
        'faculty_list': faculty_list,
        'section_list': section_list,
        'room_list': room_list,
        'curricula': Curriculum.objects.all().order_by('-year'),
    }
    
    return render(request, 'hello/schedule.html', context)

@login_required(login_url='admin_login')
def toggle_section_status(request, section_id):
    """Toggle section schedule status"""
    if request.method == 'POST':
        section = get_object_or_404(Section, id=section_id)
        
        # Toggle status
        if section.status == 'complete':
            section.status = 'incomplete'
            status_text = 'No Schedule Yet'
        else:
            section.status = 'complete'
            status_text = 'Complete Schedule'
        
        section.save()
        
        log_activity(
            user=request.user,
            action='edit',
            entity_type='section',
            entity_name=section.name,
            message=f'Updated schedule status for {section.name} to: {status_text}'
        )
        
        return JsonResponse({
            'success': True,
            'status': section.status,
            'status_display': section.get_status_display()
        })
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def delete_schedule(request, schedule_id):
    """Delete schedule"""
    if request.method == 'POST':
        schedule = get_object_or_404(Schedule, id=schedule_id)
        course_code = schedule.course.course_code
        section_name = schedule.section.name
        
        schedule.delete()
        
        log_activity(
            user=request.user,
            action='delete',
            entity_type='schedule',
            entity_name=f"{course_code} - {section_name}",
            message=f'Deleted schedule: {course_code} for {section_name}'
        )
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_section_schedules(request, section_id):
    """Delete all schedules for a section"""
    if request.method == 'POST':
        section = get_object_or_404(Section, id=section_id)
        schedules_qs = Schedule.objects.filter(section=section)
        deleted_count = schedules_qs.count()

        if deleted_count == 0:
            return JsonResponse({'success': True, 'message': 'No schedules found for this section.'})

        schedules_qs.delete()
        section.status = 'incomplete'
        section.save()

        log_activity(
            user=request.user,
            action='delete',
            entity_type='schedule',
            entity_name=f'All schedules for {section.name}',
            message=f'Deleted {deleted_count} schedules for section {section.name}'
        )

        return JsonResponse({'success': True, 'deleted_count': deleted_count})
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def staff_dashboard(request):
    """
    Staff dashboard - limited view for non-admin faculty
    Shows ONLY their assigned schedule and basic information
    """
    # Check if user has faculty profile
    try:
        faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        messages.error(request, 'No faculty profile found for your account.')
        logout(request)
        return redirect('admin_login')
    
    # Get ONLY this faculty's schedules (strict filtering by faculty FK)
    schedules = Schedule.objects.filter(faculty=faculty).select_related(
        'course', 'section', 'room'
    ).order_by('day', 'start_time')
    
    # Format schedule data for JavaScript
    schedule_data = []
    for schedule in schedules:
        # SAFETY CHECK: Ensure this schedule actually belongs to the logged-in faculty
        if schedule.faculty_id != faculty.id:
            # Skip schedules not assigned to this faculty (should never happen)
            continue
            
        schedule_data.append({
            'day': schedule.day,
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
            'duration': schedule.duration,
            'course_code': schedule.course.course_code,
            'course_title': schedule.course.descriptive_title,
            'course_color': schedule.course.color,
            'room': schedule.room.name if schedule.room else 'TBA',
            'section_name': schedule.section.name,
        })
    
    # Get specializations
    specializations = faculty.specialization.all()
    
    import json
    
    context = {
        'user': request.user,
        'faculty': faculty,
        'schedules': json.dumps(schedule_data),  # Serialize to JSON
        'time_slots': [],  # Will be generated by JavaScript
        'days': [],  # Will be generated by JavaScript
        'specializations': specializations,
    }
    
    return render(request, 'hello/staff_dashboard.html', context)


@login_required(login_url='admin_login')
def staff_schedule(request):
    """
    Staff schedule page - shows the logged-in faculty's schedule in full-page schedule view
    """
    try:
        faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        messages.error(request, 'No faculty profile found for your account.')
        logout(request)
        return redirect('admin_login')

    schedules = Schedule.objects.filter(faculty=faculty).select_related(
        'course', 'section', 'room'
    ).order_by('day', 'start_time')

    # Format schedule data for JavaScript
    schedule_data = []
    for schedule in schedules:
        if schedule.faculty_id != faculty.id:
            continue
        schedule_data.append({
            'day': schedule.day,
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
            'duration': schedule.duration,
            'course_code': schedule.course.course_code,
            'course_title': schedule.course.descriptive_title,
            'course_color': schedule.course.color,
            'room': schedule.room.name if schedule.room else 'TBA',
            'section_name': schedule.section.name,
        })

    specializations = faculty.specialization.all()

    import json

    context = {
        'user': request.user,
        'faculty': faculty,
        'schedules': json.dumps(schedule_data),
        'time_slots': [],
        'days': [],
        'specializations': specializations,
    }

    return render(request, 'hello/staff_schedule.html', context)


@login_required(login_url='admin_login')
def staff_schedule_print(request):
    """
    Print-friendly view for staff teaching assignment
    """
    try:
        faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        messages.error(request, 'No faculty profile found for your account.')
        logout(request)
        return redirect('admin_login')

    schedules = Schedule.objects.filter(faculty=faculty).select_related(
        'course', 'section', 'room'
    ).order_by('day', 'start_time')

    # Build schedule table data for print template with rowspan so we can render
    # continuous vertical arrows from start_time -> end_time.
    raw_schedules = []
    for schedule in schedules:
        if schedule.faculty_id != faculty.id:
            continue
        raw_schedules.append({
            'day': schedule.day,
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
            'course_code': schedule.course.course_code,
            'room': schedule.room.name if schedule.room else 'TBA',
            'section_name': schedule.section.name,
        })

    # Generate 30-minute time slots from 07:30 to 21:30 (skip 07:00)
    time_slots = []
    time_slots.append("07:30")
    for hour in range(8, 22):
        for minute in ['00', '30']:
            if hour == 21 and minute == '30':
                break
            time_slots.append(f"{hour:02d}:{minute}")
    time_slots.append("21:30")

    days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']

    # Compute simple table-based grid metrics (each 30-min slot = 60px row height
    # matching the interactive layout style). We'll expose `grid_height` and `time_labels` to
    # the template so the print view can render absolute-positioned, centered
    # time labels matching staff_schedule.html (07:30 at 120px, 08:00 at 180px, etc).
    # NOTE: There are 2 empty rows before the first time slot (07:30), so offset by 120px (2 * 60px)
    try:
        row_height = 60
        # The 1 empty row at the top takes up 60px
        # Keep time labels at their proper positions: 120px for 07:30, etc
        header_offset = 2 * row_height  # Keep 120px for time label positioning
        grid_height = len(time_slots) * row_height + header_offset
        time_labels = []
        for idx, t in enumerate(time_slots):
            # Position at 120px + idx * 60px (centered on horizontal lines)
            top_px = header_offset + idx * row_height
            time_labels.append({'time': t, 'top': top_px})
    except Exception:
        header_offset = 120
        grid_height = len(time_slots) * 60 + 120
        time_labels = [{'time': t, 'top': 120 + i * 60} for i, t in enumerate(time_slots)]

    # Helper to normalize time values to HH:MM strings
    from datetime import time as _time
    def _normalize_time(val):
        if val is None:
            return None
        # If it's already a string, try to parse and reformat to HH:MM
        if isinstance(val, str):
            try:
                parts = val.split(':')
                h = int(parts[0])
                m = int(parts[1]) if len(parts) > 1 else 0
                return f"{h:02d}:{m:02d}"
            except Exception:
                return val
        # If it's a time or datetime, format accordingly
        try:
            return val.strftime('%H:%M')
        except Exception:
            return str(val)

    # Build a mapping for schedules keyed by (day, start_time) with rowspan, and a set
    # of covered (day, time) slots to skip when rendering cells.
    schedule_map = {}
    covered = set()
    for rs in raw_schedules:
        day_idx = rs['day']
        start = _normalize_time(rs['start_time'])
        end = _normalize_time(rs['end_time'])
        if not start or not end:
            key = (day_idx, start)
            schedule_map[key] = {
                'rowspan': 1,
                'course_code': rs['course_code'],
                'room': rs['room'],
                'section_name': rs['section_name'],
            }
            continue

        # Compute start/end indexes by minutes to be robust to different time formats
        def _to_minutes(tval):
            if tval is None:
                return None
            if isinstance(tval, str):
                try:
                    parts = tval.split(':')
                    h = int(parts[0])
                    m = int(parts[1]) if len(parts) > 1 else 0
                    return h * 60 + m
                except Exception:
                    # try removing seconds or whitespace
                    try:
                        hhmm = tval.strip().split('.')[0]
                        h, m = map(int, hhmm.split(':')[:2])
                        return h * 60 + m
                    except Exception:
                        return None
            try:
                return tval.hour * 60 + tval.minute
            except Exception:
                try:
                    s = str(tval)
                    h, m = map(int, s.split(':')[:2])
                    return h * 60 + m
                except Exception:
                    return None

        start_min = _to_minutes(start)
        end_min = _to_minutes(end)

        # Clamp end_min to the printable/schedulable maximum (21:30)
        try:
            last_slot_min = 21 * 60 + 30
            if end_min is not None and end_min > last_slot_min:
                end_min = last_slot_min
        except Exception:
            pass

        if start_min is None or end_min is None:
            key = (day_idx, start)
            schedule_map[key] = {
                'rowspan': 1,
                'course_code': rs['course_code'],
                'room': rs['room'],
                'section_name': rs['section_name'],
            }
            continue

        # Base is 07:30 (in minutes)
        base_min = 7 * 60 + 30
        start_index = (start_min - base_min) // 30
        # Calculate number of 30-minute slots from the duration.
        # A class that lasts 60 minutes should span 2 slots. Do NOT add
        # an extra '+1' - that caused rowspan to cover extra rows and hide
        # other courses. Use integer division and clamp to at least 1.
        slots = (end_min - start_min) // 30
        if slots < 1:
            slots = 1
        
        # Clamp start_index into valid range
        start_index = max(0, start_index)
        # Ensure start_index is within time_slots bounds
        if start_index >= len(time_slots):
            start_index = len(time_slots) - 1

        # Emit debug info to server log when running in DEBUG mode
        try:
            if settings.DEBUG:
                print(f"[staff_schedule_print] course={rs.get('course_code')} day={day_idx} start={start} end={end} start_min={start_min} end_min={end_min} start_idx={start_index} slots={slots}")
        except Exception:
            pass
        # Use time_slots[start_index] as the key to ensure it matches exactly what's in time_slots
        key = (day_idx, time_slots[start_index])
        schedule_map[key] = {
            'rowspan': slots,
            'course_code': rs['course_code'],
            'room': rs['room'],
            'section_name': rs['section_name'],
        }
        for j in range(1, slots):
            # Protect index range
            idx = start_index + j
            if 0 <= idx < len(time_slots):
                time_slot_key = time_slots[idx]
                # Only mark as covered if this time slot doesn't have another course
                if (day_idx, time_slot_key) not in schedule_map:
                    covered.add((day_idx, time_slot_key))

    # Construct table rows: each row contains time, an optional time_cell (for rowspan
    # centering of the time label), and a list of 6 cell entries. Cell entries can be:
    # None, 'skip', or schedule dict (rowspan cell that includes the end row).
    table_rows = []

    # Precompute time column rowspans: when a schedule cell starts at a timeslot and
    # spans multiple slots, we may want to render the TIME column once with a rowspan
    # equal to the largest starting-span at that timeslot so the time label sits
    # vertically centered next to multi-row course blocks.
    time_covered = set()
    time_rowspan_map = {}
    for idx, t in enumerate(time_slots):
        if t in time_covered:
            continue
        # Compute the max rowspan among all schedules that start at this timeslot
        max_slots = 1
        for d in range(6):
            key = (d, t)
            if key in schedule_map:
                try:
                    r = int(schedule_map[key].get('rowspan', 1))
                except Exception:
                    r = 1
                if r > max_slots:
                    max_slots = r
        # If the max_slots > 1, mark the subsequent (max_slots-1) timeslots as covered
        if max_slots > 1:
            for j in range(1, max_slots):
                next_idx = idx + j
                if 0 <= next_idx < len(time_slots):
                    time_covered.add(time_slots[next_idx])
        time_rowspan_map[t] = max_slots

    for t in time_slots:
        cells = []
        for d in range(6):
            if (d, t) in covered:
                cells.append('skip')
            elif (d, t) in schedule_map:
                cells.append(schedule_map[(d, t)])
            else:
                cells.append(None)
        # Attach a time_cell only if this timeslot is not covered by a previous
        # time_cell rowspan. time_rowspan_map contains the intended rowspan (>=1).
        time_cell = None
        if t not in time_covered:
            time_cell = {
                'text': t,
                'rowspan': time_rowspan_map.get(t, 1)
            }
        table_rows.append({'time': t, 'time_cell': time_cell, 'cells': cells})

    # Compute totals based on unique courses assigned to this faculty.
    unique_course_ids = faculty.schedules.values_list('course', flat=True).distinct()
    totals = Course.objects.filter(id__in=unique_course_ids).aggregate(
        total_lec=Sum('lecture_hours'),
        total_lab=Sum('laboratory_hours'),
        total_units=Sum('credit_units')
    )

    context = {
        'user': request.user,
        'faculty': faculty,
        'table_rows': table_rows,
        'grid_height': grid_height,
        'time_labels': time_labels,
        'time_slots': time_slots,
        'days': days,
        'total_lec': totals.get('total_lec') or 0,
        'total_lab': totals.get('total_lab') or 0,
        'total_units': totals.get('total_units') or 0,
    }

    return render(request, 'hello/staff_schedule_print.html', context)

# ===== SECTION VIEWS =====

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def section_view(request):
    """Section management page"""
    # Get all sections with their related curriculum
    sections = Section.objects.select_related('curriculum').all().order_by('year_level', 'semester', 'name')
    
    # Calculate total units for each section
    for section in sections:
        unique_course_ids = section.schedules.values_list('course', flat=True).distinct()
        total = Course.objects.filter(id__in=unique_course_ids).aggregate(
            total=Sum('credit_units')
        )['total'] or 0
        section.calculated_total_units = total
    
    # Get all curricula for the add/edit section forms
    curricula = Curriculum.objects.all().order_by('-year')
    
    # Get all courses for schedule creation
    all_courses = Course.objects.all().order_by('course_code')
    
    # Get faculty and rooms for schedule modal
    faculty_list = Faculty.objects.all().order_by('last_name', 'first_name')
    room_list = Room.objects.all().order_by('campus', 'room_number')
    
    # Try to get faculty profile for current user (may not exist for pure admin accounts)
    try:
        current_faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        current_faculty = None
    
    context = {
        'user': request.user,
        'faculty': current_faculty,
        'sections': sections,
        'curricula': curricula,
        'all_courses': all_courses,
        'faculty_list': faculty_list,
        'room_list': room_list,
    }
    
    return render(request, 'hello/section.html', context)

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_section(request):
    """Add new section"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            year_level = int(request.POST.get('year_level'))
            semester = int(request.POST.get('semester'))
            curriculum_id = request.POST.get('curriculum')
            max_students = int(request.POST.get('max_students', 40))
            
            curriculum = Curriculum.objects.get(id=curriculum_id)
            
            # Check if section name already exists for this curriculum
            if Section.objects.filter(name=name, curriculum=curriculum).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['A section with this name already exists in the selected curriculum.']
                })
            
            section = Section(
                name=name,
                year_level=year_level,
                semester=semester,
                curriculum=curriculum,
                max_students=max_students,
                status='incomplete'
            )
            
            # This will validate the section name format
            section.full_clean()
            section.save()
            
            log_activity(
                user=request.user,
                action='add',
                entity_type='section',
                entity_name=section.name,
                message=f'Added section: {section.name} - Year {year_level}, Semester {semester}'
            )
            
            return JsonResponse({'success': True})
            
        except Curriculum.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Selected curriculum does not exist.']
            })
        except ValidationError as e:
            error_messages = []
            if hasattr(e, 'error_dict'):
                for field, errors in e.error_dict.items():
                    for error in errors:
                        error_messages.append(error.message)
            else:
                error_messages = [str(e)]
            
            return JsonResponse({
                'success': False,
                'errors': error_messages
            })
        except Exception as e:
            import traceback
            print(f"Error adding section: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [f'Error adding section: {str(e)}']
            })
    
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_section(request, section_id):
    """Edit existing section"""
    section = get_object_or_404(Section, id=section_id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            year_level = int(request.POST.get('year_level'))
            semester = int(request.POST.get('semester'))
            curriculum_id = request.POST.get('curriculum')
            max_students = int(request.POST.get('max_students', 40))
            
            curriculum = Curriculum.objects.get(id=curriculum_id)
            
            # Check if section name already exists for this curriculum (excluding current section)
            if Section.objects.filter(name=name, curriculum=curriculum).exclude(id=section_id).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['A section with this name already exists in the selected curriculum.']
                })
            
            section.name = name
            section.year_level = year_level
            section.semester = semester
            section.curriculum = curriculum
            section.max_students = max_students
            
            section.full_clean()
            section.save()
            
            log_activity(
                user=request.user,
                action='edit',
                entity_type='section',
                entity_name=section.name,
                message=f'Edited section: {section.name} - Year {year_level}, Semester {semester}'
            )
            
            return JsonResponse({'success': True})
            
        except Curriculum.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Selected curriculum does not exist.']
            })
        except ValidationError as e:
            error_messages = []
            if hasattr(e, 'error_dict'):
                for field, errors in e.error_dict.items():
                    for error in errors:
                        error_messages.append(error.message)
            else:
                error_messages = [str(e)]
            
            return JsonResponse({
                'success': False,
                'errors': error_messages
            })
        except Exception as e:
            import traceback
            print(f"Error editing section: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    # Return section data for editing
    return JsonResponse({
        'id': section.id,
        'name': section.name,
        'year_level': section.year_level,
        'semester': section.semester,
        'curriculum': section.curriculum.id,
        'max_students': section.max_students,
        'status': section.status
    })

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_section(request, section_id):
    """Delete section"""
    if request.method == 'POST':
        section = get_object_or_404(Section, id=section_id)
        section_name = section.name
        
        # Check if section has schedules
        if section.schedules.exists():
            return JsonResponse({
                'success': False,
                'errors': ['Cannot delete section with existing schedules. Delete schedules first.']
            })
        
        section.delete()
        
        log_activity(
            user=request.user,
            action='delete',
            entity_type='section',
            entity_name=section_name,
            message=f'Deleted section: {section_name}'
        )
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def get_section_schedule(request, section_id):
    """Get schedule data for a specific section"""
    try:
        section = get_object_or_404(Section, id=section_id)
        
        # Get all schedules for this section
        schedules = Schedule.objects.filter(section=section).select_related(
            'course', 'faculty', 'room'
        ).order_by('day', 'start_time')
        
        # Format schedule data
        schedule_data = []
        courses_map = {}
        
        for schedule in schedules:
            schedule_item = {
                'id': schedule.id,
                'day': schedule.day,
                'start_time': schedule.start_time,
                'end_time': schedule.end_time,
                'duration': schedule.duration,
                'course_id': schedule.course.id,
                'course_code': schedule.course.course_code,
                'course_title': schedule.course.descriptive_title,
                'course_color': schedule.course.color,
                'faculty': f"{schedule.faculty.first_name} {schedule.faculty.last_name}" if schedule.faculty else 'TBA',
                'room': schedule.room.name if schedule.room else 'TBA',
                'section_name': schedule.section.name,
            }
            schedule_data.append(schedule_item)
            
            # Track unique courses for sidebar
            course_entry = courses_map.get(schedule.course.id)
            if not course_entry:
                # Use a set to collect faculty names, convert later for JSON
                courses_map[schedule.course.id] = {
                    'course_code': schedule.course.course_code,
                    'descriptive_title': schedule.course.descriptive_title,
                    'color': schedule.course.color,
                    'lecture_hours': schedule.course.lecture_hours,
                    'laboratory_hours': schedule.course.laboratory_hours,
                    'credit_units': schedule.course.credit_units,
                    'faculty_names': set()
                }

            # Add faculty name to the course's faculty set (skip if None)
            if schedule.faculty:
                fname = f"{schedule.faculty.first_name} {schedule.faculty.last_name}"
                courses_map[schedule.course.id]['faculty_names'].add(fname)
        
        # Convert courses_map to list and format faculty names for JSON
        courses_list = []
        for entry in courses_map.values():
            faculty_names = entry.pop('faculty_names', set())
            entry['faculty'] = ', '.join(sorted(faculty_names)) if faculty_names else 'TBA'
            courses_list.append(entry)

        # Calculate total units
        total_units = sum(course['credit_units'] for course in courses_list)
        
        return JsonResponse({
            'success': True,
            'schedules': schedule_data,
            'courses': courses_list,
            'total_units': total_units,
            'section_info': {
                'name': section.name,
                'year_level': section.year_level,
                'semester': section.semester,
                'curriculum': str(section.curriculum),
                'max_students': section.max_students
            }
        })
    except Exception as e:
        import traceback
        print(f"Error in get_section_schedule: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def toggle_section_status(request, section_id):
    """Toggle section schedule status"""
    if request.method == 'POST':
        section = get_object_or_404(Section, id=section_id)
        
        # Toggle status
        if section.status == 'complete':
            section.status = 'incomplete'
            status_text = 'No Schedule Yet'
        else:
            section.status = 'complete'
            status_text = 'Complete Schedule'
        
        section.save()
        
        log_activity(
            user=request.user,
            action='edit',
            entity_type='section',
            entity_name=section.name,
            message=f'Updated schedule status for {section.name} to: {status_text}'
        )
        
        return JsonResponse({
            'success': True,
            'status': section.status,
            'status_display': section.get_status_display()
        })
    return JsonResponse({'success': False})

# ===== COURSE VIEWS =====

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def course_view(request):
    """Course management page"""
    # Get all curricula for the add/edit course forms
    curricula = Curriculum.objects.all().order_by('-year')

    # Read optional filters from querystring
    curriculum_id = request.GET.get('curriculum')
    selected_curriculum = None
    selected_year = request.GET.get('year')
    selected_semester = request.GET.get('semester')

    grouped_courses = {}
    academic_levels = []

    if curriculum_id:
        try:
            selected_curriculum = Curriculum.objects.get(id=curriculum_id)

            # Base queryset for this curriculum
            qs = Course.objects.filter(curriculum=selected_curriculum).order_by('year_level', 'semester', 'course_code')

            # Apply year/semester filters if present
            if selected_year:
                try:
                    qs = qs.filter(year_level=int(selected_year))
                except ValueError:
                    pass
            if selected_semester:
                try:
                    qs = qs.filter(semester=int(selected_semester))
                except ValueError:
                    pass

            # Build academic_levels (distinct year/semester pairs)
            levels = qs.values('year_level', 'semester').distinct().order_by('year_level', 'semester')
            for lvl in levels:
                yl = lvl['year_level']
                sem = lvl['semester']
                display = f"{('1st' if yl==1 else '2nd' if yl==2 else '3rd' if yl==3 else '4th')} Year, {('1st' if sem==1 else '2nd')} Semester"
                academic_levels.append({'year': yl, 'semester': sem, 'display': display})

            # Group courses by year_level and semester
            from collections import OrderedDict
            grouped = OrderedDict()
            for course in qs:
                key = f"{course.year_level}-{course.semester}"
                if key not in grouped:
                    display = f"{('1st' if course.year_level==1 else '2nd' if course.year_level==2 else '3rd' if course.year_level==3 else '4th')} Year, {('1st' if course.semester==1 else '2nd')} Semester"
                    grouped[key] = {
                        'display': display,
                        'courses': [],
                        'total_units': 0
                    }
                grouped[key]['courses'].append(course)
                grouped[key]['total_units'] += (course.credit_units or 0)

            grouped_courses = grouped
        except Curriculum.DoesNotExist:
            selected_curriculum = None

    # Try to get faculty profile for current user (may not exist for pure admin accounts)
    try:
        current_faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        current_faculty = None

    # Provide the context expected by the template
    context = {
        'user': request.user,
        'faculty': current_faculty,
        'curricula': curricula,
        'selected_curriculum': selected_curriculum,
        'selected_year': int(selected_year) if selected_year and selected_year.isdigit() else None,
        'selected_semester': int(selected_semester) if selected_semester and selected_semester.isdigit() else None,
        'grouped_courses': grouped_courses,
        'academic_levels': academic_levels,
    }

    return render(request, 'hello/course.html', context)

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_course(request):
    """Add new course"""
    if request.method == 'POST':
        try:
            curriculum_id = request.POST.get('curriculum')
            course_code = request.POST.get('course_code').strip().upper()
            descriptive_title = request.POST.get('descriptive_title').strip()
            laboratory_hours = int(request.POST.get('laboratory_hours', 0))
            lecture_hours = int(request.POST.get('lecture_hours', 0))
            credit_units = int(request.POST.get('credit_units', 0))
            year_level = int(request.POST.get('year_level'))
            semester = int(request.POST.get('semester'))
            
            curriculum = Curriculum.objects.get(id=curriculum_id)
            
            # Check if course code already exists in this curriculum
            if Course.objects.filter(course_code=course_code, curriculum=curriculum).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['A course with this code already exists in the selected curriculum.']
                })
            
            course = Course.objects.create(
                curriculum=curriculum,
                course_code=course_code,
                descriptive_title=descriptive_title,
                laboratory_hours=laboratory_hours,
                lecture_hours=lecture_hours,
                credit_units=credit_units,
                year_level=year_level,
                semester=semester
            )
            
            log_activity(
                user=request.user,
                action='add',
                entity_type='course',
                entity_name=f"{course.course_code} - {course.descriptive_title}",
                message=f'Added course: {course.course_code} - {course.descriptive_title}'
            )
            
            return JsonResponse({'success': True})
            
        except Curriculum.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Selected curriculum does not exist.']
            })
        except Exception as e:
            import traceback
            print(f"Error adding course: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [f'Error adding course: {str(e)}']
            })
    
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_course(request, course_id):
    """Edit existing course"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        try:
            curriculum_id = request.POST.get('curriculum')
            course_code = request.POST.get('course_code').strip().upper()
            descriptive_title = request.POST.get('descriptive_title').strip()
            laboratory_hours = int(request.POST.get('laboratory_hours', 0))
            lecture_hours = int(request.POST.get('lecture_hours', 0))
            credit_units = int(request.POST.get('credit_units', 0))
            year_level = int(request.POST.get('year_level'))
            semester = int(request.POST.get('semester'))
            
            curriculum = Curriculum.objects.get(id=curriculum_id)
            
            # Check if course code already exists in this curriculum (excluding current course)
            if Course.objects.filter(course_code=course_code, curriculum=curriculum).exclude(id=course_id).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['A course with this code already exists in the selected curriculum.']
                })
            
            course.curriculum = curriculum
            course.course_code = course_code
            course.descriptive_title = descriptive_title
            course.laboratory_hours = laboratory_hours
            course.lecture_hours = lecture_hours
            course.credit_units = credit_units
            course.year_level = year_level
            course.semester = semester
            
            course.save()
            
            log_activity(
                user=request.user,
                action='edit',
                entity_type='course',
                entity_name=f"{course.course_code} - {course.descriptive_title}",
                message=f'Edited course: {course.course_code} - {course.descriptive_title}'
            )
            
            return JsonResponse({'success': True})
            
        except Curriculum.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Selected curriculum does not exist.']
            })
        except Exception as e:
            import traceback
            print(f"Error editing course: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    # Return course data for editing
    return JsonResponse({
        'id': course.id,
        'curriculum': course.curriculum.id,
        'course_code': course.course_code,
        'descriptive_title': course.descriptive_title,
        'laboratory_hours': course.laboratory_hours,
        'lecture_hours': course.lecture_hours,
        'credit_units': course.credit_units,
        'year_level': course.year_level,
        'semester': course.semester,
        'color': course.color
    })

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_course(request, course_id):
    """Delete course"""
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        course_name = f"{course.course_code} - {course.descriptive_title}"
        
        # Check if course has schedules
        if course.schedules.exists():
            return JsonResponse({
                'success': False,
                'errors': ['Cannot delete course with existing schedules. Delete schedules first.']
            })
        
        course.delete()
        
        log_activity(
            user=request.user,
            action='delete',
            entity_type='course',
            entity_name=course_name,
            message=f'Deleted course: {course_name}'
        )
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# ===== CURRICULUM VIEWS =====

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_curriculum(request):
    """Add new curriculum"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name').strip()
            year = int(request.POST.get('year'))
            
            # Check if curriculum already exists
            if Curriculum.objects.filter(name=name, year=year).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['A curriculum with this name and year already exists.']
                })
            
            curriculum = Curriculum.objects.create(
                name=name,
                year=year
            )
            
            log_activity(
                user=request.user,
                action='add',
                entity_type='curriculum',
                entity_name=f"{curriculum.name} ({curriculum.year})",
                message=f'Added curriculum: {curriculum.name} ({curriculum.year})'
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            import traceback
            print(f"Error adding curriculum: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [f'Error adding curriculum: {str(e)}']
            })
    
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_curriculum(request, curriculum_id):
    """Edit existing curriculum"""
    curriculum = get_object_or_404(Curriculum, id=curriculum_id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name').strip()
            year = int(request.POST.get('year'))
            
            # Check if curriculum with new name/year already exists (excluding current)
            if Curriculum.objects.filter(name=name, year=year).exclude(id=curriculum_id).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['A curriculum with this name and year already exists.']
                })
            
            curriculum.name = name
            curriculum.year = year
            curriculum.save()
            
            log_activity(
                user=request.user,
                action='edit',
                entity_type='curriculum',
                entity_name=f"{curriculum.name} ({curriculum.year})",
                message=f'Edited curriculum: {curriculum.name} ({curriculum.year})'
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            import traceback
            print(f"Error editing curriculum: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    # Return curriculum data for editing
    return JsonResponse({
        'id': curriculum.id,
        'name': curriculum.name,
        'year': curriculum.year
    })

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_curriculum(request, curriculum_id):
    """Delete curriculum"""
    if request.method == 'POST':
        curriculum = get_object_or_404(Curriculum, id=curriculum_id)
        curriculum_name = f"{curriculum.name} ({curriculum.year})"
        
        # Check if curriculum has courses
        if curriculum.courses.exists():
            return JsonResponse({
                'success': False,
                'errors': ['Cannot delete curriculum with existing courses. Delete courses first.']
            })
        
        # Check if curriculum has sections
        if curriculum.sections.exists():
            return JsonResponse({
                'success': False,
                'errors': ['Cannot delete curriculum with existing sections. Delete sections first.']
            })
        
        curriculum.delete()
        
        log_activity(
            user=request.user,
            action='delete',
            entity_type='curriculum',
            entity_name=curriculum_name,
            message=f'Deleted curriculum: {curriculum_name}'
        )
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def edit_schedule(request, schedule_id):
    """Edit existing schedule entry"""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    if request.method == 'POST':
        try:
            course_id = request.POST.get('course')
            faculty_id = request.POST.get('faculty')
            room_id = request.POST.get('room')
            day = request.POST.get('day')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            
            course = Course.objects.get(id=course_id)
            faculty = Faculty.objects.get(id=faculty_id) if faculty_id else None
            room = Room.objects.get(id=room_id) if room_id else None
            
            schedule.course = course
            schedule.faculty = faculty
            schedule.room = room
            schedule.day = int(day)
            schedule.start_time = start_time
            schedule.end_time = end_time
            # Quick server-side enforcement of allowed window (07:30 - 21:30)
            try:
                def _tmin(tstr):
                    h, m = map(int, tstr.split(':'))
                    return h * 60 + m

                min_allowed = 7 * 60 + 30
                max_allowed = 21 * 60 + 30
                if start_time and end_time:
                    smin = _tmin(start_time)
                    emin = _tmin(end_time)
                    if smin < min_allowed or emin > max_allowed:
                        return JsonResponse({
                            'success': False,
                            'errors': [f'Schedule times must be within 07:30 and 21:30. Received {start_time} - {end_time}']
                        })
            except Exception:
                pass

            schedule.full_clean()
            schedule.save()
            
            log_activity(
                user=request.user,
                action='edit',
                entity_type='schedule',
                entity_name=f"{course.course_code} - {schedule.section.name}",
                message=f'Edited schedule: {course.course_code} for {schedule.section.name}'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Schedule updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    # Return schedule data for editing
    return JsonResponse({
        'id': schedule.id,
        'course': schedule.course.id,
        'faculty': schedule.faculty.id if schedule.faculty else '',
        'room': schedule.room.id if schedule.room else '',
        'day': schedule.day,
        'start_time': schedule.start_time,
        'end_time': schedule.end_time
    })


@login_required(login_url='admin_login')
def save_account_settings(request):
    """Handle account settings update for logged-in user (admin or faculty)"""
    print(f"DEBUG: save_account_settings called with method {request.method}")
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Only POST requests are allowed'
        }, status=400)
    
    print(f"DEBUG: Starting save_account_settings for user {request.user.username}")
    try:
        # Try to get the faculty profile, but it's optional (for admin users)
        try:
            faculty = Faculty.objects.get(user=request.user)
        except Faculty.DoesNotExist:
            faculty = None
            print(f"DEBUG: No Faculty profile found for user {request.user.username} (admin user)")
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error accessing user profile: {str(e)}'
        }, status=500)
    
    # Get form data
    first_name = request.POST.get('firstName', '').strip()
    last_name = request.POST.get('lastName', '').strip()
    email = request.POST.get('email', '').strip()
    gender = request.POST.get('gender', '').strip()
    current_password = request.POST.get('currentPassword', '')
    new_password = request.POST.get('newPassword', '')
    profile_picture = request.FILES.get('profilePicture', None)
    delete_profile_pic = request.POST.get('deleteProfilePic', '').lower() == 'true'
    
    print(f"DEBUG: Form data received - new_password='{new_password}', current_password='{current_password}'")
    print(f"DEBUG: new_password type: {type(new_password)}, value: '{new_password}', len: {len(new_password) if new_password else 0}")
    
    # Validate required fields
    errors = []
    
    if not first_name:
        errors.append('First name is required')
    if not last_name:
        errors.append('Last name is required')
    if not email:
        errors.append('Email is required')
    if gender and gender not in ['M', 'F']:
        errors.append('Invalid gender selection')
    
    # Validate email format and uniqueness
    if email:
        # Check if email is unique (excluding current user's email)
        email_exists = User.objects.filter(email=email).exclude(id=request.user.id).exists()
        if not email_exists and faculty:
            email_exists = Faculty.objects.filter(email=email).exclude(id=faculty.id).exists()
        
        if email_exists:
            errors.append('This email is already in use')
        # Basic email validation
        if '@' not in email:
            errors.append('Invalid email format')
    
    # Check if password change is attempted
    # Rule: if current_password is provided, new_password must also be provided
    if current_password and not new_password:
        errors.append('New password is required when providing current password')
    
    print(f"DEBUG: new_password='{new_password}', current_password='{current_password}'")
    
    if new_password is not None and new_password != '':
        # Normalize password (trim whitespace)
        new_password = new_password.strip()
        print(f"DEBUG: After strip, new_password='{new_password}', len={len(new_password)}")
        
        # First: verify current password is correct BEFORE validating new password strength
        if not current_password:
            errors.append('Current password is required to set a new password')
        elif not request.user.check_password(current_password):
            errors.append('Current password is incorrect')
            print(f"DEBUG: Current password check failed for user {request.user.username}")
        else:
            print(f"DEBUG: Current password verified for user {request.user.username}")
        
        # Only validate new password strength if current password is correct
        if not errors:  # No errors from current password check
            print(f"DEBUG: Validating new password strength...")
            password_errors = []

            # Check minimum length (at least 8 characters)
            if len(new_password) < 8:
                password_errors.append('at least 8 characters long')
                print(f"DEBUG: Length check failed: {len(new_password)} < 8")

            # Check for at least one uppercase letter
            if not any(c.isupper() for c in new_password):
                password_errors.append('at least one uppercase letter (A-Z)')
                print(f"DEBUG: Uppercase check failed")

            # Check for at least one allowed special character (use the same set as UI)
            allowed_specials = set('!@#$%^&*')
            if not any(c in allowed_specials for c in new_password):
                password_errors.append('at least one special character (!@#$%^&*)')
                print(f"DEBUG: Special char check failed")

            if password_errors:
                errors.append('New password must have: ' + ', '.join(password_errors))
                print(f"DEBUG: Password errors added: {errors}")
    
    # Return errors if any
    if errors:
        print(f"DEBUG: Returning error response with status 400: {errors}")
        return JsonResponse({
            'success': False,
            'errors': errors
        }, status=400)
    
    try:
        # Update faculty profile if it exists
        if faculty:
            if first_name:
                faculty.first_name = first_name
            if last_name:
                faculty.last_name = last_name
            if email:
                faculty.email = email
            if gender:
                faculty.gender = gender
            
            faculty.save()
        
        # Always update user profile
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        
        # Update password if provided
        if new_password:
            print(f"DEBUG: Setting password for {request.user.username} to new value: '{new_password}'")
            print(f"DEBUG: Before set_password - user.password hash: {request.user.password}")
            request.user.set_password(new_password)
            print(f"DEBUG: After set_password - user.password hash: {request.user.password}")
        else:
            print(f"DEBUG: No password change (new_password is empty)")
        
        print(f"DEBUG: About to save user {request.user.username}")
        request.user.save()
        # If password was changed, update the session auth hash so the user isn't logged out
        if new_password:
            try:
                update_session_auth_hash(request, request.user)
                print(f"DEBUG: Session auth hash updated for user {request.user.username}")
            except Exception as e:
                print(f"DEBUG: Failed to update session auth hash: {e}")
        print(f"DEBUG: User {request.user.username} saved successfully")
        
        # Verify it was actually saved by re-fetching from database
        refreshed_user = User.objects.get(pk=request.user.pk)
        print(f"DEBUG: Refreshed user from DB - password hash: {refreshed_user.password}")
        print(f"DEBUG: Can refresh user authenticate with new password? {refreshed_user.check_password(new_password)}")
        
        # Handle delete request or profile picture upload (only for faculty)
        if faculty:
            # If user requested deletion, delete persisted profile picture
            if delete_profile_pic:
                print(f"DEBUG: User {request.user.username} requested to delete profile picture")
                if faculty.profile_picture:
                    faculty.profile_picture.delete(save=False)
                    faculty.profile_picture = None
                    faculty.save()
                    print(f"DEBUG: Profile picture deleted for {request.user.username}")

            # Handle profile picture upload (takes precedence if a file was provided)
            elif profile_picture:
                # Validate file type
                allowed_types = ['image/jpeg', 'image/png']
                if profile_picture.content_type not in allowed_types:
                    return JsonResponse({
                        'success': False,
                        'errors': ['Only PNG and JPEG images are allowed']
                    }, status=400)
                
                # Validate file size (15MB)
                if profile_picture.size > 15 * 1024 * 1024:
                    return JsonResponse({
                        'success': False,
                        'errors': ['File size must be under 15MB']
                    }, status=400)
                
                # Delete old profile picture if it exists
                if faculty.profile_picture:
                    faculty.profile_picture.delete()
                
                # Save new profile picture
                faculty.profile_picture = profile_picture
                faculty.save()

        messages.success(request, 'Account settings saved successfully!')

        return JsonResponse({
            'success': True,
            'message': 'Account settings saved successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': [f'Error saving account settings: {str(e)}']
        }, status=500)
    if errors:
        print(f"DEBUG: Returning error response with status 400: {errors}")
        return JsonResponse({
            'success': False,
            'errors': errors
        }, status=400)
    
    try:
        # Update faculty profile
        if first_name:
            faculty.first_name = first_name
        if last_name:
            faculty.last_name = last_name
        if email:
            faculty.email = email
        if gender:
            faculty.gender = gender
        
        faculty.save()
        
        # Update user profile
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        
        # Update password if provided
        if new_password:
            print(f"DEBUG: Setting password for {request.user.username} to new value: '{new_password}'")
            print(f"DEBUG: Before set_password - user.password hash: {request.user.password}")
            request.user.set_password(new_password)
            print(f"DEBUG: After set_password - user.password hash: {request.user.password}")
        else:
            print(f"DEBUG: No password change (new_password is empty)")
        
        print(f"DEBUG: About to save user {request.user.username}")
        request.user.save()
        # If password was changed, update the session auth hash so the user isn't logged out
        if new_password:
            try:
                update_session_auth_hash(request, request.user)
                print(f"DEBUG: Session auth hash updated for user {request.user.username}")
            except Exception as e:
                print(f"DEBUG: Failed to update session auth hash: {e}")
        print(f"DEBUG: User {request.user.username} saved successfully")
        
        # Verify it was actually saved by re-fetching from database
        refreshed_user = User.objects.get(pk=request.user.pk)
        print(f"DEBUG: Refreshed user from DB - password hash: {refreshed_user.password}")
        print(f"DEBUG: Can refresh user authenticate with new password? {refreshed_user.check_password(new_password)}")
        
        # Handle profile picture upload or delete
        if faculty:
            # Check if user wants to delete profile picture
            if delete_profile_pic:
                print(f"DEBUG: User {request.user.username} requested to delete profile picture")
                if faculty.profile_picture:
                    faculty.profile_picture.delete()
                    faculty.profile_picture = None
                    faculty.save()
                    print(f"DEBUG: Profile picture deleted for {request.user.username}")
            
            # Handle profile picture upload
            elif profile_picture:
                print(f"DEBUG: User {request.user.username} uploading new profile picture")
                # Validate file type
                allowed_types = ['image/jpeg', 'image/png']
                if profile_picture.content_type not in allowed_types:
                    return JsonResponse({
                        'success': False,
                        'errors': ['Only PNG and JPEG images are allowed']
                    }, status=400)
                
                # Validate file size (15MB)
                if profile_picture.size > 15 * 1024 * 1024:
                    return JsonResponse({
                        'success': False,
                        'errors': ['File size must be under 15MB']
                    }, status=400)
                
                # Delete old profile picture if it exists
                if faculty.profile_picture:
                    faculty.profile_picture.delete()
                
                # Save new profile picture
                faculty.profile_picture = profile_picture
                faculty.save()
                print(f"DEBUG: New profile picture saved for {request.user.username}")
        
        messages.success(request, 'Account settings saved successfully!')
        
        return JsonResponse({
            'success': True,
            'message': 'Account settings saved successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': [f'Error saving account settings: {str(e)}']
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_faculty_data(request):
    """API endpoint to fetch current user's faculty data for the Android App"""
    try:
        faculty = Faculty.objects.get(user=request.user)
        
        # Build full URL so the app can find the image (http://10.0.2.2:8000/media/...)
        profile_pic_url = None
        if faculty.profile_picture:
            profile_pic_url = request.build_absolute_uri(faculty.profile_picture.url)

        return Response({
            'first_name': faculty.first_name,
            'last_name': faculty.last_name,
            'email': faculty.email,
            'gender': faculty.gender or '',
            'profile_picture_url': profile_pic_url,
        }, status=status.HTTP_200_OK)

    except Faculty.DoesNotExist:
        return Response({
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'gender': '',
            'profile_picture_url': None,
        }, status=status.HTTP_200_OK)

def api_password_reset(request):
    """API endpoint to send password reset email"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            email = data.get('email')

            if not email:
                return JsonResponse({'error': 'Email is required'}, status=400)

            # Check if user exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Don't reveal if email exists or not for security
                return JsonResponse({'message': 'If an account with this email exists, a password reset link has been sent.'})

            # Generate password reset token
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Build reset URL
            from django.urls import reverse
            reset_url = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )

            # Send email
            subject = 'Password Reset Request for ASSIST'
            message = f'''Hello {user.first_name},

You have requested to reset your password for the ASSIST system.

Please click the following link to reset your password:
{reset_url}

This link will expire in 7 days.

If you did not request this password reset, please ignore this email.

Best regards,
ASSIST Administration Team'''

            try:
                email_message = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email],
                )
                email_message.send(fail_silently=False)
            except Exception as e:
                print(f"Error sending password reset email: {str(e)}")
                return JsonResponse({'error': 'Failed to send email'}, status=500)

            return JsonResponse({'message': 'If an account with this email exists, a password reset link has been sent.'})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Error in api_password_reset: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

def api_password_reset_confirm(request):
    """API endpoint to confirm password reset and set new password"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            uid = data.get('uid')
            token = data.get('token')
            new_password = data.get('new_password')

            if not all([uid, token, new_password]):
                return JsonResponse({'error': 'uid, token, and new_password are required'}, status=400)

            # Decode uid
            from django.utils.http import urlsafe_base64_decode
            from django.utils.encoding import force_str
            from django.contrib.auth.tokens import default_token_generator

            try:
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return JsonResponse({'error': 'Invalid reset link'}, status=400)

            # Check token
            if not default_token_generator.check_token(user, token):
                return JsonResponse({'error': 'Invalid or expired reset token'}, status=400)

            # Validate new password
            from django.contrib.auth.password_validation import validate_password
            try:
                validate_password(new_password, user)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)

            # Set new password
            user.set_password(new_password)
            user.save()

            return JsonResponse({'message': 'Password has been reset successfully'})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Error in api_password_reset_confirm: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_resources(request):
    """API endpoint to get available faculty and rooms for a given time slot"""
    try:
        # Get data from request.query_params (standard for GET in DRF)
        day = request.query_params.get('day')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')

        if not all([day, start_time, end_time]):
            return Response({'error': 'day, start_time, and end_time are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Convert day name to integer if needed
        day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5}
        
        try:
            day_val = day_mapping[day] if day in day_mapping else int(day)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid day format'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter logic
        all_faculty = Faculty.objects.all().order_by('last_name', 'first_name')
        all_rooms = Room.objects.all().order_by('campus', 'room_number')

        available_faculty = []
        for f in all_faculty:
            if not Schedule.objects.filter(faculty=f, day=day_val, start_time__lt=end_time, end_time__gt=start_time).exists():
                available_faculty.append({'id': f.id, 'name': f"{f.last_name}, {f.first_name}", 'email': f.email})

        available_rooms = []
        for r in all_rooms:
            if not Schedule.objects.filter(room=r, day=day_val, start_time__lt=end_time, end_time__gt=start_time).exists():
                available_rooms.append({
                    'id': r.id, 
                    'name': f"{r.get_room_type_display()}: {'A' if r.campus == 'arlegui' else 'C'}-{r.room_number}",
                    'capacity': r.capacity
                })

        return Response({
            'success': True,
            'faculty': available_faculty,
            'rooms': available_rooms
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_stats(request):
    data = {
        "faculty_count": Faculty.objects.count(),
        "section_count": Section.objects.count()
    }
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_curriculums(request):
    curriculums = Curriculum.objects.all().order_by('-year')
    data = [{"id": c.id, "name": c.name, "year": c.year} for c in curriculums]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sections(request):
    sections = Section.objects.all()
    data = [{
        "id": s.id, 
        "name": s.name, 
        "year_level": s.year_level, 
        "semester": s.semester, 
        "status": s.status,
        "curriculum": s.curriculum.id
    } for s in sections]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_courses(request):
    # Get filters from URL (e.g. ?curriculum=1)
    curr_id = request.query_params.get('curriculum')
    courses = Course.objects.all()
    if curr_id:
        courses = courses.filter(curriculum_id=curr_id)
        
    data = [{
        "id": c.id,
        "course_code": c.course_code,
        "descriptive_title": c.descriptive_title,
        "lecture_hours": c.lecture_hours,
        "laboratory_hours": c.laboratory_hours,
        "credit_units": c.credit_units,
        "year_level": c.year_level,
        "semester": c.semester,
        "color": c.color or "#000000"
    } for c in courses]
    return Response(data)