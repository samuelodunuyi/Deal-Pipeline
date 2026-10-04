from django.contrib import admin

from .models import (
    Users, Events, Projects, Grant, Grant_partner,
    DevelopmentPlans, Deliverables, MentorshipPlans,
    SkillAssessments, SpeakingEngagements, TrainingSchedules, AdminUsers,
)

for model in (
    Users, Events, Projects, Grant, Grant_partner,
    DevelopmentPlans, Deliverables, MentorshipPlans,
    SkillAssessments, SpeakingEngagements, TrainingSchedules, AdminUsers,
):
    admin.site.register(model)
