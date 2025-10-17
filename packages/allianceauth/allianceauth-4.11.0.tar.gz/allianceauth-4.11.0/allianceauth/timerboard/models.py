from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from allianceauth.eveonline.models import EveCharacter
from allianceauth.eveonline.models import EveCorporationInfo


class Timer(models.Model):
    class Objective(models.TextChoices):
        """
        Choices for Objective Type
        """

        FRIENDLY = "Friendly", _("Friendly")
        HOSTILE = "Hostile", _("Hostile")
        NEUTRAL = "Neutral", _("Neutral")

    class Structure(models.TextChoices):
        """
        Choices for Structure Type
        """

        POCO = "POCO", _("POCO")
        ORBITALSKYHOOK = "Orbital Skyhook", _("Orbital Skyhook")
        IHUB = "I-HUB", _("Sovereignty Hub")
        TCU = "TCU", _("TCU")  # Pending Remval
        POSS = "POS[S]", _("POS [S]")
        POSM = "POS[M]", _("POS [M]")
        POSL = "POS[L]", _("POS [L]")
        ASTRAHUS = "Astrahus", _("Astrahus")
        FORTIZAR = "Fortizar", _("Fortizar")
        KEEPSTAR = "Keepstar", _("Keepstar")
        RAITARU = "Raitaru", _("Raitaru")
        AZBEL = "Azbel", _("Azbel")
        SOTIYO = "Sotiyo", _("Sotiyo")
        ATHANOR = "Athanor", _("Athanor")
        TATARA = "Tatara", _("Tatara")
        PHAROLUX = "Pharolux Cyno Beacon", _("Cyno Beacon")
        TENEBREX = "Tenebrex Cyno Jammer", _("Cyno Jammer")
        ANSIBLEX = "Ansiblex Jump Gate", _("Ansiblex Jump Gate")
        MERCDEN = "Mercenary Den", _("Mercenary Den")
        MOONPOP = "Moon Mining Cycle", _("Moon Mining Cycle")
        METENOX = "Metenox Moon Drill", _("Metenox Moon Drill")
        OTHER = "Other", _("Other")

    class TimerType(models.TextChoices):
        """
        Choices for Timer Type
        """

        UNSPECIFIED = "UNSPECIFIED", _("Not Specified")
        SHIELD = "SHIELD", _("Shield")
        ARMOR = "ARMOR", _("Armor")
        HULL = "HULL", _("Hull")
        FINAL = "FINAL", _("Final")
        ANCHORING = "ANCHORING", _("Anchoring")
        UNANCHORING = "UNANCHORING", _("Unanchoring")
        ABANDONED = "ABANDONED", _("Abandoned")
        THEFT = "THEFT", _("Theft")

    details = models.CharField(max_length=254, default="")
    system = models.CharField(max_length=254, default="")
    planet_moon = models.CharField(max_length=254, blank=True, default="")
    structure = models.CharField(max_length=254,choices=Structure.choices,default=Structure.OTHER)
    timer_type = models.CharField(max_length=254,choices=TimerType.choices,default=TimerType.UNSPECIFIED)
    objective = models.CharField(max_length=254, choices=Objective.choices, default=Objective.NEUTRAL)
    eve_time = models.DateTimeField()
    important = models.BooleanField(default=False)
    eve_character = models.ForeignKey(EveCharacter, null=True, on_delete=models.SET_NULL)
    eve_corp = models.ForeignKey(EveCorporationInfo, on_delete=models.CASCADE)
    corp_timer = models.BooleanField(default=False)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    def __str__(self) -> str:
        return str(self.system) + ' ' + str(self.details)

    class Meta:
        ordering = ['eve_time']
