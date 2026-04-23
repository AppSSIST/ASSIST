from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
import random
import re
from django.core.exceptions import ValidationError

class Curriculum(models.Model):
    name = models.CharField(max_length=100)
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-year']
        unique_together = ['name', 'year']
    
    def __str__(self):
        return f"{self.name} ({self.year})"

class Course(models.Model):
    YEAR_CHOICES = [
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
    ]
    
    SEMESTER_CHOICES = [
        (1, '1st Semester'),
        (2, '2nd Semester'),
    ]
    
    # Predefined color palette for courses
    COLOR_PALETTE = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DFE6E9', '#74B9FF', '#A29BFE', '#FD79A8', '#FDCB6E',
        '#6C5CE7', '#00B894', '#E17055', '#0984E3', '#00CEC9',
        '#B2BEC3', '#FF7675', '#55EFC4', '#FAB1A0', '#A29BFE',
    ]
    
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='courses')
    course_code = models.CharField(max_length=20)
    descriptive_title = models.CharField(max_length=200)
    laboratory_hours = models.IntegerField(default=0)
    lecture_hours = models.IntegerField(default=0)
    credit_units = models.IntegerField(default=0)
    year_level = models.IntegerField(choices=YEAR_CHOICES)
    semester = models.IntegerField(choices=SEMESTER_CHOICES)
    color = models.CharField(max_length=7, default='#FFA726')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['year_level', 'semester', 'course_code']
        unique_together = ['curriculum', 'course_code']
    
    def save(self, *args, **kwargs):
        """Auto-assign a unique color if not set"""
        if not self.color or self.color == '#FFA726':
            existing_colors = Course.objects.filter(
                curriculum=self.curriculum
            ).exclude(id=self.id).values_list('color', flat=True)
            
            available_colors = [c for c in self.COLOR_PALETTE if c not in existing_colors]
            
            if available_colors:
                self.color = random.choice(available_colors)
            else:
                self.color = random.choice(self.COLOR_PALETTE)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.course_code} - {self.descriptive_title}"
    
    def get_year_semester_display(self):
        year = dict(self.YEAR_CHOICES)[self.year_level]
        semester = dict(self.SEMESTER_CHOICES)[self.semester]
        return f"{year}, {semester}"

class Faculty(models.Model):
    """Model for faculty members"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    EMPLOYMENT_STATUS_CHOICES = [
        ('full_time', 'Full-Time'),
        ('part_time', 'Part-Time'),
        ('contractual', 'Contractual'),
    ]
    
    PROFESSIONAL_TITLE_CHOICES = [
        ('', '-- Select Title --'),
        ('Dr.', 'Dr. (Doctor)'),
        ('Engr.', 'Engr. (Engineer)'),
    ]
    
    SPECIALIZATION_CHOICES = [
        ('computer_networking', 'Computer Networking'),
        ('digital_electronics', 'Digital Electronics'),
        ('software_dev', 'Software Development'),
        ('machine_learning', 'Machine Learning'),
        ('cyber_security', 'Cyber Security'),
        ('system_administration', 'System Administration'),
        ('computer_architecture', 'Computer Architecture'),
        ('embedded_systems', 'Embedded Systems'),
        ('other', 'Other'),
    ]
    
    HIGHEST_DEGREE_CHOICES = [
        ('', '-- Select Degree --'),
        ('Bachelor\'s Degree', 'Bachelor\'s Degree'),
        ('Master\'s Degree', 'Master\'s Degree'),
        ('Doctoral Degree', 'Doctoral Degree'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='faculty_profile')
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    professional_title = models.CharField(max_length=20, choices=PROFESSIONAL_TITLE_CHOICES, blank=True, default='')
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default='full_time')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True, verbose_name='Profile Picture')
    highest_degree = models.CharField(max_length=100, choices=HIGHEST_DEGREE_CHOICES, blank=True, default='')
    prc_licensed = models.BooleanField(default=False, verbose_name='PRC Licensed (Qualified)')
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES, blank=True, default='')
    department = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name_plural = 'Faculty'
    
    def __str__(self):
        if self.middle_name:
            return f"{self.last_name}, {self.first_name} {self.middle_name}"
        return f"{self.last_name}, {self.first_name}"
    
    @property
    def total_units(self):
        """Calculate total credit units from unique courses in schedules.

        If a faculty member has multiple schedule entries for the same course
        (for example, a 2-unit PE that meets two days), the course's credit
        units are counted only once.
        """
        # Get distinct course IDs assigned to this faculty via schedules
        unique_course_ids = self.schedules.values_list('course', flat=True).distinct()
        total = Course.objects.filter(id__in=unique_course_ids).aggregate(
            total=Sum('credit_units')
        )['total'] or 0
        return total
    
    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

class Section(models.Model):
    """Model for class sections with naming convention CPE[year][semester]S[number]"""
    
    STATUS_CHOICES = [
        ('complete', 'Complete Schedule'),
        ('incomplete', 'No Schedule Yet'),
    ]
    
    name = models.CharField(max_length=50)
    year_level = models.IntegerField(choices=Course.YEAR_CHOICES)
    semester = models.IntegerField(choices=Course.SEMESTER_CHOICES)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='sections')
    max_students = models.IntegerField(default=40)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='incomplete')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['year_level', 'semester', 'name']
        unique_together = ['curriculum', 'name']
    
    def clean(self):
        """Validate section name format: CPE[year][semester]S[number]"""
        super().clean()
        
        pattern = r'^([A-Z]+)(\d)(\d)S(\d+)$'
        match = re.match(pattern, self.name)
        
        if not match:
            raise ValidationError({
                'name': 'Section name must follow format: CPE[year][semester]S[number]. Example: CPE11S1'
            })
        
        program, year_digit, sem_digit, section_num = match.groups()
        name_year = int(year_digit)
        name_sem = int(sem_digit)
        
        if name_year != self.year_level:
            raise ValidationError({
                'name': f'Section name year ({name_year}) must match year level ({self.year_level})'
            })
        
        if name_sem != self.semester:
            raise ValidationError({
                'name': f'Section name semester ({name_sem}) must match semester ({self.semester})'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def total_units(self):
        """Calculate total credit units from unique courses in schedules"""
        unique_course_ids = self.schedules.values_list('course', flat=True).distinct()
        total = Course.objects.filter(id__in=unique_course_ids).aggregate(
            total=Sum('credit_units')
        )['total'] or 0
        return total

class Room(models.Model):
    """Model for classrooms"""
    CAMPUS_CHOICES = [
        ('casal', 'Casal'),
        ('arlegui', 'Arlegui'),
    ]
    
    ROOM_TYPE_CHOICES = [
        ('lecture', 'Lecture'),
        ('laboratory', 'Laboratory'),
    ]
    
    name = models.CharField(max_length=100)
    room_number = models.CharField(max_length=20, default='000', blank=True)
    capacity = models.IntegerField(default=40)
    campus = models.CharField(max_length=20, choices=CAMPUS_CHOICES, default='casal')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='lecture')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['campus', 'room_number']
        # unique_together = ['campus', 'room_number']  # Comment this out temporarily
    
    def __str__(self):
        return f"{self.name} ({self.get_campus_display()})"

class Schedule(models.Model):
    """Model for course schedules with validation"""
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='schedules')
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules')
    day = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.CharField(max_length=5)
    end_time = models.CharField(max_length=5)
    duration = models.IntegerField(default=0, help_text="Duration in minutes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['day', 'start_time']
    
    def clean(self):
        """Validate course matches section's year/semester and check for time conflicts"""
        super().clean()
        
        if self.course.year_level != self.section.year_level:
            raise ValidationError(
                f'Cannot add {self.course.course_code} (Year {self.course.year_level}) '
                f'to {self.section.name} (Year {self.section.year_level})'
            )
        
        if self.course.semester != self.section.semester:
            raise ValidationError(
                f'Cannot add {self.course.course_code} (Semester {self.course.semester}) '
                f'to {self.section.name} (Semester {self.section.semester})'
            )
        
        if self.course.curriculum != self.section.curriculum:
            raise ValidationError(
                f'{self.course.course_code} curriculum does not match {self.section.name} curriculum'
            )

        # Enforce allowed schedule window: classes must fall within 07:30 - 21:30
        try:
            def _time_to_minutes(tstr):
                h, m = map(int, tstr.split(':'))
                return h * 60 + m

            if self.start_time and self.end_time:
                start_min = _time_to_minutes(self.start_time)
                end_min = _time_to_minutes(self.end_time)
                min_allowed = 7 * 60 + 30
                max_allowed = 21 * 60 + 30
                if start_min < min_allowed or end_min > max_allowed:
                    raise ValidationError(
                        f'Schedule times must be within 07:30 and 21:30. Received {self.start_time} - {self.end_time}'
                    )
        except Exception:
            # If parsing fails, let other validations handle it or surface later
            pass

        # Check for section time conflicts (same section, same day, overlapping times)
        section_conflicts = Schedule.objects.filter(
            section=self.section,
            day=self.day
        ).exclude(pk=self.pk)

        for conflict_schedule in section_conflicts:
            if self._times_overlap(self.start_time, self.end_time, conflict_schedule.start_time, conflict_schedule.end_time):
                raise ValidationError(
                    f'Section {self.section.name} has a time conflict on '
                    f'{dict(self.DAY_CHOICES)[self.day]} between {conflict_schedule.start_time} and {conflict_schedule.end_time} '
                    f'({conflict_schedule.course.course_code})'
                )

        # Check for faculty time conflicts (same faculty, same day, overlapping times)
        if self.faculty:
            faculty_conflicts = Schedule.objects.filter(
                faculty=self.faculty,
                day=self.day
            ).exclude(pk=self.pk)

            for conflict_schedule in faculty_conflicts:
                if self._times_overlap(self.start_time, self.end_time, conflict_schedule.start_time, conflict_schedule.end_time):
                    raise ValidationError(
                        f'Faculty {self.faculty.first_name} {self.faculty.last_name} has a time conflict on '
                        f'{dict(self.DAY_CHOICES)[self.day]} between {conflict_schedule.start_time} and {conflict_schedule.end_time}'
                    )

        # Check for room time conflicts (same room, same day, overlapping times)
        if self.room:
            room_conflicts = Schedule.objects.filter(
                room=self.room,
                day=self.day
            ).exclude(pk=self.pk)

            for conflict_schedule in room_conflicts:
                if self._times_overlap(self.start_time, self.end_time, conflict_schedule.start_time, conflict_schedule.end_time):
                    raise ValidationError(
                        f'Room {self.room.name} has a time conflict on '
                        f'{dict(self.DAY_CHOICES)[self.day]} between {conflict_schedule.start_time} and {conflict_schedule.end_time}'
                    )
    
    def _times_overlap(self, start1, end1, start2, end2):
        """Check if two time ranges overlap.
        Times are in HH:MM format (24-hour).
        Overlap occurs if: start1 < end2 AND start2 < end1
        """
        def time_to_minutes(time_str):
            h, m = map(int, time_str.split(':'))
            return h * 60 + m

        start1_min = time_to_minutes(start1)
        end1_min = time_to_minutes(end1)
        start2_min = time_to_minutes(start2)
        end2_min = time_to_minutes(end2)

        return start1_min < end2_min and start2_min < end1_min

    def save(self, *args, **kwargs):
        """Calculate duration and validate"""
        if self.start_time and self.end_time:
            start_hour, start_min = map(int, self.start_time.split(':'))
            end_hour, end_min = map(int, self.end_time.split(':'))
            self.duration = (end_hour * 60 + end_min) - (start_hour * 60 + start_min)
        # NOTE: Removed hard limit enforcement for faculty unit load (previously 25 units).
        # The system now allows assigning schedules that may exceed a fixed unit cap.
        # If you later want to re-enable a configurable limit, implement it as a
        # tunable setting and validate against that value here.
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        day_name = dict(self.DAY_CHOICES)[self.day]
        return f"{self.course.course_code} - {day_name} {self.start_time}-{self.end_time}"

class Activity(models.Model):
    """Model for tracking user activities"""
    ACTION_CHOICES = [
        ('add', 'Added'),
        ('edit', 'Edited'),
        ('delete', 'Deleted'),
    ]
    
    ENTITY_CHOICES = [
        ('course', 'Course'),
        ('curriculum', 'Curriculum'),
        ('faculty', 'Faculty'),
        ('section', 'Section'),
        ('room', 'Room'),
        ('schedule', 'Schedule'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=20, choices=ENTITY_CHOICES)
    entity_name = models.CharField(max_length=200)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Activities'
    
    def __str__(self):
        return f"{self.action} {self.entity_type}: {self.entity_name}"