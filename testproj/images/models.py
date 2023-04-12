from django.db import models


class Picture(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='images/%Y/%m/%d', null=True, blank=True)

    def __str__(self):
        return f'id={self.id}'
