
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0003_auto_20250601_0258'),
    ]

    operations = [
        migrations.AddField(
            model_name='salarypredictionmodel',
            name='max_pipeline',
            field=models.BinaryField(blank=True, null=True, verbose_name='最高薪资预测模型'),
        ),
        migrations.AddField(
            model_name='salarypredictionmodel',
            name='min_pipeline',
            field=models.BinaryField(blank=True, null=True, verbose_name='最低薪资预测模型'),
        ),
    ]
