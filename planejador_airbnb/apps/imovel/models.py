from django.db import models

from apps.localizacoes.models import Cidade, Bairro


class Imovel(models.Model):
    id_imovel = models.BigIntegerField(verbose_name="ID do Imóvel")
    tipo_acomodacao = models.CharField(max_length=100, verbose_name="Tipo de Acomodação")

    cidade = models.ForeignKey(
        Cidade,
        on_delete=models.PROTECT,
        related_name='imoveis_cidade'
    )
    bairro = models.ForeignKey(
        Bairro,
        on_delete=models.PROTECT,
        related_name='imoveis_bairro'
    )

    quartos = models.IntegerField(null=True, blank=True, verbose_name="Quartos")
    camas = models.IntegerField(null=True, blank=True, verbose_name="Camas")
    banheiros = models.IntegerField(null=True, blank=True, verbose_name="Banheiros")

    def __str__(self):
        return f"{self.tipo_acomodacao} - {self.bairro.nome}, {self.cidade.nome}"

    class Meta:
        db_table = 'imovel'
        verbose_name = "Imóvel"
        verbose_name_plural = "Imóveis"
        indexes = [
            models.Index(fields=['cidade', 'bairro']),
            models.Index(fields=['quartos']),
            models.Index(fields=['camas']),
        ]