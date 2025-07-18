# Generated by Django 5.1.7 on 2025-07-09 14:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("compras", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TipoCompra",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nombre", models.CharField(max_length=50)),
                (
                    "categoria",
                    models.CharField(
                        choices=[
                            ("venta", "Venta/Productos para Venta"),
                            ("gasto", "Gasto Operativo"),
                            ("inversion", "Inversión/Activo Fijo"),
                        ],
                        max_length=20,
                    ),
                ),
                ("descripcion", models.TextField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Tipo de Compra",
                "verbose_name_plural": "Tipos de Compra",
            },
        ),
        migrations.AddField(
            model_name="compra",
            name="tipo_compra",
            field=models.ForeignKey(
                blank=True,
                help_text="Categoría de la compra: inventario, gasto o inversión",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="compras.tipocompra",
            ),
        ),
    ]
