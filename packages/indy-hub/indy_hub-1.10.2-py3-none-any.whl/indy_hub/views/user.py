# User-related views
# Standard Library
import json
import logging
import secrets
from math import ceil
from urllib.parse import urlencode

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from esi.models import CallbackRedirect, Token

# AA Example App
from indy_hub.models import CharacterSettings

from ..decorators import indy_hub_access_required
from ..models import (
    Blueprint,
    BlueprintCopyRequest,
    IndustryJob,
    ProductionConfig,
    ProductionSimulation,
    UserOnboardingProgress,
)
from ..services.simulations import summarize_simulations
from ..tasks.industry import (
    MANUAL_REFRESH_KIND_BLUEPRINTS,
    MANUAL_REFRESH_KIND_JOBS,
    request_manual_refresh,
)
from ..utils.eve import get_character_name

logger = logging.getLogger(__name__)

ONBOARDING_TASK_CONFIG = [
    {
        "key": "connect_blueprints",
        "title": _("Connect blueprint access"),
        "description": _(
            "Authorize at least one character so Indy Hub can import your blueprints."
        ),
        "mode": "auto",
        "cta": "indy_hub:token_management",
        "icon": "fa-scroll",
    },
    {
        "key": "connect_jobs",
        "title": _("Connect industry jobs"),
        "description": _(
            "Add an industry jobs token to track active slots and completions."
        ),
        "mode": "auto",
        "cta": "indy_hub:token_management",
        "icon": "fa-industry",
    },
    {
        "key": "enable_sharing",
        "title": _("Enable copy sharing"),
        "description": _(
            "Pick a sharing scope so corpmates can request copies from your originals."
        ),
        "mode": "auto",
        "cta": "indy_hub:index",
        "icon": "fa-share-alt",
    },
    {
        "key": "review_guides",
        "title": _("Review the quick-start guides"),
        "description": _(
            "Skim the journey cards on the request or fulfil pages to learn the flow."
        ),
        "mode": "manual",
        "cta": "indy_hub:bp_copy_request_page",
        "icon": "fa-compass",
    },
    {
        "key": "submit_request",
        "title": _("Submit your first copy request"),
        "description": _("Try the workflow end to end by requesting a blueprint copy."),
        "mode": "auto",
        "cta": "indy_hub:bp_copy_request_page",
        "icon": "fa-copy",
    },
]

MANUAL_ONBOARDING_KEYS = {
    cfg["key"] for cfg in ONBOARDING_TASK_CONFIG if cfg["mode"] == "manual"
}

BLUEPRINT_SCOPE = "esi-characters.read_blueprints.v1"
JOBS_SCOPE = "esi-industry.read_character_jobs.v1"
STRUCTURE_SCOPE = "esi-universe.read_structures.v1"
BLUEPRINT_SCOPE_SET = [BLUEPRINT_SCOPE, STRUCTURE_SCOPE]
JOBS_SCOPE_SET = [JOBS_SCOPE, STRUCTURE_SCOPE]


def get_copy_sharing_states():
    return {
        CharacterSettings.SCOPE_NONE: {
            "enabled": False,
            "button_label": _("Private"),
            "button_hint": _("Your originals stay private for now."),
            "status_label": _("Not shared"),
            "status_hint": _("Turn on sharing to accept requests."),
            "badge_class": "bg-secondary-subtle text-secondary",
            "popup_message": _("Blueprint sharing disabled."),
            "fulfill_hint": _(
                "Enable sharing to see requests that match your originals."
            ),
            "subtitle": _(
                "Keep your library private until you're ready to collaborate."
            ),
        },
        CharacterSettings.SCOPE_CORPORATION: {
            "enabled": True,
            "button_label": _("Corporation"),
            "button_hint": _("Corpmates can request copies of your originals."),
            "status_label": _("Shared with corporation"),
            "status_hint": _("Blueprint requests are visible to your corporation."),
            "badge_class": "bg-warning-subtle text-warning",
            "popup_message": _("Blueprint sharing enabled for your corporation."),
            "fulfill_hint": _("Corporation pilots may be waiting on your copies."),
            "subtitle": _("Share duplicates with trusted corp industrialists."),
        },
        CharacterSettings.SCOPE_ALLIANCE: {
            "enabled": True,
            "button_label": _("Alliance"),
            "button_hint": _("Alliance pilots can request copies of your originals."),
            "status_label": _("Shared with alliance"),
            "status_hint": _("Blueprint requests are visible to your alliance."),
            "badge_class": "bg-primary-subtle text-primary",
            "popup_message": _("Blueprint sharing enabled for the entire alliance."),
            "fulfill_hint": _("Alliance pilots may be waiting on you."),
            "subtitle": _("Coordinate duplicate production across your alliance."),
        },
    }


# --- User views (token management, sync, etc.) ---
@indy_hub_access_required
@login_required
def index(request):
    """
    Home page for Indy Hub module.
    """
    blueprint_tokens = None
    jobs_tokens = None
    if Token:
        try:
            blueprint_tokens = Token.objects.filter(user=request.user).require_scopes(
                BLUEPRINT_SCOPE_SET
            )
            jobs_tokens = Token.objects.filter(user=request.user).require_scopes(
                JOBS_SCOPE_SET
            )
            # Deduplicate by character_id
            blueprint_char_ids = (
                list(blueprint_tokens.values_list("character_id", flat=True).distinct())
                if blueprint_tokens
                else []
            )
            jobs_char_ids = (
                list(jobs_tokens.values_list("character_id", flat=True).distinct())
                if jobs_tokens
                else []
            )
        except Exception:
            blueprint_tokens = jobs_tokens = None
            blueprint_char_ids = jobs_char_ids = []
    user_chars = []
    ownerships = CharacterOwnership.objects.filter(user=request.user)
    for ownership in ownerships:
        cid = ownership.character.character_id
        user_chars.append(
            {
                "character_id": cid,
                "name": get_character_name(cid),
                "bp_enabled": (
                    blueprint_tokens.filter(character_id=cid).exists()
                    if blueprint_tokens
                    else False
                ),
                "jobs_enabled": (
                    jobs_tokens.filter(character_id=cid).exists()
                    if jobs_tokens
                    else False
                ),
            }
        )
    # Blueprints stats
    blueprints_qs = Blueprint.objects.filter(owner_user=request.user)

    def normalized_quantity(value: int | None) -> int:
        if value in (-1, -2):
            return 1
        if value is None:
            return 0
        return max(value, 0)

    blueprint_count = 0
    original_blueprints = 0
    copy_blueprints = 0

    for bp in blueprints_qs:
        qty = normalized_quantity(bp.quantity)
        blueprint_count += qty
        if bp.is_copy:
            copy_blueprints += qty
        else:
            original_blueprints += qty
    # Jobs stats
    jobs_qs = IndustryJob.objects.filter(owner_user=request.user)

    now = timezone.now()
    today = now.date()
    active_jobs_count = jobs_qs.filter(status="active", end_date__gt=now).count()
    completed_jobs_count = jobs_qs.filter(end_date__lte=now).count()
    completed_jobs_today = jobs_qs.filter(
        end_date__date=today, end_date__lte=now
    ).count()
    # Récupère ou crée les préférences utilisateur
    settings, _ = CharacterSettings.objects.get_or_create(
        user=request.user, character_id=0
    )
    jobs_notify_completed = settings.jobs_notify_completed
    copy_sharing_scope = settings.copy_sharing_scope
    if copy_sharing_scope not in dict(CharacterSettings.COPY_SHARING_SCOPE_CHOICES):
        copy_sharing_scope = CharacterSettings.SCOPE_NONE

    copy_sharing_states = get_copy_sharing_states()
    copy_sharing_states_with_scope = {
        key: {**value, "scope": key} for key, value in copy_sharing_states.items()
    }
    sharing_state = copy_sharing_states.get(
        copy_sharing_scope, copy_sharing_states[CharacterSettings.SCOPE_NONE]
    )

    allow_copy_requests = sharing_state["enabled"]
    if allow_copy_requests != settings.allow_copy_requests:
        settings.allow_copy_requests = allow_copy_requests
        settings.save(update_fields=["allow_copy_requests"])

    # Blueprint copy request insights
    copy_fulfill_count = 0
    copy_my_requests_open = 0
    copy_my_requests_pending_delivery = 0

    if sharing_state["enabled"]:
        fulfill_filters = Q()
        originals_for_fulfill = blueprints_qs.filter(
            bp_type__in=[Blueprint.BPType.ORIGINAL, Blueprint.BPType.REACTION]
        )
        original_blueprint_type_ids: set[int] = set()
        for bp in originals_for_fulfill:
            original_blueprint_type_ids.add(bp.type_id)
            fulfill_filters |= Q(
                type_id=bp.type_id,
                material_efficiency=bp.material_efficiency,
                time_efficiency=bp.time_efficiency,
            )

        open_requests_qs = BlueprintCopyRequest.objects.none()
        open_requests_to_fulfill = 0
        if fulfill_filters:
            open_requests_qs = BlueprintCopyRequest.objects.filter(
                fulfill_filters, fulfilled=False
            )
            copy_fulfill_count = (
                open_requests_qs.exclude(requested_by=request.user)
                .aggregate(total=Sum("copies_requested"))
                .get("total")
                or 0
            )
            open_requests_to_fulfill = open_requests_qs.exclude(
                requested_by=request.user
            ).count()

        my_open_requests = BlueprintCopyRequest.objects.filter(
            requested_by=request.user, fulfilled=False
        ).count()
        copy_my_requests_open = open_requests_to_fulfill + my_open_requests

        if original_blueprint_type_ids:
            copy_my_requests_pending_delivery = jobs_qs.filter(
                activity_id=5,
                blueprint_type_id__in=list(original_blueprint_type_ids),
                status__in=["active", "ready"],
            ).count()

    copy_my_requests_total = copy_my_requests_open + copy_my_requests_pending_delivery

    onboarding_progress, _ = UserOnboardingProgress.objects.get_or_create(
        user=request.user
    )
    manual_steps = onboarding_progress.manual_steps or {}
    has_any_request_history = BlueprintCopyRequest.objects.filter(
        requested_by=request.user
    ).exists()

    onboarding_tasks = []
    for cfg in ONBOARDING_TASK_CONFIG:
        task = {
            "key": cfg["key"],
            "title": cfg["title"],
            "description": cfg["description"],
            "mode": cfg["mode"],
            "icon": cfg.get("icon"),
            "cta": cfg.get("cta"),
        }
        if cfg["mode"] == "manual":
            completed = bool(manual_steps.get(cfg["key"]))
        else:
            if cfg["key"] == "connect_blueprints":
                completed = bool(blueprint_char_ids)
            elif cfg["key"] == "connect_jobs":
                completed = bool(jobs_char_ids)
            elif cfg["key"] == "enable_sharing":
                completed = bool(sharing_state["enabled"])
            elif cfg["key"] == "submit_request":
                completed = has_any_request_history
            else:
                completed = False
        task["completed"] = completed
        cta_name = task.get("cta")
        if cta_name:
            try:
                task["cta_url"] = reverse(cta_name)
            except Exception:
                task["cta_url"] = None
        else:
            task["cta_url"] = None
        onboarding_tasks.append(task)

    completed_count = sum(1 for task in onboarding_tasks if task["completed"])
    total_tasks = len(onboarding_tasks)
    pending_tasks = [task for task in onboarding_tasks if not task["completed"]]
    onboarding_percent = (
        int(round((completed_count / total_tasks) * 100)) if total_tasks else 0
    )
    onboarding_show = bool(pending_tasks) and not onboarding_progress.dismissed

    context = {
        "has_blueprint_tokens": bool(blueprint_char_ids),
        "has_jobs_tokens": bool(jobs_char_ids),
        "blueprint_token_count": len(blueprint_char_ids),
        "jobs_token_count": len(jobs_char_ids),
        "characters": user_chars,
        "blueprint_count": blueprint_count,
        "original_blueprints": original_blueprints,
        "copy_blueprints": copy_blueprints,
        "active_jobs_count": active_jobs_count,
        "completed_jobs_count": completed_jobs_count,
        "completed_jobs_today": completed_jobs_today,
        "jobs_notify_completed": jobs_notify_completed,
        "allow_copy_requests": sharing_state["enabled"],
        "copy_sharing_scope": copy_sharing_scope,
        "copy_sharing_state": sharing_state,
        "copy_sharing_states_json": json.dumps(copy_sharing_states_with_scope),
        "copy_fulfill_count": copy_fulfill_count,
        "copy_my_requests_open": copy_my_requests_open,
        "copy_my_requests_pending_delivery": copy_my_requests_pending_delivery,
        "copy_my_requests_total": copy_my_requests_total,
        "onboarding": {
            "tasks": onboarding_tasks,
            "completed": completed_count,
            "total": total_tasks,
            "pending": len(pending_tasks),
            "percent": onboarding_percent,
            "show": onboarding_show,
            "dismissed": onboarding_progress.dismissed,
        },
    }
    return render(request, "indy_hub/index.html", context)


@indy_hub_access_required
@login_required
def token_management(request):
    blueprint_tokens = None
    jobs_tokens = None
    if Token:
        try:
            blueprint_tokens = Token.objects.filter(user=request.user).require_scopes(
                BLUEPRINT_SCOPE_SET
            )
            jobs_tokens = Token.objects.filter(user=request.user).require_scopes(
                JOBS_SCOPE_SET
            )
            # Deduplicate by character_id
            blueprint_char_ids = (
                list(blueprint_tokens.values_list("character_id", flat=True).distinct())
                if blueprint_tokens
                else []
            )
            jobs_char_ids = (
                list(jobs_tokens.values_list("character_id", flat=True).distinct())
                if jobs_tokens
                else []
            )
        except Exception:
            blueprint_tokens = jobs_tokens = None
            blueprint_char_ids = jobs_char_ids = []
    blueprint_auth_url = (
        reverse("indy_hub:authorize_blueprints") if CallbackRedirect else None
    )
    jobs_auth_url = reverse("indy_hub:authorize_jobs") if CallbackRedirect else None
    user_chars = []
    ownerships = CharacterOwnership.objects.filter(user=request.user)
    for ownership in ownerships:
        cid = ownership.character.character_id
        user_chars.append(
            {
                "character_id": cid,
                "name": get_character_name(cid),
                "bp_enabled": (
                    blueprint_tokens.filter(character_id=cid).exists()
                    if blueprint_tokens
                    else False
                ),
                "jobs_enabled": (
                    jobs_tokens.filter(character_id=cid).exists()
                    if jobs_tokens
                    else False
                ),
            }
        )
    context = {
        "has_blueprint_tokens": bool(blueprint_char_ids),
        "has_jobs_tokens": bool(jobs_char_ids),
        "blueprint_token_count": len(blueprint_char_ids),
        "jobs_token_count": len(jobs_char_ids),
        "blueprint_auth_url": blueprint_auth_url,
        "jobs_auth_url": jobs_auth_url,
        "characters": user_chars,
    }
    return render(request, "indy_hub/token_management.html", context)


@indy_hub_access_required
@login_required
def authorize_blueprints(request):
    # Only skip if ALL characters are already authorized for blueprint scope
    all_chars = CharacterOwnership.objects.filter(user=request.user).values_list(
        "character__character_id", flat=True
    )
    authorized = (
        Token.objects.filter(user=request.user)
        .require_scopes(BLUEPRINT_SCOPE_SET)
        .values_list("character_id", flat=True)
    )
    missing = set(all_chars) - set(authorized)
    if not missing:
        messages.info(request, "All characters already have blueprint access.")
        return redirect("indy_hub:token_management")
    if not CallbackRedirect:
        messages.error(request, "ESI module not available")
        return redirect("indy_hub:token_management")
    try:
        if not request.session.session_key:
            request.session.create()
        CallbackRedirect.objects.filter(
            session_key=request.session.session_key
        ).delete()
        blueprint_state = f"indy_hub_blueprints_{secrets.token_urlsafe(8)}"
        CallbackRedirect.objects.create(
            session_key=request.session.session_key,
            url=reverse("indy_hub:token_management"),
            state=blueprint_state,
        )
        callback_url = getattr(
            settings, "ESI_SSO_CALLBACK_URL", "http://localhost:8000/sso/callback/"
        )
        client_id = getattr(settings, "ESI_SSO_CLIENT_ID", "")
        blueprint_params = {
            "response_type": "code",
            "redirect_uri": callback_url,
            "client_id": client_id,
            "scope": " ".join(BLUEPRINT_SCOPE_SET),
            "state": blueprint_state,
        }
        blueprint_auth_url = f"https://login.eveonline.com/v2/oauth/authorize/?{urlencode(blueprint_params)}"
        return redirect(blueprint_auth_url)
    except Exception as e:
        logger.error(f"Error creating blueprint authorization: {e}")
        messages.error(request, f"Error setting up ESI authorization: {e}")
        return redirect("indy_hub:token_management")


@indy_hub_access_required
@login_required
def authorize_jobs(request):
    # Only skip if ALL characters have jobs access
    all_chars = CharacterOwnership.objects.filter(user=request.user).values_list(
        "character__character_id", flat=True
    )
    authorized = (
        Token.objects.filter(user=request.user)
        .require_scopes(JOBS_SCOPE_SET)
        .values_list("character_id", flat=True)
    )
    missing = set(all_chars) - set(authorized)
    if not missing:
        messages.info(request, "All characters already have jobs access.")
        return redirect("indy_hub:token_management")
    if not CallbackRedirect:
        messages.error(request, "ESI module not available")
        return redirect("indy_hub:token_management")
    try:
        if not request.session.session_key:
            request.session.create()
        CallbackRedirect.objects.filter(
            session_key=request.session.session_key
        ).delete()
        jobs_state = f"indy_hub_jobs_{secrets.token_urlsafe(8)}"
        CallbackRedirect.objects.create(
            session_key=request.session.session_key,
            url=reverse("indy_hub:token_management"),
            state=jobs_state,
        )
        callback_url = getattr(
            settings, "ESI_SSO_CALLBACK_URL", "http://localhost:8000/sso/callback/"
        )
        client_id = getattr(settings, "ESI_SSO_CLIENT_ID", "")
        jobs_params = {
            "response_type": "code",
            "redirect_uri": callback_url,
            "client_id": client_id,
            "scope": " ".join(JOBS_SCOPE_SET),
            "state": jobs_state,
        }
        jobs_auth_url = (
            f"https://login.eveonline.com/v2/oauth/authorize/?{urlencode(jobs_params)}"
        )
        return redirect(jobs_auth_url)
    except Exception as e:
        logger.error(f"Error creating jobs authorization: {e}")
        messages.error(request, f"Error setting up ESI authorization: {e}")
        return redirect("indy_hub:token_management")


@indy_hub_access_required
@login_required
def authorize_all(request):
    # Only skip if ALL characters have both blueprint and jobs access
    all_chars = CharacterOwnership.objects.filter(user=request.user).values_list(
        "character__character_id", flat=True
    )
    blueprint_auth = (
        Token.objects.filter(user=request.user)
        .require_scopes(BLUEPRINT_SCOPE_SET)
        .values_list("character_id", flat=True)
    )
    jobs_auth = (
        Token.objects.filter(user=request.user)
        .require_scopes(JOBS_SCOPE_SET)
        .values_list("character_id", flat=True)
    )
    missing = set(all_chars) - (set(blueprint_auth) & set(jobs_auth))
    if not missing:
        messages.info(request, "All characters already authorized for all scopes.")
        return redirect("indy_hub:token_management")
    if not CallbackRedirect:
        messages.error(request, "ESI module not available")
        return redirect("indy_hub:token_management")
    try:
        if not request.session.session_key:
            request.session.create()
        CallbackRedirect.objects.filter(
            session_key=request.session.session_key
        ).delete()
        state = f"indy_hub_all_{secrets.token_urlsafe(8)}"
        CallbackRedirect.objects.create(
            session_key=request.session.session_key,
            url=reverse("indy_hub:token_management"),
            state=state,
        )
        callback_url = getattr(
            settings, "ESI_SSO_CALLBACK_URL", "http://localhost:8000/sso/callback/"
        )
        client_id = getattr(settings, "ESI_SSO_CLIENT_ID", "")
        combined_scopes = sorted({*BLUEPRINT_SCOPE_SET, *JOBS_SCOPE_SET})
        params = {
            "response_type": "code",
            "redirect_uri": callback_url,
            "client_id": client_id,
            "scope": " ".join(combined_scopes),
            "state": state,
        }
        auth_url = (
            f"https://login.eveonline.com/v2/oauth/authorize/?{urlencode(params)}"
        )
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Error creating combined authorization: {e}")
        messages.error(request, f"Error setting up ESI authorization: {e}")
        return redirect("indy_hub:token_management")


@indy_hub_access_required
@login_required
def sync_all_tokens(request):
    if Token:
        try:
            blueprint_tokens = Token.objects.filter(user=request.user).require_scopes(
                BLUEPRINT_SCOPE_SET
            )
            jobs_tokens = Token.objects.filter(user=request.user).require_scopes(
                JOBS_SCOPE_SET
            )
            any_scheduled = False
            if blueprint_tokens.exists():
                scheduled, remaining = request_manual_refresh(
                    MANUAL_REFRESH_KIND_BLUEPRINTS,
                    request.user.id,
                    priority=5,
                )
                if scheduled:
                    any_scheduled = True
                    messages.success(
                        request,
                        _("Blueprint synchronization scheduled."),
                    )
                else:
                    wait_minutes = max(1, ceil(remaining.total_seconds() / 60))
                    messages.warning(
                        request,
                        _(
                            "Blueprint synchronization is on cooldown. Please retry in %(minutes)s minute(s)."
                        )
                        % {"minutes": wait_minutes},
                    )
            else:
                messages.warning(
                    request,
                    _("No blueprint tokens available for synchronization."),
                )

            if jobs_tokens.exists():
                scheduled, remaining = request_manual_refresh(
                    MANUAL_REFRESH_KIND_JOBS,
                    request.user.id,
                    priority=5,
                )
                if scheduled:
                    any_scheduled = True
                    messages.success(
                        request,
                        _("Industry jobs synchronization scheduled."),
                    )
                else:
                    wait_minutes = max(1, ceil(remaining.total_seconds() / 60))
                    messages.warning(
                        request,
                        _(
                            "Jobs synchronization is on cooldown. Please retry in %(minutes)s minute(s)."
                        )
                        % {"minutes": wait_minutes},
                    )
            else:
                messages.warning(
                    request,
                    _("No jobs tokens available for synchronization."),
                )

            if not any_scheduled:
                logger.info(
                    "User %s requested sync_all_tokens but no tasks were queued due to cooldown or missing tokens",
                    request.user.username,
                )
        except Exception as e:
            logger.error(f"Error triggering sync_all: {e}")
            messages.error(request, "Error starting synchronization.")
    else:
        messages.error(request, "ESI module not available.")
    return redirect("indy_hub:token_management")


@indy_hub_access_required
@login_required
def sync_blueprints(request):
    if Token:
        try:
            blueprint_tokens = Token.objects.filter(user=request.user).require_scopes(
                BLUEPRINT_SCOPE_SET
            )
            if blueprint_tokens.exists():
                scheduled, remaining = request_manual_refresh(
                    MANUAL_REFRESH_KIND_BLUEPRINTS,
                    request.user.id,
                    priority=5,
                )
                if scheduled:
                    messages.success(
                        request,
                        _("Blueprint synchronization scheduled."),
                    )
                else:
                    wait_minutes = max(1, ceil(remaining.total_seconds() / 60))
                    messages.warning(
                        request,
                        _(
                            "Blueprint synchronization is on cooldown. Please retry in %(minutes)s minute(s)."
                        )
                        % {"minutes": wait_minutes},
                    )
            else:
                messages.warning(
                    request, "No blueprint tokens available for synchronization."
                )
        except Exception as e:
            logger.error(f"Error triggering sync_blueprints: {e}")
            messages.error(request, "Error starting blueprint synchronization.")
    else:
        messages.error(request, "ESI module not available.")
    return redirect("indy_hub:token_management")


@indy_hub_access_required
@login_required
def sync_jobs(request):
    if Token:
        try:
            jobs_tokens = Token.objects.filter(user=request.user).require_scopes(
                JOBS_SCOPE_SET
            )
            if jobs_tokens.exists():
                scheduled, remaining = request_manual_refresh(
                    MANUAL_REFRESH_KIND_JOBS,
                    request.user.id,
                    priority=5,
                )
                if scheduled:
                    messages.success(
                        request,
                        _("Jobs synchronization scheduled."),
                    )
                else:
                    wait_minutes = max(1, ceil(remaining.total_seconds() / 60))
                    messages.warning(
                        request,
                        _(
                            "Jobs synchronization is on cooldown. Please retry in %(minutes)s minute(s)."
                        )
                        % {"minutes": wait_minutes},
                    )
            else:
                messages.warning(
                    request, "No jobs tokens available for synchronization."
                )
        except Exception as e:
            logger.error(f"Error triggering sync_jobs: {e}")
            messages.error(request, "Error starting jobs synchronization.")
    else:
        messages.error(request, "ESI module not available.")
    return redirect("indy_hub:token_management")


# Toggle notification des travaux
@indy_hub_access_required
@login_required
@require_POST
def toggle_job_notifications(request):
    # Basculer la préférence de notification
    settings, _ = CharacterSettings.objects.get_or_create(
        user=request.user, character_id=0
    )
    settings.jobs_notify_completed = not settings.jobs_notify_completed
    settings.save(update_fields=["jobs_notify_completed"])
    return JsonResponse({"enabled": settings.jobs_notify_completed})


# Toggle pooling de partage de copies
@indy_hub_access_required
@login_required
@require_POST
def toggle_copy_sharing(request):
    settings, _ = CharacterSettings.objects.get_or_create(
        user=request.user, character_id=0
    )
    scope_order = [
        CharacterSettings.SCOPE_NONE,
        CharacterSettings.SCOPE_CORPORATION,
        CharacterSettings.SCOPE_ALLIANCE,
    ]
    payload = {}
    if request.body:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            payload = {}

    requested_scope = payload.get("scope") if isinstance(payload, dict) else None
    if requested_scope in scope_order:
        next_scope = requested_scope
    else:
        try:
            current_index = scope_order.index(settings.copy_sharing_scope)
        except ValueError:
            current_index = 0
        next_scope = scope_order[(current_index + 1) % len(scope_order)]

    settings.set_copy_sharing_scope(next_scope)
    settings.save(
        update_fields=["allow_copy_requests", "copy_sharing_scope", "updated_at"]
    )

    sharing_state = get_copy_sharing_states()[next_scope]

    return JsonResponse(
        {
            "scope": next_scope,
            "enabled": sharing_state["enabled"],
            "button_label": sharing_state["button_label"],
            "button_hint": sharing_state["button_hint"],
            "status_label": sharing_state["status_label"],
            "status_hint": sharing_state["status_hint"],
            "badge_class": sharing_state["badge_class"],
            "popup_message": sharing_state["popup_message"],
            "fulfill_hint": sharing_state["fulfill_hint"],
            "subtitle": sharing_state["subtitle"],
        }
    )


@indy_hub_access_required
@login_required
@require_POST
def onboarding_toggle_task(request):
    task_key = request.POST.get("task", "").strip()
    action = request.POST.get("action", "complete")
    next_url = (
        request.POST.get("next")
        or request.headers.get("referer")
        or reverse("indy_hub:index")
    )
    if not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = reverse("indy_hub:index")

    if task_key not in MANUAL_ONBOARDING_KEYS:
        messages.error(request, _("This checklist item can't be updated manually."))
        return redirect(next_url)

    progress, _created = UserOnboardingProgress.objects.get_or_create(user=request.user)
    completed = action != "reset"
    progress.mark_step(task_key, completed)
    fields = ["manual_steps", "updated_at"]
    if completed and progress.dismissed:
        progress.dismissed = False
        fields.append("dismissed")
    progress.save(update_fields=list(dict.fromkeys(fields)))

    if completed:
        messages.success(
            request, _("Nice! We'll remember that you've reviewed the guides.")
        )
    else:
        messages.info(request, _("Checklist item reset."))
    return redirect(next_url)


@indy_hub_access_required
@login_required
@require_POST
def onboarding_set_visibility(request):
    action = request.POST.get("action", "dismiss")
    next_url = (
        request.POST.get("next")
        or request.headers.get("referer")
        or reverse("indy_hub:index")
    )
    if not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = reverse("indy_hub:index")

    progress, _created = UserOnboardingProgress.objects.get_or_create(user=request.user)
    dismiss = action != "restore"
    if progress.dismissed != dismiss:
        progress.dismissed = dismiss
        progress.save(update_fields=["dismissed", "updated_at"])

    if dismiss:
        messages.info(request, _("Checklist hidden. You can bring it back anytime."))
    else:
        messages.success(request, _("Checklist restored."))
    return redirect(next_url)


# --- Production Simulations Management ---
@indy_hub_access_required
@login_required
def production_simulations(request):
    """
    Page de gestion des simulations de production sauvegardées.
    """
    simulations = (
        ProductionSimulation.objects.filter(user=request.user)
        .order_by("-updated_at")
        .prefetch_related("production_configs")
    )

    total_simulations, stats = summarize_simulations(simulations)

    context = {
        "simulations": simulations,
        "total_simulations": total_simulations,
        "stats": stats,
    }

    return render(request, "indy_hub/production_simulations.html", context)


@indy_hub_access_required
@login_required
@require_POST
def delete_production_simulation(request, simulation_id):
    """
    Supprimer une simulation de production.
    """
    simulation = get_object_or_404(
        ProductionSimulation, id=simulation_id, user=request.user
    )

    # Supprimer aussi toutes les configurations associées
    ProductionConfig.objects.filter(
        user=request.user,
        blueprint_type_id=simulation.blueprint_type_id,
        runs=simulation.runs,
    ).delete()

    simulation_name = simulation.display_name
    simulation.delete()

    messages.success(request, f'Simulation "{simulation_name}" supprimée avec succès.')
    return redirect("indy_hub:production_simulations")


@indy_hub_access_required
@login_required
def rename_production_simulation(request, simulation_id):
    """
    Renommer une simulation de production.
    """
    simulation = get_object_or_404(
        ProductionSimulation, id=simulation_id, user=request.user
    )

    if request.method == "POST":
        new_name = request.POST.get("simulation_name", "").strip()
        simulation.simulation_name = new_name
        simulation.save(update_fields=["simulation_name"])

        messages.success(
            request, f'Simulation renommée en "{simulation.display_name}".'
        )
        return redirect("indy_hub:production_simulations")

    context = {
        "simulation": simulation,
    }

    return render(request, "indy_hub/rename_simulation.html", context)
