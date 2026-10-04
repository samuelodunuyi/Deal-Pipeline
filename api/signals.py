from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .caching import bump_model_version
from .models import (
    Events, Users, Projects, Grant, Grant_partner,
    DevelopmentPlans, Deliverables, MentorshipPlans,
    SkillAssessments, SpeakingEngagements, TrainingSchedules, AdminUsers,
)

_WATCHED_MODELS = [
    Events, Users, Projects, Grant, Grant_partner,
    DevelopmentPlans, Deliverables, MentorshipPlans,
    SkillAssessments, SpeakingEngagements, TrainingSchedules, AdminUsers,
]


def _invalidate(sender, **kwargs):
    bump_model_version(sender._meta.label)


for _model in _WATCHED_MODELS:
    post_save.connect(_invalidate, sender=_model, weak=False)
    post_delete.connect(_invalidate, sender=_model, weak=False)
