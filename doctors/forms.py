from django import forms
from decimal import Decimal
from .models import DoctorProfile, Patient, Appointment, CommissionPayment


class DoctorProfileForm(forms.ModelForm):

    other_specialization = forms.CharField(
        required=False,
        label="Specify Other Specialization",
        widget=forms.TextInput(
            attrs={
                'id': 'id_other_specialization',
                'class': 'form-control',
                'placeholder': 'Enter doctor specialization',
                'autocomplete': 'off',
            }
        )
    )

    class Meta:
        model = DoctorProfile
        fields = [
            'name',
            'off_days',
            'fee',
            'specialization',
            'other_specialization',
            'arrival_time',
            'commission_type',
            'commission',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter doctor name'}),
            'off_days': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: Sunday, Monday'}),
            'fee': forms.NumberInput(attrs={'class': 'form-control no-scroll', 'placeholder': 'Enter consultation fee', 'step': '0.01', 'id': 'id_fee'}),
            'specialization': forms.Select(attrs={'class': 'form-control', 'id': 'id_specialization'}),
            'arrival_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'commission_type': forms.Select(attrs={'class': 'form-control', 'id': 'id_commission_type'}),
            'commission': forms.NumberInput(attrs={'class': 'form-control no-scroll', 'placeholder': 'Enter commission', 'step': '0.01', 'id': 'id_commission'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Build a lookup map of all valid choice keys and labels (uppercase)
        choice_map = {}
        for code, label in DoctorProfile.SPECIALIZATION_CHOICES:
            if code != 'OTHER':
                choice_map[code.upper()] = code
                choice_map[label.upper()] = code

        if self.instance and self.instance.pk:
            current_spec = (self.instance.specialization or "").strip()
            
            # 1. If it matches a standard specialization (like MBBS or MBBS / General Physician)
            if current_spec.upper() in choice_map:
                self.initial['specialization'] = choice_map[current_spec.upper()]
                self.initial['other_specialization'] = ''
            # 2. Only if it is truly a custom specialization (not in the standard list)
            elif current_spec and current_spec.upper() != 'OTHER':
                self.initial['specialization'] = 'OTHER'
                self.initial['other_specialization'] = current_spec
            else:
                self.initial['specialization'] = 'MBBS'
                self.initial['other_specialization'] = ''
        else:
            # Default for new doctors: MBBS
            self.initial['specialization'] = 'MBBS'
            self.initial['other_specialization'] = ''

    def clean(self):
        cleaned_data = super().clean()
        specialization = cleaned_data.get("specialization")
        other_specialization = cleaned_data.get("other_specialization")

        if specialization == "OTHER":
            if not other_specialization or not other_specialization.strip():
                self.add_error("other_specialization", "Please specify the specialization.")

        return cleaned_data

    def save(self, commit=True):
        doctor = super().save(commit=False)
        specialization = self.cleaned_data.get("specialization")
        other_specialization = self.cleaned_data.get("other_specialization")

        # If OTHER was chosen, save the custom text; otherwise save standard code (e.g. MBBS)
        if specialization == "OTHER" and other_specialization:
            doctor.specialization = other_specialization.strip()
        else:
            doctor.specialization = specialization

        if commit:
            doctor.save()

        return doctor 

    
class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter full name'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Enter your Phone Number'}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        # Note: paid_amount and total_amount are excluded to keep Add Appointment clean
        fields = [
            'doctor',
            'patient',
            'appointment_date',
            'payment_status',
            'appointment_type',
            'status',
            'notes',
        ]

        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-control', 'id': 'id_doctor'}),
            'patient': forms.Select(attrs={'class': 'form-control', 'id': 'id_patient'}),
            'appointment_date': forms.DateInput(
                attrs={
                    'type': 'text',
                    'class': 'form-control',
                    'id': 'id_appointment_date',
                    'autocomplete': 'off',
                    'placeholder': 'Select appointment date',
                }
            ),
            'payment_status': forms.Select(attrs={'class': 'form-control', 'id': 'id_payment_status'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'appointment_type': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'placeholder': 'Enter any additional notes...', 'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get("doctor")
        appointment_date = cleaned_data.get("appointment_date")

        # Off-day check
        if doctor and appointment_date:
            off_days = doctor.off_days or ""
            off_days_list = [day.strip().lower() for day in off_days.split(",") if day.strip()]
            appointment_day = appointment_date.strftime("%A").lower()

            if appointment_day in off_days_list:
                self.add_error(
                    "appointment_date",
                    f"{doctor} is not available on {appointment_date.strftime('%A')}. Please select another date."
                )

        return cleaned_data


class AppointmentPaymentForm(forms.ModelForm):
    """Used strictly in the dedicated payment page"""
    class Meta:
        model = Appointment
        fields = ['paid_amount']
        widgets = {
            'paid_amount': forms.NumberInput(
                attrs={
                    'class': 'form-control no-scroll',
                    'step': '0.01',
                    'min': '0.01',
                    'placeholder': 'Enter amount paid',
                    'id': 'id_paid_amount',
                    'style': 'width: 100%; padding: 10px; font-size: 16px; border: 1px solid #cbd5e1; border-radius: 6px;',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paid_amount'].required = True

    def clean_paid_amount(self):
        paid = self.cleaned_data.get('paid_amount')
        total = self.instance.total_amount or Decimal('0.00')

        if paid is None or paid <= Decimal('0.00'):
            raise forms.ValidationError("Paid amount must be greater than zero.")

        if paid > total:
            raise forms.ValidationError(f"Paid amount cannot exceed total doctor charge of Rs. {total:.2f}")

        return paid


class CommissionPaymentForm(forms.ModelForm):
    class Meta:
        model = CommissionPayment
        fields = ['amount', 'payment_date']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'no-scroll', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }