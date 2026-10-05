from django.contrib import admin

# Register your models here.
from .models import DoctorProfile, Patient, Appointment

admin.site.register(DoctorProfile)
admin.site.register(Patient)
admin.site.register(Appointment)