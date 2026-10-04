from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone


HOST = settings.HOST

status_choices = [
    ('Pending storage creation', 'Pending storage creation'),
    ('Pending document upload', 'Pending document upload'),
    ('Pending L&D verification', 'Pending L&D verification'),
    ('Pending schedule', 'Pending schedule'),
    ('Pending access to dataroom', 'Pending access to dataroom'),
    ('Done', 'Done'),
]


def _full_url(field):
    if field:
        return HOST.rstrip('/') + field.url
    return ''


class Events(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.CharField(max_length=50, null=True, blank=True)
    transaction_description = models.TextField(max_length=625, null=True, blank=True)
    venue = models.CharField(max_length=50, null=True, blank=True)
    co_transactor = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=450, null=True, blank=True)
    address2 = models.CharField(max_length=450, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True, choices=status_choices, default='Pending storage creation')
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.transaction} -> {self.date}: {self.time} {self.status}"

    class Meta:
        ordering = ('-date', '-time')


class Users(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} -> {self.role}"

    class Meta:
        ordering = ('-name',)


class Projects(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_name = models.CharField(max_length=255, blank=True, null=True)
    project_name = models.CharField(max_length=255, blank=True, null=True)
    transaction_name = models.CharField(max_length=255, blank=True, null=True)
    sector = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    status = models.BooleanField(blank=True, null=True, default=False)
    mandated_deal_size = models.FloatField(blank=True, null=True)
    initial_deal_size = models.FloatField(blank=True, null=True)
    transaction_lead = models.CharField(max_length=255, blank=True, null=True)
    leadtransactorName = models.CharField(max_length=255, blank=True, null=True)
    transactoranalystname = models.CharField(max_length=255, blank=True, null=True)
    transaction_analyst = models.CharField(max_length=255, blank=True, null=True)
    credit_commitee_approval = models.DateField(blank=True, null=True)
    fee_letter_date = models.DateField(blank=True, null=True)
    expected_closing_date = models.CharField(max_length=100, blank=True, null=True)
    transaction_stage = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    NBC = models.CharField(max_length=1000, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    expected_end_date = models.DateField(blank=True, null=True)
    actual_end_date = models.DateField(blank=True, null=True)
    NBC_document = models.TextField(max_length=3000, blank=True, null=True)
    issues = models.TextField(max_length=3000, blank=True, null=True)
    board = models.TextField(max_length=3000, blank=True, null=True)
    board_start_date = models.DateField(blank=True, null=True)
    board_expected_end_date = models.DateField(blank=True, null=True)
    board_actual_end_date = models.DateField(blank=True, null=True)
    board_document = models.TextField(max_length=3000, blank=True, null=True)
    SFU_first_installment_amount = models.FloatField(blank=True, null=True)
    SFU_second_installment_amount = models.FloatField(blank=True, null=True)
    DDW_preliminary_legal_DD_consultant = models.CharField(max_length=1000, blank=True, null=True)
    DDW_preliminary_legal_DD_amount = models.FloatField(blank=True, null=True)
    DDW_preliminary_legal_DD_status = models.CharField(max_length=1000, blank=True, null=True)
    DDW_preliminary_legal_DD_start_date = models.DateField(blank=True, null=True)
    DDW_preliminary_legal_DD_expected_end_date = models.DateField(blank=True, null=True)
    DDW_preliminary_legal_DD_actual_end_date = models.DateField(blank=True, null=True)
    DDW_preliminary_E_and_S_consultant = models.CharField(max_length=1000, blank=True, null=True)
    DDW_preliminary_E_and_S_amount = models.FloatField(blank=True, null=True)
    DDW_preliminary_E_and_S_status = models.CharField(max_length=1000, blank=True, null=True)
    DDW_preliminary_E_and_S_start_date = models.DateField(blank=True, null=True)
    DDW_preliminary_E_and_S_expected_end_date = models.DateField(blank=True, null=True)
    DDW_preliminary_E_and_S_actual_end_date = models.DateField(blank=True, null=True)
    DDW_tech_and_com_consultant = models.CharField(max_length=1000, blank=True, null=True)
    DDW_tech_and_com_amount = models.FloatField(blank=True, null=True)
    DDW_tech_and_com_status = models.CharField(max_length=1000, blank=True, null=True)
    DDW_tech_and_com_start_date = models.DateField(blank=True, null=True)
    DDW_tech_and_com_expected_end_date = models.DateField(blank=True, null=True)
    DDW_tech_and_com_actual_end_date = models.DateField(blank=True, null=True)
    DDW_embedded_advisor_consultant = models.CharField(max_length=1000, blank=True, null=True)
    DDW_embedded_advisor_amount = models.FloatField(blank=True, null=True)
    DDW_embedded_advisor_status = models.CharField(max_length=1000, blank=True, null=True)
    DDW_embedded_advisor_start_date = models.DateField(blank=True, null=True)
    DDW_embedded_advisor_expected_end_date = models.DateField(blank=True, null=True)
    DDW_embedded_advisor_actual_end_date = models.DateField(blank=True, null=True)
    CAS_status_financial_model = models.CharField(max_length=1000, blank=True, null=True)
    CAS_status_risk_rating = models.BooleanField(blank=True, null=True, default=False)
    CAS_status_TA_funding_required = models.BooleanField(blank=True, null=True, default=False)
    CAS_status_TA_refunded = models.BooleanField(blank=True, null=True, default=False)
    CAS_status_credit_paper = models.CharField(max_length=1000, blank=True, null=True)
    CAS_status_credit_paper_start_date = models.DateField(blank=True, null=True)
    CAS_status_credit_paper_expected_end_date = models.DateField(blank=True, null=True)
    CAS_status_credit_paper_actual_end_date = models.DateField(blank=True, null=True)
    CAS_status_fee_letter = models.CharField(max_length=1000, blank=True, null=True)
    CAS_status_fee_letter_start_date = models.DateField(blank=True, null=True)
    CAS_status_fee_letter_expected_end_date = models.DateField(blank=True, null=True)
    CAS_status_fee_letter_actual_end_date = models.DateField(blank=True, null=True)
    GRL = models.CharField(max_length=1000, blank=True, null=True)
    GRL_start_date = models.DateField(blank=True, null=True)
    GRL_expected_end_date = models.DateField(blank=True, null=True)
    GRL_actual_end_date = models.DateField(blank=True, null=True)
    NDA = models.CharField(max_length=1000, blank=True, null=True)
    NDA_start_date = models.DateField(blank=True, null=True)
    NDA_expected_end_date = models.DateField(blank=True, null=True)
    NDA_actual_end_date = models.DateField(blank=True, null=True)
    NDA_Doc = models.CharField(max_length=256, blank=True, null=True)
    GRL_Doc = models.CharField(max_length=256, blank=True, null=True)
    mandateLetterDate = models.DateTimeField(blank=True, null=True)
    productSelected = models.CharField(max_length=256, blank=True, null=True)
    fundOption = models.CharField(max_length=256, blank=True, null=True)
    TAAmount = models.FloatField(blank=True, null=True)
    firstInstallmentComment = models.TextField(max_length=3000, blank=True, null=True)
    secondInstallmentComment = models.TextField(max_length=3000, blank=True, null=True)
    transactionDescription = models.TextField(max_length=3000, blank=True, null=True)
    LegalDDActualEndDateProcurement = models.DateTimeField(blank=True, null=True)
    E_S_ActualEndProcurement = models.DateTimeField(blank=True, null=True)
    TechComActualEndProcurement = models.DateTimeField(blank=True, null=True)
    sign_DRG_deed = models.CharField(max_length=100, blank=True, null=True)
    engagement_of_solicitor_for_bridge_to_bond = models.CharField(max_length=100, blank=True, null=True)
    bridge_to_bond_disbursement = models.CharField(max_length=100, blank=True, null=True)
    use_of_proceeds = models.TextField(max_length=3000, blank=True, null=True)
    project_period = models.CharField(max_length=1000, blank=True, null=True)
    status_update = models.TextField(max_length=3000, blank=True, null=True)
    next_steps = models.TextField(max_length=3000, blank=True, null=True)
    view = models.JSONField(default=list, blank=True, null=True)
    clientPrimaryEmail = models.CharField(max_length=100, blank=True, null=True)
    clientSecondaryEmail = models.CharField(max_length=100, blank=True, null=True)
    transaction_state = models.CharField(max_length=100, blank=True, null=True)
    last_modified_by = models.CharField(max_length=100, blank=True, null=True)
    modification_date = models.DateTimeField(blank=True, null=True)
    date_added = models.DateTimeField(default=timezone.now, blank=True, null=True)

    class Meta:
        ordering = ('-date_added',)

    def __str__(self):
        return self.project_name or str(self.uuid)


class Grant(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    development_partner = models.CharField(max_length=100, blank=True, null=True)
    transaction_name = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=50, blank=True, null=True)
    grant_type = models.CharField(max_length=50, blank=True, null=True)
    total_grant_required = models.FloatField(blank=True, null=True)
    total_grant_used = models.FloatField(blank=True, null=True)
    total_grant_left = models.FloatField(blank=True, null=True)
    purpose_of_grant = models.TextField(max_length=3000, blank=True, null=True)
    date_added = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ('date_added',)

    def __str__(self):
        return f"Grant: {self.development_partner} / {self.transaction_name}"


class Grant_partner(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner_name = models.CharField(max_length=100, blank=True, null=True)
    grant_type = models.CharField(max_length=100, blank=True, null=True)
    total_grant_amount = models.FloatField(blank=True, null=True)
    total_grant_available = models.FloatField(blank=True, null=True)
    currency = models.CharField(max_length=50, blank=True, null=True)
    date_added = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ('date_added',)

    def __str__(self):
        return f"partner name: {self.partner_name}"


class DevelopmentPlans(models.Model):
    planTermId = models.IntegerField(null=True, blank=True)
    planTypeId = models.IntegerField(null=True, blank=True)
    goalSummary = models.TextField(blank=True, null=True, max_length=3000)
    requiredResources = models.TextField(blank=True, null=True, max_length=3000)
    achievementApproach = models.TextField(blank=True, null=True, max_length=3000)
    potentialChallenges = models.TextField(blank=True, null=True, max_length=3000)
    solutionCriteria = models.TextField(blank=True, null=True, max_length=3000)
    status = models.TextField(blank=True, null=True, max_length=3000)
    progressMetrics = models.TextField(blank=True, null=True, max_length=3000)
    targetCompletionDate = models.DateTimeField(blank=True, null=True)
    actualCompletionDate = models.DateTimeField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True, max_length=3000)
    evidenceURL = models.FileField(upload_to="development-plans", max_length=255, blank=True, null=True)
    createdBy = models.CharField(max_length=255, blank=True, null=True)
    lastModifiedBy = models.CharField(max_length=255, blank=True, null=True)
    createdDate = models.DateTimeField(blank=True, null=True, default=timezone.now)
    lastModifiedDate = models.DateTimeField(blank=True, null=True)
    recordOwner = models.CharField(max_length=255, blank=True, null=True)

    def evidenceURLpath(self):
        return _full_url(self.evidenceURL)

    def __str__(self):
        return f"DevelopmentPlan: {self.goalSummary}"


class Deliverables(models.Model):
    deliverableTypeId = models.IntegerField(null=True, blank=True)
    taskDescription = models.TextField(blank=True, null=True, max_length=3000)
    startDate = models.DateTimeField(blank=True, null=True)
    endDate = models.DateTimeField(blank=True, null=True)
    evidence = models.FileField(upload_to="deliverables", max_length=255, blank=True, null=True)
    comment = models.TextField(blank=True, null=True, max_length=3000)
    status = models.TextField(blank=True, null=True, max_length=3000)
    createdBy = models.TextField(blank=True, null=True, max_length=3000)
    lastModifiedBy = models.TextField(blank=True, null=True, max_length=3000)
    createdDate = models.DateTimeField(blank=True, null=True, default=timezone.now)
    lastModifiedDate = models.DateTimeField(blank=True, null=True)
    recordOwner = models.TextField(blank=True, null=True, max_length=3000)

    def evidenceURLpath(self):
        return _full_url(self.evidence)

    def __str__(self):
        return f"Deliverable: {self.taskDescription}"


class MentorshipPlans(models.Model):
    financialYearId = models.IntegerField(null=True, blank=True)
    month = models.TextField(blank=True, null=True, max_length=3000)
    mentor = models.TextField(blank=True, null=True, max_length=3000)
    goals = models.TextField(blank=True, null=True, max_length=3000)
    actionPlans = models.TextField(blank=True, null=True, max_length=3000)
    targetCompletionDate = models.DateTimeField(blank=True, null=True)
    actualCompletionDate = models.DateTimeField(blank=True, null=True)
    progressMetrics = models.TextField(blank=True, null=True, max_length=3000)
    status = models.TextField(blank=True, null=True, max_length=3000)
    feedback = models.TextField(blank=True, null=True, max_length=3000)
    evidenceURL = models.FileField(upload_to="mentorship-plans", max_length=255, blank=True, null=True)
    createdBy = models.TextField(blank=True, null=True, max_length=3000)
    lastModifiedBy = models.TextField(blank=True, null=True, max_length=3000)
    createdDate = models.DateTimeField(blank=True, null=True, default=timezone.now)
    lastModifiedDate = models.DateTimeField(blank=True, null=True)
    recordOwner = models.TextField(blank=True, null=True, max_length=3000)

    def evidenceURLpath(self):
        return _full_url(self.evidenceURL)

    def __str__(self):
        return f"MentorshipPlan: {self.goals}"


class SkillAssessments(models.Model):
    skillDescription = models.TextField(blank=True, null=True, max_length=3000)
    currentStageId = models.IntegerField(blank=True, null=True)
    desiredStageId = models.IntegerField(blank=True, null=True)
    skillGapDetails = models.TextField(blank=True, null=True, max_length=3000)
    comment = models.TextField(blank=True, null=True, max_length=3000)
    actionPlan = models.TextField(blank=True, null=True, max_length=3000)
    createdBy = models.TextField(blank=True, null=True, max_length=3000)
    lastModifiedBy = models.TextField(blank=True, null=True, max_length=3000)
    recordOwner = models.TextField(blank=True, null=True, max_length=3000)

    def __str__(self):
        return f"SkillAssessment: {self.skillDescription}"


class SpeakingEngagements(models.Model):
    eventDescription = models.TextField(blank=True, null=True, max_length=3000)
    eventDate = models.DateTimeField(blank=True, null=True)
    country = models.TextField(blank=True, null=True, max_length=3000)
    eventCategory = models.TextField(blank=True, null=True, max_length=3000)
    representative = models.TextField(blank=True, null=True, max_length=3000)
    contactPerson = models.TextField(blank=True, null=True, max_length=3000)
    contactPhone = models.TextField(blank=True, null=True, max_length=3000)
    contactEmail = models.TextField(blank=True, null=True, max_length=3000)
    topicTheme = models.TextField(blank=True, null=True, max_length=3000)
    sponsorship = models.TextField(blank=True, null=True, max_length=3000)
    status = models.TextField(blank=True, null=True, max_length=3000)
    createdBy = models.TextField(blank=True, null=True, max_length=3000)
    lastModifiedBy = models.TextField(blank=True, null=True, max_length=3000)
    createdDate = models.DateTimeField(blank=True, null=True, default=timezone.now)
    lastModifiedDate = models.DateTimeField(blank=True, null=True)
    recordOwner = models.TextField(blank=True, null=True, max_length=3000)

    def __str__(self):
        return f"SpeakingEngagement: {self.eventDescription}"


class TrainingSchedules(models.Model):
    trainingStartDate = models.DateTimeField(blank=True, null=True)
    trainingTopic = models.TextField(blank=True, null=True, max_length=3000)
    trainingMethod = models.TextField(blank=True, null=True, max_length=3000)
    learningOutcome = models.TextField(blank=True, null=True, max_length=3000)
    dueDate = models.DateTimeField(blank=True, null=True)
    trainingInitiator = models.TextField(blank=True, null=True, max_length=3000)
    rating = models.IntegerField(blank=True, null=True)
    evidenceURL = models.FileField(upload_to="training-schedules", max_length=255, blank=True, null=True)
    recordOwner = models.TextField(blank=True, null=True, max_length=3000)
    status = models.TextField(blank=True, null=True, max_length=3000)
    department = models.TextField(blank=True, null=True, max_length=3000)
    isApproved = models.BooleanField(default=False)

    def evidenceURLpath(self):
        return _full_url(self.evidenceURL)

    def __str__(self):
        return f"TrainingSchedule: {self.trainingTopic}"


class AdminUsers(models.Model):
    userId = models.CharField(max_length=64, blank=True, null=True)
    roleId = models.CharField(max_length=64, blank=True, null=True)
    fullName = models.TextField(blank=True, null=True, max_length=3000)
    jobTitle = models.TextField(blank=True, null=True, max_length=3000)
    phoneNumber = models.TextField(blank=True, null=True, max_length=3000)
    address = models.TextField(blank=True, null=True, max_length=3000)
    departmentId = models.CharField(max_length=64, blank=True, null=True)
    businessUnitId = models.CharField(max_length=64, blank=True, null=True)
    createdBy = models.TextField(blank=True, null=True, max_length=3000)
    lastModifiedBy = models.TextField(blank=True, null=True, max_length=3000)
    createdDate = models.DateTimeField(blank=True, null=True, default=timezone.now)
    lastModifiedDate = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"AdminUser: {self.fullName}"
