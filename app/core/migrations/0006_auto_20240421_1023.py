# Generated by Django 3.2.20 on 2024-04-21 10:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_rename_ingridient_ingredient'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ingredient',
            name='recipes',
        ),
        migrations.AddField(
            model_name='recipe',
            name='ingredients',
            field=models.ManyToManyField(to='core.Ingredient'),
        ),
    ]