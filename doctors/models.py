from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


# User Profile
class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    specialization = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Doctor
class DoctorProfile(models.Model):
    SPECIALIZATION_CHOICES = [
        ("MBBS", "MBBS / General Physician"),
        ("CARDIOLOGIST", "Cardiologist"),
        ("DERMATOLOGIST", "Dermatologist"),
        ("ENT", "ENT Specialist"),
        ("GYNECOLOGIST", "Gynecologist"),
        ("NEUROLOGIST", "Neurologist"),
        ("ORTHOPEDIC", "Orthopedic"),
        ("PEDIATRICIAN", "Pediatrician"),
        ("PSYCHIATRIST", "Psychiatrist"),
        ("DENTIST", "Dentist"),
        ("OPHTHALMOLOGIST", "Ophthalmologist"),
        ("UROLOGIST", "Urologist"),
        ("GENERAL_SURGEON", "General Surgeon"),
        ("RADIOLOGIST", "Radiologist"),
        ("ANESTHESIOLOGIST", "Anesthesiologist"),
        ("OTHER", "Other"),
    ]

    COMMISSION_TYPE_CHOICES = [
        ("percentage", "Percentage (%)"),
        ("fixed", "Fixed Amount (Rs.)"),
    ]

    name = models.CharField(max_length=100, null=True)
    off_days = models.CharField(max_length=30)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    specialization = models.CharField(max_length=100, choices=SPECIALIZATION_CHOICES, default='MBBS')
    arrival_time = models.TimeField(null=True, blank=True)
    commission_type = models.CharField(max_length=20, choices=COMMISSION_TYPE_CHOICES, default='percentage')
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Dr. {self.name}"


# Patient
class Patient(models.Model):
    name = models.CharField(max_length=100, null=True)
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.name}"


# Appointment
class Appointment(models.Model):
    APPOINTMENT_STATUS_CHOICES = [
        ("waiting", "Waiting"),
        ("visited", "Visited"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("paid", "Paid"),
        ("partial", "Partial"),
        ("unpaid", "Unpaid"),
    ]

    TYPE_CHOICES = [
        ("regular", "Regular"),
        ("followup_paid", "FollowUpPaid"),
        ("followup_free", "FollowUpFree"),
    ]

    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    token_number = models.PositiveBigIntegerField(editable=False)

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid'
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=100, choices=APPOINTMENT_STATUS_CHOICES, default='visited')
    appointment_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='regular')
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Generate token only when creating a new appointment
        if not self.pk:
            last_appointment = (
                Appointment.objects.filter(
                    doctor=self.doctor,
                    appointment_date=self.appointment_date
                )
                .order_by("-token_number")
                .first()
            )
            self.token_number = (last_appointment.token_number + 1) if last_appointment else 1

        # Automatically assign doctor's consultation fee as total_amount if zero
        if (not self.total_amount or self.total_amount == Decimal("0.00")) and self.doctor and self.doctor.fee:
            self.total_amount = self.doctor.fee

        # ---------------------------------------
        # PAYMENT CALCULATION
        # ---------------------------------------
        if self.payment_status == "paid":
            self.paid_amount = self.total_amount
            self.remaining_amount = Decimal("0.00")

        elif self.payment_status == "partial":
            if self.paid_amount < Decimal("0.00"):
                self.paid_amount = Decimal("0.00")
            if self.paid_amount >= self.total_amount:
                self.paid_amount = self.total_amount
                self.payment_status = "paid"
                self.remaining_amount = Decimal("0.00")
            else:
                self.remaining_amount = self.total_amount - self.paid_amount

        else:  # unpaid
            self.paid_amount = Decimal("0.00")
            self.remaining_amount = self.total_amount

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Token #{self.token_number} - {self.doctor} - {self.patient} - {self.appointment_date}"


# Commission Payment
class CommissionPayment(models.Model):
    STATUS_CHOICES = [
        ("paid", "Paid"),
        ("pending", "Pending"),
        ("cancelled", "Cancelled"),
    ]

    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='commission_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.doctor} - Rs. {self.amount} - {self.payment_date}"