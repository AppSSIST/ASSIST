# Generated migration to fix professional title and degree choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hello', '0014_faculty_middle_name_faculty_professional_title_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='faculty',
            name='professional_title',
            field=models.CharField(blank=True, choices=[('', '-- Select Title --'), ('Dr.', 'Dr. (Doctor)'), ('Engr.', 'Engr. (Engineer)')], default='', max_length=20),
        ),
        migrations.AlterField(
            model_name='faculty',
            name='highest_degree',
            field=models.CharField(blank=True, choices=[('', '-- Select Degree --'), ('Bachelor\'s Degree', 'Bachelor\'s Degree'), ('Master\'s Degree', 'Master\'s Degree'), ('Doctoral Degree', 'Doctoral Degree')], default='', max_length=100),
        ),
    ]
