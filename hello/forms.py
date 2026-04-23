from django import forms
from .models import Course, Curriculum, Faculty

class FacultyProfileForm(forms.ModelForm):
    """Form for faculty to update their profile information"""
    class Meta:
        model = Faculty
        fields = ['first_name', 'middle_name', 'last_name', 'email', 'gender', 'professional_title', 'highest_degree', 'specialization', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'professional_title': forms.Select(attrs={'class': 'form-control'}),
            'highest_degree': forms.Select(attrs={'class': 'form-control'}),
            'specialization': forms.Select(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/png,image/jpeg'}),
        }

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['curriculum', 'course_code', 'descriptive_title', 'laboratory_hours', 
                  'lecture_hours', 'credit_units', 'year_level', 'semester']
        widgets = {
            'curriculum': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'course_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., CPE 001',
                'required': True
            }),
            'descriptive_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Software Design',
                'required': True
            }),
            'laboratory_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'required': True
            }),
            'lecture_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'required': True
            }),
            'credit_units': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'required': True
            }),
            'year_level': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'semester': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
        }

class CurriculumForm(forms.ModelForm):
    class Meta:
        model = Curriculum
        fields = ['name', 'year']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., BSCPE Curriculum',
                'required': True
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2025',
                'min': '2000',
                'max': '2100',
                'required': True
            }),
        }