from django.db import models


class DatedModel(models.Model):
    """feature
    :name: DatedModel
    :description: Modèle de base qui contient des champs de création et de mise à jour.
    :return: modèle Django prêt à être hérité.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
