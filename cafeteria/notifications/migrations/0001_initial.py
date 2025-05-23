# Generated by Django 5.1.7 on 2025-03-24 15:34

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Notificacion",
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
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("nuevo_pedido", "Nuevo Pedido"),
                            ("pedido_listo", "Pedido Listo"),
                            ("pedido_cancelado", "Pedido Cancelado"),
                            ("item_listo", "Item Listo"),
                            ("cambio_estado", "Cambio de Estado"),
                        ],
                        max_length=50,
                    ),
                ),
                ("titulo", models.CharField(max_length=100)),
                ("mensaje", models.TextField()),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("leida", models.BooleanField(default=False)),
                (
                    "prioridad",
                    models.CharField(
                        choices=[
                            ("baja", "Baja"),
                            ("media", "Media"),
                            ("alta", "Alta"),
                        ],
                        default="media",
                        max_length=10,
                    ),
                ),
                ("enlace", models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                "verbose_name": "Notificación",
                "verbose_name_plural": "Notificaciones",
                "ordering": ["-fecha_creacion"],
            },
        ),
    ]
