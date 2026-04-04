from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zipgrade', '0005_zipgradeexam_answer_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='subjectsplit',
            name='class_type',
            field=models.CharField(
                choices=[('all', 'All Classes'), ('ru', 'RU Classes Only'), ('kg', 'KG Classes Only')],
                default='all',
                help_text='Restrict this split to specific class types. "All" applies to everyone.',
                max_length=5,
                verbose_name='Class Type',
            ),
        ),
    ]
