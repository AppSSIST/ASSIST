from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Dashboards
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/schedule/', views.staff_schedule, name='staff_schedule'),
    path('staff/schedule/print/', views.staff_schedule_print, name='staff_schedule_print'),
    path('staff/account/save/', views.save_account_settings, name='save_account_settings'),
    
    # Sections
    path('admin/section/', views.section_view, name='section_view'),  
    path('admin/section/add/', views.add_section, name='add_section'),
    path('admin/section/edit/<int:section_id>/', views.edit_section, name='edit_section'),
    path('admin/section/delete/<int:section_id>/', views.delete_section, name='delete_section'),
    path('admin/section/<int:section_id>/schedule-data/', views.get_section_schedule, name='get_section_schedule'),
    path('admin/section/<int:section_id>/delete-schedules/', views.delete_section_schedules, name='delete_section_schedules'),
    path('admin/section/<int:section_id>/toggle-status/', views.toggle_section_status, name='toggle_section_status'),
    
    # Courses
    path('admin/course/', views.course_view, name='course_view'),
    path('admin/course/add/', views.add_course, name='add_course'),
    path('admin/course/edit/<int:course_id>/', views.edit_course, name='edit_course'),
    path('admin/course/delete/<int:course_id>/', views.delete_course, name='delete_course'),
    
    # Schedules
    path('admin/schedule/', views.schedule_view, name='schedule_view'),
    path('admin/section/<int:section_id>/schedule/print/', views.admin_section_schedule_print, name='admin_section_schedule_print'),
    path('admin/faculty/<int:faculty_id>/schedule/print/', views.admin_faculty_schedule_print, name='admin_faculty_schedule_print'),
    path('admin/room/<int:room_id>/schedule/print/', views.admin_room_schedule_print, name='admin_room_schedule_print'),
    path('admin/schedule/add/', views.add_schedule, name='add_schedule'),
    path('admin/schedule/delete/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),
    path('admin/schedule/edit/new/', views.edit_schedule, {'schedule_id': None}, name='edit_schedule_new'),
    path('admin/schedule/edit/<int:schedule_id>/', views.edit_schedule, name='edit_schedule'),
    
    # Curriculum operations
    path('admin/curriculum/add/', views.add_curriculum, name='add_curriculum'),
    path('admin/curriculum/delete/<int:curriculum_id>/', views.delete_curriculum, name='delete_curriculum'),
    path('curriculum/edit/<int:curriculum_id>/', views.edit_curriculum, name='edit_curriculum'),
    
    # Faculty CRUD operations
    path('admin/faculty/', views.faculty_view, name='faculty_view'),
    path('admin/faculty/add/', views.add_faculty, name='add_faculty'),
    path('admin/faculty/edit/<int:faculty_id>/', views.edit_faculty, name='edit_faculty'),
    path('admin/faculty/delete/<int:faculty_id>/', views.delete_faculty, name='delete_faculty'),
    path('admin/faculty/<int:faculty_id>/schedule-data/', views.get_faculty_schedule, name='get_faculty_schedule'),

    # Room CRUD operations 
    path('admin/room/', views.room_view, name='room_view'),
    path('admin/room/add/', views.add_room, name='add_room'),
    path('admin/room/edit/<int:room_id>/', views.edit_room, name='edit_room'),
    path('admin/room/delete/<int:room_id>/', views.delete_room, name='delete_room'),
    path('admin/room/<int:room_id>/schedule-data/', views.get_room_schedule, name='get_room_schedule'),

    # Auth
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('admin/password-reset/', 
         views.CustomPasswordResetView.as_view(
             template_name='hello/password_reset.html',
             email_template_name='hello/password_reset_email.html',
             success_url=reverse_lazy('password_reset_done')
         ), 
         name='password_reset'),
    path('admin/password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='hello/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('admin/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='hello/password_reset_confirm.html',
             success_url=reverse_lazy('password_reset_complete')
         ),
         name='password_reset_confirm'),
    path('admin/reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='hello/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    
    # API endpoints
    # JWT token endpoints for mobile clients
    path('api/auth/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/password-reset/', views.api_password_reset, name='api_password_reset'),
    path('api/auth/password-reset/confirm/', views.api_password_reset_confirm, name='api_password_reset_confirm'),
    path('api/schedules/available-resources/', views.get_available_resources, name='get_available_resources'),
    path('api/schedule/available-resources/', views.get_available_resources, name='schedule_available_resources'),  # Alias for mobile app
    path('api/user-faculty-data/', views.get_user_faculty_data, name='get_user_faculty_data'),
    path('api/user-profile-update/', views.api_user_profile_update, name='api_user_profile_update'),

    #api for mobile app to fetch data for schedule generation
    path('api/dashboard-stats/', views.get_dashboard_stats, name='api_dashboard_stats'),
    path('api/curriculums/', views.get_curriculums, name='api_curriculums'),
    path('api/sections/', views.get_sections, name='api_sections'),
    path('api/rooms/', views.get_rooms, name='api_rooms'),
    path('api/faculty-list/', views.get_faculty_list, name='api_faculty_list'),
    path('api/my-schedule/', views.api_my_schedule, name='api_my_schedule'),
    path('api/faculty/<int:faculty_id>/schedule-data/', views.api_faculty_schedule, name='api_faculty_schedule'),
    path('api/section/<int:section_id>/schedule-data/', views.api_section_schedule, name='api_section_schedule'),
    path('api/room/<int:room_id>/schedule-data/', views.api_room_schedule, name='api_room_schedule'),
    path('api/courses/', views.get_courses, name='api_courses'),
    path('api/courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('api/courses/add/', views.api_add_course, name='api_add_course'),
    
    # API endpoints for adding data
    path('api/room/add/', views.api_add_room, name='api_add_room'),
    path('api/section/add/', views.api_add_section, name='api_add_section'),
    path('api/faculty/add/', views.api_add_faculty, name='api_add_faculty'),
    
    # Mobile app schedule print API endpoints
    path('api/schedule/staff/html/', views.staff_schedule_html, name='api_staff_schedule_html'),
    path('api/schedule/staff/pdf/', views.staff_schedule_pdf, name='api_staff_schedule_pdf'),
    path('api/schedule/faculty/html/', views.faculty_schedule_html, name='api_faculty_schedule_html'),
    path('api/schedule/faculty/pdf/', views.faculty_schedule_pdf, name='api_faculty_schedule_pdf'),
    path('api/schedule/faculty/<int:faculty_id>/html/', views.api_faculty_schedule_html, name='api_faculty_schedule_html_id'),
    path('api/schedule/faculty/<int:faculty_id>/pdf/', views.api_faculty_schedule_pdf, name='api_faculty_schedule_pdf_id'),
    path('api/schedule/section/<int:section_id>/html/', views.api_section_schedule_html, name='api_section_schedule_html'),
    path('api/schedule/section/<int:section_id>/pdf/', views.api_section_schedule_pdf, name='api_section_schedule_pdf'),
    path('api/schedule/room/<int:room_id>/html/', views.api_room_schedule_html, name='api_room_schedule_html'),
    path('api/schedule/room/<int:room_id>/pdf/', views.api_room_schedule_pdf, name='api_room_schedule_pdf'),
    
    # API endpoint for schedule operations
    path('api/schedules/', views.api_schedules, name='api_schedules'),
    path('api/schedule/', views.api_schedules, name='api_schedule'),  # Alias for mobile app (singular)
    
    # Mobile CRUD API endpoints for Faculty
    path('api/faculty/<int:faculty_id>/', views.api_edit_delete_faculty, name='api_edit_delete_faculty'),
    
    # Mobile CRUD API endpoints for Course
    path('api/courses/<int:course_id>/edit/', views.api_edit_delete_course, name='api_edit_delete_course'),
    
    # Mobile CRUD API endpoints for Room
    path('api/rooms/<int:room_id>/', views.api_edit_delete_room, name='api_edit_delete_room'),
    
    # Mobile CRUD API endpoints for Section
    path('api/sections/<int:section_id>/', views.api_edit_delete_section, name='api_edit_delete_section'),
    
    # Mobile CRUD API endpoints for Schedule
    path('api/schedules/<int:schedule_id>/', views.api_edit_delete_schedule, name='api_edit_delete_schedule'),
]

