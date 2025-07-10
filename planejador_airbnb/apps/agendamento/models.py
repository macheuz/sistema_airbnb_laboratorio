from django.db import models

from apps.imovel.models import Imovel


class Agendamento(models.Model):
    imovel = models.ForeignKey(
        Imovel,
        on_delete=models.CASCADE,
        related_name='agendamentos'
    )
    data_checkin = models.DateField()
    data_checkout = models.DateField(null=True, blank=True)
    preco_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preco_por_dia = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hospedes = models.PositiveIntegerField()
    link = models.URLField(max_length=1024, verbose_name="Link")

    class Meta:
        db_table = 'agendamento'
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ['data_checkin']

    def __str__(self):
        return f"Agendamento para Imóvel ID {self.imovel.id}: {self.data_checkin} a {self.data_checkout}"