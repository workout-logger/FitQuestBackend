# Generated by Django 4.2.13 on 2024-12-29 01:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_customuser_coins'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='body_color',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(1, 'Color 1'), (2, 'Color 2'), (3, 'Color 3'), (4, 'Color 4'), (5, 'Color 5')], null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='eye_color',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(1, 'Eye Color 1'), (2, 'Eye Color 2'), (3, 'Eye Color 3'), (4, 'Eye Color 4'), (5, 'Eye Color 5')], null=True),
        ),
    ]