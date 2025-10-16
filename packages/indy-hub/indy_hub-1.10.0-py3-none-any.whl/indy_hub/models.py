# Django
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .utils.eve import get_blueprint_product_type_id, is_reaction_blueprint


class BlueprintManager(models.Manager):
    """Manager for Blueprint operations (local only)"""

    pass


class IndustryJobManager(models.Manager):
    """Manager for Industry Job operations (local only)"""

    pass


class Blueprint(models.Model):
    class BPType(models.TextChoices):
        REACTION = "REACTION", "Reaction"
        ORIGINAL = "ORIGINAL", "Original"
        COPY = "COPY", "Copy"

    owner_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blueprints"
    )
    character_id = models.BigIntegerField()
    item_id = models.BigIntegerField(unique=True)
    blueprint_id = models.BigIntegerField(blank=True, null=True)
    type_id = models.IntegerField()
    location_id = models.BigIntegerField()
    location_name = models.CharField(max_length=255, blank=True)
    location_flag = models.CharField(max_length=50)
    quantity = models.IntegerField()
    bp_type = models.CharField(
        max_length=16,
        choices=BPType.choices,
        default=BPType.ORIGINAL,
    )
    time_efficiency = models.IntegerField(default=0)
    material_efficiency = models.IntegerField(default=0)
    runs = models.IntegerField(default=0)
    character_name = models.CharField(max_length=255, blank=True)
    type_name = models.CharField(max_length=255, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = BlueprintManager()

    class Meta:
        verbose_name = "Blueprint"
        verbose_name_plural = "Blueprints"
        db_table = "indy_hub_indyblueprint"
        indexes = [
            models.Index(
                fields=["character_id", "type_id"],
                name="indy_hub_bl_charact_bfe16f_idx",
            ),
            models.Index(
                fields=["owner_user", "last_updated"],
                name="indy_hub_bl_owner_u_47cf92_idx",
            ),
        ]
        permissions = [
            ("can_access_indy_hub", "Can access Indy Hub module"),
        ]
        default_permissions = ()  # Disable Django's add/change/delete/view permissions

    def __str__(self):
        return f"{self.type_name or self.type_id} @ {self.character_id}"

    @property
    def is_original(self):
        return self.bp_type == self.BPType.ORIGINAL

    @property
    def is_copy(self):
        return self.bp_type in {self.BPType.COPY, "STACK"}

    @property
    def is_reaction(self):
        return self.bp_type == self.BPType.REACTION

    @property
    def quantity_display(self):
        """Human-readable quantity display"""
        if self.is_reaction:
            return "Reaction"
        if self.is_original:
            return "Original"
        if self.is_copy:
            runs = self.runs or 0
            return f"Copy ({runs} runs)" if runs else "Copy"
        return "Unknown"

    @property
    def product_type_id(self):
        """
        Attempts to determine the product type ID from blueprint type ID.
        For most blueprints in EVE: product_id = blueprint_id - 1
        Returns the type_id to use for icon display.
        """
        try:
            # Most blueprints follow the pattern: blueprint_type_id = product_type_id + 1
            potential_product_id = self.type_id - 1

            # Basic validation - product IDs should be positive
            if potential_product_id > 0:
                return potential_product_id
            else:
                # If calculation gives invalid result, return blueprint type_id
                return self.type_id
        except (TypeError, ValueError):
            # Fallback to blueprint type_id if calculation fails
            return self.type_id

    @property
    def icon_type_id(self):
        """
        Returns the type ID to use for displaying the blueprint icon.
        Uses product type ID when possible, falls back to blueprint type ID.
        """
        return self.product_type_id

    @property
    def me_progress_percentage(self):
        """Returns ME progress as percentage (0-100) for progress bar"""
        return int(min(100, (self.material_efficiency / 10.0) * 100))

    @property
    def te_progress_percentage(self):
        """Returns TE progress as percentage (0-100) for progress bar"""
        return int(min(100, (self.time_efficiency / 20.0) * 100))

    @classmethod
    def classify_bp_type(
        cls,
        *,
        quantity: int | None,
        type_name: str | None,
        type_id: int | None,
    ) -> str:
        if type_id and is_reaction_blueprint(type_id):
            return cls.BPType.REACTION

        name = (type_name or "").lower()
        if "formula" in name or "reaction" in name:
            return cls.BPType.REACTION

        if quantity == -2:
            return cls.BPType.COPY
        if quantity == -1:
            return cls.BPType.ORIGINAL
        if quantity and quantity > 0:
            return cls.BPType.COPY

        return cls.BPType.ORIGINAL

    def save(self, *args, **kwargs):
        self.bp_type = self.classify_bp_type(
            quantity=self.quantity,
            type_name=self.type_name,
            type_id=self.type_id,
        )
        if self.bp_type == "STACK":
            self.bp_type = self.BPType.COPY
        super().save(*args, **kwargs)


class IndustryJob(models.Model):
    owner_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="industry_jobs"
    )
    character_id = models.BigIntegerField()
    job_id = models.IntegerField(unique=True)
    installer_id = models.IntegerField()
    station_id = models.BigIntegerField(blank=True, null=True)
    location_name = models.CharField(max_length=255, blank=True)
    activity_id = models.IntegerField()
    blueprint_id = models.BigIntegerField()
    blueprint_type_id = models.IntegerField()
    runs = models.IntegerField()
    cost = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    licensed_runs = models.IntegerField(blank=True, null=True)
    probability = models.FloatField(blank=True, null=True)
    product_type_id = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=20)
    duration = models.IntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    pause_date = models.DateTimeField(blank=True, null=True)
    completed_date = models.DateTimeField(blank=True, null=True)
    completed_character_id = models.IntegerField(blank=True, null=True)
    successful_runs = models.IntegerField(blank=True, null=True)
    job_completed_notified = models.BooleanField(default=False)
    # Cached names for admin display
    activity_name = models.CharField(max_length=100, blank=True)
    blueprint_type_name = models.CharField(max_length=255, blank=True)
    product_type_name = models.CharField(max_length=255, blank=True)
    character_name = models.CharField(max_length=255, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = IndustryJobManager()

    class Meta:
        verbose_name = "Industry Job"
        verbose_name_plural = "Industry Jobs"
        indexes = [
            models.Index(
                fields=["character_id", "status"], name="indy_hub_in_charact_9ec4da_idx"
            ),
            models.Index(
                fields=["owner_user", "start_date"],
                name="indy_hub_in_owner_u_b59db7_idx",
            ),
            models.Index(
                fields=["activity_id", "status"], name="indy_hub_in_activit_8408d4_idx"
            ),
        ]
        default_permissions = ()

    def __str__(self):
        return f"Job {self.job_id} ({self.status})"

    @property
    def is_active(self):
        # Active only if status is active and end_date is in the future
        return (
            self.status == "active" and self.end_date and self.end_date > timezone.now()
        )

    @property
    def is_completed(self):
        # Completed when status flags delivered/ready or if end_date has passed
        if self.status in ["delivered", "ready"]:
            return True
        # treat overdue active jobs as completed
        return self.end_date and self.end_date <= timezone.now()

    @property
    def display_end_date(self):
        # Only mark as Completed if status indicates completion
        if self.is_completed:
            return "Completed"
        # Otherwise show the scheduled end date
        return self.end_date.strftime("%Y-%m-%d %H:%M") if self.end_date else ""

    @property
    def icon_url(self):
        """
        Returns the appropriate icon URL based on the job activity.
        """
        size = 32  # Default icon size for jobs

        # Copying jobs always show the resulting blueprint copy image when possible
        if self.activity_id == 5:
            copy_type_id = self.product_type_id or self.blueprint_type_id
            return f"https://images.evetech.net/types/{copy_type_id}/bpc?size={size}"

        # When blueprint and product IDs match, prefer the blueprint original artwork
        if self.product_type_id and self.blueprint_type_id == self.product_type_id:
            return f"https://images.evetech.net/types/{self.product_type_id}/bp?size={size}"

        # Otherwise favour the product icon if available
        if self.product_type_id:
            return f"https://images.evetech.net/types/{self.product_type_id}/icon?size={size}"

        # Fallback for missing product IDs – display the blueprint artwork
        return (
            f"https://images.evetech.net/types/{self.blueprint_type_id}/bp?size={size}"
        )

    @property
    def progress_percent(self):
        """Compute job progress percentage based on start and end dates"""
        if self.start_date and self.end_date:
            total = (self.end_date - self.start_date).total_seconds()
            if total <= 0:
                return 100
            elapsed = (timezone.now() - self.start_date).total_seconds()
            percent = (elapsed / total) * 100
            return int(max(0, min(100, percent)))
        return 0

    @property
    def display_eta(self):
        """Return formatted remaining time or Completed for jobs"""
        if self.end_date and self.end_date > timezone.now():
            remaining = self.end_date - timezone.now()
            total_seconds = int(remaining.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:d}:{minutes:02d}:{seconds:02d}"
        if self.end_date:
            return "Completed"
        return ""


class BlueprintCopyRequest(models.Model):
    # Blueprint identity (anonymized, deduped by type_id, ME, TE)
    type_id = models.IntegerField()
    material_efficiency = models.IntegerField()
    time_efficiency = models.IntegerField()
    requested_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bp_copy_requests"
    )
    runs_requested = models.IntegerField(default=1)
    copies_requested = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    fulfilled = models.BooleanField(default=False)
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    # No direct link to owner(s) to preserve anonymity

    class Meta:
        default_permissions = ()
        indexes = [
            models.Index(
                fields=(
                    "type_id",
                    "material_efficiency",
                    "time_efficiency",
                    "fulfilled",
                ),
                name="indy_copy_req_lookup",
            ),
            models.Index(
                fields=("requested_by", "fulfilled"),
                name="indy_copy_req_user_state",
            ),
        ]

    def __str__(self):
        return f"Copy request: {self.type_id} ME{self.material_efficiency} TE{self.time_efficiency} by {self.requested_by.username}"


class BlueprintCopyOffer(models.Model):
    request = models.ForeignKey(
        "BlueprintCopyRequest", on_delete=models.CASCADE, related_name="offers"
    )
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bp_copy_offers"
    )
    status = models.CharField(
        max_length=16,
        choices=[
            ("accepted", "Accepted"),
            ("conditional", "Conditional"),
            ("rejected", "Rejected"),
        ],
    )
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_by_buyer = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("request", "owner")
        default_permissions = ()


class UserOnboardingProgress(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="indy_onboarding",
    )
    dismissed = models.BooleanField(default=False)
    manual_steps = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = ()
        verbose_name = _("Onboarding progress")
        verbose_name_plural = _("Onboarding progress")

    def __str__(self):
        return f"Onboarding for {self.user.username}"

    def mark_step(self, key: str, completed: bool) -> None:
        manual = self.manual_steps.copy()
        if completed:
            manual[key] = True
        else:
            manual.pop(key, None)
        self.manual_steps = manual


class CharacterSettings(models.Model):
    """
    Regroupe les préférences utilisateur pour les notifications de jobs et le partage de copies.
    """

    SCOPE_NONE = "none"
    SCOPE_CORPORATION = "corporation"
    SCOPE_ALLIANCE = "alliance"
    COPY_SHARING_SCOPE_CHOICES = [
        (SCOPE_NONE, "None"),
        (SCOPE_CORPORATION, "Corporation"),
        (SCOPE_ALLIANCE, "Alliance"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    character_id = models.BigIntegerField()
    jobs_notify_completed = models.BooleanField(default=False)
    allow_copy_requests = models.BooleanField(default=False)
    copy_sharing_scope = models.CharField(
        max_length=20,
        choices=COPY_SHARING_SCOPE_CHOICES,
        default=SCOPE_NONE,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(
                fields=["user", "character_id"],
                name="charsettings_user_char_uq",
            )
        ]
        indexes = [
            models.Index(
                fields=["user", "character_id"],
                name="charsettings_user_char_idx",
            )
        ]

    def __str__(self):
        return f"Settings for {self.user.username}#{self.character_id}"

    def set_copy_sharing_scope(self, scope):
        if scope not in dict(self.COPY_SHARING_SCOPE_CHOICES):
            raise ValueError(f"Invalid copy sharing scope: {scope}")
        self.copy_sharing_scope = scope
        self.allow_copy_requests = scope != self.SCOPE_NONE


class ProductionConfig(models.Model):
    """
    Stocke les configurations de production (Prod/Buy/Useless) pour chaque blueprint et utilisateur.
    Maintenant lié à une simulation spécifique pour permettre de sauvegarder plusieurs configurations.
    """

    PRODUCTION_CHOICES = [
        ("prod", "Produce"),
        ("buy", "Buy"),
        ("useless", "Useless"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    simulation = models.ForeignKey(
        "ProductionSimulation",
        on_delete=models.CASCADE,
        related_name="production_configs",
        null=True,
        blank=True,
    )
    blueprint_type_id = models.BigIntegerField()  # Type ID du blueprint principal
    item_type_id = models.BigIntegerField()  # Type ID de l'item dans l'arbre
    production_mode = models.CharField(
        max_length=10, choices=PRODUCTION_CHOICES, default="prod"
    )
    quantity_needed = models.BigIntegerField(default=0)
    runs = models.IntegerField(default=1)  # Nombre de runs du blueprint principal
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("simulation", "item_type_id")
        default_permissions = ()
        indexes = [
            models.Index(fields=["user", "blueprint_type_id", "runs"]),
            models.Index(fields=["user", "item_type_id"]),
            models.Index(fields=["simulation", "item_type_id"]),
        ]

    def __str__(self):
        return f"{self.user.username} - BP:{self.blueprint_type_id} - Item:{self.item_type_id} - {self.production_mode}"


class BlueprintEfficiency(models.Model):
    """
    Stocke les valeurs ME/TE personnalisées définies par l'utilisateur pour chaque blueprint.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blueprint_type_id = models.BigIntegerField()
    simulation = models.ForeignKey(
        "ProductionSimulation",
        on_delete=models.CASCADE,
        related_name="blueprint_efficiencies",
    )
    material_efficiency = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    time_efficiency = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("simulation", "blueprint_type_id")
        default_permissions = ()
        indexes = [
            models.Index(fields=["user", "blueprint_type_id"]),
            models.Index(fields=["simulation", "blueprint_type_id"]),
        ]

    def __str__(self):
        return f"{self.user.username} - BP:{self.blueprint_type_id} - ME:{self.material_efficiency} TE:{self.time_efficiency}"


class CustomPrice(models.Model):
    """
    Stocke les prix manuels définis par l'utilisateur pour chaque item dans l'onglet Financial.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_type_id = models.BigIntegerField()
    simulation = models.ForeignKey(
        "ProductionSimulation", on_delete=models.CASCADE, related_name="custom_prices"
    )
    unit_price = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    is_sale_price = models.BooleanField(
        default=False
    )  # True si c'est le prix de vente du produit final
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("simulation", "item_type_id")
        default_permissions = ()
        indexes = [
            models.Index(fields=["user", "item_type_id"]),
            models.Index(fields=["simulation", "item_type_id"]),
        ]

    def __str__(self):
        price_type = "Sale" if self.is_sale_price else "Cost"
        return f"{self.user.username} - Item:{self.item_type_id} - {price_type}: {self.unit_price}"


class ProductionSimulation(models.Model):
    """
    Métadonnées des simulations de production sauvegardées par utilisateur.
    Chaque simulation stocke toutes les configurations: switches, ME/TE, prix manuels, etc.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blueprint_type_id = models.BigIntegerField()
    blueprint_name = models.CharField(max_length=255)
    runs = models.IntegerField(default=1)
    simulation_name = models.CharField(
        max_length=255, blank=True
    )  # Nom personnalisé optionnel

    # Métadonnées de résumé
    total_items = models.IntegerField(default=0)  # Nombre d'items dans la config
    total_buy_items = models.IntegerField(default=0)  # Nombre d'items à acheter
    total_prod_items = models.IntegerField(default=0)  # Nombre d'items à produire
    estimated_cost = models.DecimalField(
        max_digits=20, decimal_places=2, default=0
    )  # Coût estimé
    estimated_revenue = models.DecimalField(
        max_digits=20, decimal_places=2, default=0
    )  # Revenus estimés
    estimated_profit = models.DecimalField(
        max_digits=20, decimal_places=2, default=0
    )  # Profit estimé

    # Configuration générale de la simulation
    active_tab = models.CharField(
        max_length=50, default="materials"
    )  # Onglet actif (materials, blueprints, financial)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "blueprint_type_id", "runs")
        default_permissions = ()
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "-updated_at"]),
            models.Index(fields=["user", "blueprint_type_id"]),
        ]

    def __str__(self):
        name = self.simulation_name or f"{self.blueprint_name} x{self.runs}"
        return f"{self.user.username} - {name}"

    @property
    def display_name(self):
        if self.simulation_name:
            return f"{self.simulation_name} ({self.blueprint_name} x{self.runs})"
        return f"{self.blueprint_name} x{self.runs}"

    def get_production_configs(self):
        """Retourne toutes les configurations Prod/Buy/Useless de cette simulation."""
        return self.production_configs.all()

    @property
    def productionconfig_set(self):
        """Compatibilité rétro pour l'ancien nom de relation Django."""
        return self.production_configs

    def get_blueprint_efficiencies(self):
        """Retourne toutes les configurations ME/TE de cette simulation."""
        return self.blueprint_efficiencies.all()

    def get_custom_prices(self):
        """Retourne tous les prix manuels de cette simulation."""
        return self.custom_prices.all()

    @property
    def product_type_id(self) -> int | None:
        """Return the likely manufactured item type id for icon display."""
        product_id = get_blueprint_product_type_id(self.blueprint_type_id)
        if product_id:
            return product_id
        if self.blueprint_type_id:
            try:
                return int(self.blueprint_type_id)
            except (TypeError, ValueError):
                return None
        return None

    @property
    def product_icon_url(self) -> str | None:
        """Return the product render URL if available (matching blueprint listing)."""
        type_id = self.product_type_id
        if not type_id:
            return None
        return f"https://images.evetech.net/types/{type_id}/render?size=32"

    @property
    def blueprint_icon_url(self) -> str | None:
        """Return the blueprint icon URL for fallback display."""
        if not self.blueprint_type_id:
            return None
        return (
            f"https://images.evetech.net/types/{int(self.blueprint_type_id)}/bp?size=32"
        )

    @property
    def profit_margin(self):
        """Calcule la marge de profit en pourcentage."""
        if self.estimated_revenue > 0:
            return float((self.estimated_profit / self.estimated_revenue) * 100)
        return 0.0
