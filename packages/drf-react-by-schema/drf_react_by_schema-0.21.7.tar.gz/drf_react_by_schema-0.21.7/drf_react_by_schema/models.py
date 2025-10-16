from django.db import models
from django.utils.text import slugify

from . import CharField


class GenericSimpleModel(models.Model):
    filter_and_search_field = "nome"
    nome = CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["slug"]

    def __str__(self):
        return f"{self.nome}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.nome}")

            # If slug already exists, put a suffix until it becomes unique
            if self.__class__.objects.filter(slug=self.slug).count() > 0:
                i = 2
                while True:
                    slug = f"{self.slug}-{i}"
                    if self.__class__.objects.filter(slug=slug).count() > 0:
                        i += 1
                    else:
                        self.slug = slug
                        break

        super().save(*args, **kwargs)
