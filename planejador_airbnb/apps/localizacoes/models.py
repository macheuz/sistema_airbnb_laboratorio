# apps/localizacoes/models.py
from django.db import models

class Cidade(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    estado = models.CharField(max_length=2) # UF

    def __str__(self):
        return self.nome
    class Meta:
        db_table = 'cidade'
        verbose_name = "Cidade"
        verbose_name_plural = "Cidades"

class Bairro(models.Model):
    nome = models.CharField(max_length=100)
    cidade = models.ForeignKey(Cidade, on_delete=models.CASCADE, related_name='bairros')

    def __str__(self):
        return f"{self.nome}, {self.cidade.nome}"

    class Meta:
        db_table = 'bairro'
        verbose_name = "Bairro"
        verbose_name_plural = "Bairros"