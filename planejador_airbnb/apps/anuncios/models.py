from django.db import models

from apps.agendamento.models import Agendamento


class Anuncio(models.Model):
    agendamento = models.ForeignKey(
        Agendamento,
        on_delete=models.CASCADE,
        related_name='anuncios'
    )
    titulo = models.CharField(max_length=255, verbose_name="Título")
    link = models.URLField(max_length=1024, verbose_name="Link")

    def __str__(self):
        return f"{self.titulo} - {self.agendamento.imovel.tipo_acomodacao}"

    class Meta:
        db_table = 'anuncio'
        verbose_name = "Anúncio"
        verbose_name_plural = "Anúncios"