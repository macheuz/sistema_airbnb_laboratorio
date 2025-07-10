from django.db import models

from apps.imovel.models import Imovel


class Avaliacao(models.Model):
    imovel = models.ForeignKey(
        Imovel,
        on_delete=models.CASCADE,
        related_name='avaliacoes'
    )
    nota = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True
    )
    qtd_avaliacoes = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'avaliacao'
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"
        ordering = ['-nota']

    def __str__(self):
        return f"Avaliação de {self.nota} para o Imóvel ID {self.imovel.id}"