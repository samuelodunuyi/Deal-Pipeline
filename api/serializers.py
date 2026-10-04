import os

from django.conf import settings
from rest_framework import serializers

from .models import (
    Users, Events, Projects, Grant, Grant_partner,
    DevelopmentPlans, Deliverables, MentorshipPlans,
    SkillAssessments, SpeakingEngagements, TrainingSchedules, AdminUsers,
)


class UploadValidationMixin:
    """Rejects uploaded files with a disallowed extension or above the size limit."""

    upload_fields = ()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        allowed = {ext.lower().lstrip('.') for ext in settings.UPLOAD_ALLOWED_EXTENSIONS}
        max_bytes = settings.UPLOAD_MAX_MB * 1024 * 1024
        errors = {}
        for field in self.upload_fields:
            upload = attrs.get(field)
            if not upload:
                continue
            extension = os.path.splitext(upload.name)[1].lower().lstrip('.')
            if extension not in allowed:
                errors[field] = f"File type '.{extension}' is not allowed. Allowed: {', '.join(sorted(allowed))}."
            elif upload.size > max_bytes:
                errors[field] = f'File is too large. The limit is {settings.UPLOAD_MAX_MB} MB.'
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class EventsSerializers(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = (
            'uuid', 'transaction', 'transaction_description',
            'venue', 'co_transactor', 'address', 'address2',
            'state', 'country', 'date', 'time', 'status',
        )


class UsersSerializers(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = (
            'uuid', 'name', 'company',
            'phone_number', 'role', 'status', 'email',
            'date_added',
        )


class ProjectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projects
        fields = '__all__'


class GrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grant
        fields = '__all__'


class GrantPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grant_partner
        fields = '__all__'


class DevelopmentPlansSerializer(UploadValidationMixin, serializers.ModelSerializer):
    upload_fields = ('evidenceURL',)
    evidenceURLpath = serializers.SerializerMethodField()

    class Meta:
        model = DevelopmentPlans
        fields = (
            'id', 'planTermId', 'planTypeId', 'goalSummary',
            'requiredResources', 'achievementApproach', 'potentialChallenges',
            'solutionCriteria', 'status', 'progressMetrics',
            'targetCompletionDate', 'actualCompletionDate', 'feedback',
            'evidenceURL', 'evidenceURLpath', 'createdBy', 'lastModifiedBy',
            'createdDate', 'lastModifiedDate', 'recordOwner',
        )

    def get_evidenceURLpath(self, obj):
        return obj.evidenceURLpath()


class DeliverablesSerializer(UploadValidationMixin, serializers.ModelSerializer):
    upload_fields = ('evidence',)

    class Meta:
        model = Deliverables
        fields = '__all__'


class MentorshipPlansSerializer(UploadValidationMixin, serializers.ModelSerializer):
    upload_fields = ('evidenceURL',)
    evidenceURLpath = serializers.SerializerMethodField()

    class Meta:
        model = MentorshipPlans
        fields = (
            'id', 'financialYearId', 'month', 'mentor', 'goals',
            'actionPlans', 'targetCompletionDate', 'actualCompletionDate',
            'progressMetrics', 'status', 'feedback', 'evidenceURL',
            'evidenceURLpath', 'createdBy', 'lastModifiedBy',
            'createdDate', 'lastModifiedDate', 'recordOwner',
        )

    def get_evidenceURLpath(self, obj):
        return obj.evidenceURLpath()


class SkillAssessmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillAssessments
        fields = (
            'id', 'skillDescription', 'currentStageId', 'desiredStageId',
            'skillGapDetails', 'comment', 'actionPlan',
            'createdBy', 'lastModifiedBy', 'recordOwner',
        )


class SpeakingEngagementsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakingEngagements
        fields = '__all__'


class TrainingSchedulesSerializer(UploadValidationMixin, serializers.ModelSerializer):
    upload_fields = ('evidenceURL',)
    evidenceURLpath = serializers.SerializerMethodField()

    class Meta:
        model = TrainingSchedules
        fields = (
            'id', 'trainingStartDate', 'trainingTopic', 'trainingMethod',
            'learningOutcome', 'dueDate', 'trainingInitiator', 'rating',
            'evidenceURL', 'evidenceURLpath', 'recordOwner',
            'status', 'department', 'isApproved',
        )

    def get_evidenceURLpath(self, obj):
        return obj.evidenceURLpath()


class AdminUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUsers
        fields = '__all__'
