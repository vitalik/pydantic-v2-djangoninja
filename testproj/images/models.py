from django.db import models


class MockRel:
    def method(self):
        return 'mock rel'


class Picture(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='images/%Y/%m/%d', null=True, blank=True)
    type = models.CharField(
        max_length=20,
        choices=[(i, i.title()) for i in ['nature', 'animal', 'other']],
        default='other',
    )

    def __str__(self):
        return f'id={self.id}'

    rel = MockRel()
