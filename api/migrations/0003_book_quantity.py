# Generated by Django 4.1.1 on 2022-10-04 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_remove_cartitem_ordered_cartitem_cart_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="quantity",
            field=models.PositiveBigIntegerField(default=1),
        ),
    ]
