from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)
from django.urls import reverse
from django.http import HttpResponse
from django.db.models import Q, Sum
from decimal import Decimal

from .models import (
    DoctorProfile,
    Patient,
    Appointment,
    CommissionPayment
)
from .forms import (
    DoctorProfileForm,
    PatientForm,
    AppointmentForm,
    AppointmentPaymentForm,
    CommissionPaymentForm
)


# Home
def home(request):
    return HttpResponse("This is homepage")


# Homepage
def homepage(request):
    return render(request, 'homepage.html')


# Doctor List
def doctor_list(request):
    doctors = DoctorProfile.objects.all().order_by('name')
    return render(request, 'doctors/doctor_list.html', {'doctors': doctors})


# Patient List
def patient_list(request):
    patients = Patient.objects.all().order_by('name')
    return render(request, 'patients/patient_list.html', {'patients': patients})


# Dashboard
def dashboard(request):
    doctor_count = DoctorProfile.objects.count()
    patient_count = Patient.objects.count()
    appointment_count = Appointment.objects.count()

    paid_count = Appointment.objects.filter(payment_status="paid").count()
    unpaid_count = Appointment.objects.filter(payment_status="unpaid").count()
    waiting_count = Appointment.objects.filter(status="waiting").count()
    visited_count = Appointment.objects.filter(status="visited").count()

    doctors = DoctorProfile.objects.all()[:3]
    patients = Patient.objects.all()[:3]
    appointments = Appointment.objects.select_related('doctor', 'patient').all()[:3]

    context = {
        'doctor_count': doctor_count,
        'patient_count': patient_count,
        'appointment_count': appointment_count,
        'paid_count': paid_count,
        'unpaid_count': unpaid_count,
        'waiting_count': waiting_count,
        'visited_count': visited_count,
        'doctors': doctors,
        'patients': patients,
        'appointments': appointments,
    }
    return render(request, 'dashboard.html', context)


# Add Doctor
def add_doctor(request):
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = DoctorProfileForm()

    return render(request, 'doctors/add_doctor.html', {'form': form})


# Doctor Detail
def doctor_detail(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    appointments = doctor.appointments.select_related('patient').order_by('-appointment_date', 'token_number')

    total_appointments = appointments.count()
    waiting_appointments = appointments.filter(status='waiting').count()
    visited_appointments = appointments.filter(status='visited').count()
    paid_appointments = appointments.filter(payment_status='paid').count()
    unpaid_appointments = appointments.filter(payment_status='unpaid').count()

    patient_query = request.GET.get('patient', '').strip()
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    filtered_appointments = appointments
    if patient_query:
        filtered_appointments = filtered_appointments.filter(patient__name__icontains=patient_query)
    if from_date:
        filtered_appointments = filtered_appointments.filter(appointment_date__gte=from_date)
    if to_date:
        filtered_appointments = filtered_appointments.filter(appointment_date__lte=to_date)

    # =========================================================================
    # Commission Calculation (Calculated whenever money is paid)
    # =========================================================================
    consultation_fee = doctor.fee or Decimal('0.00')
    commission_rate = doctor.commission or Decimal('0.00')

    # Base commission for standard full appointment
    if doctor.commission_type == 'percentage':
        commission_per_appointment = (
            consultation_fee * commission_rate / Decimal('100')
        )
    else:
        commission_per_appointment = commission_rate

    # Calculate actual commission earned based on money received
    total_commission = Decimal('0.00')

    for appt in filtered_appointments:
        paid = appt.paid_amount or Decimal('0.00')

        # If appointment is not cancelled and patient has paid (Full or Partial)
        if appt.status != 'cancelled' and paid > Decimal('0.00'):
            if doctor.commission_type == 'percentage':
                appt.earned_commission = (paid * commission_rate) / Decimal('100')
            else:
                if consultation_fee > Decimal('0.00'):
                    appt.earned_commission = (paid / consultation_fee) * commission_rate
                else:
                    appt.earned_commission = commission_rate
        else:
            appt.earned_commission = Decimal('0.00')

        total_commission += appt.earned_commission

    # Commission payments history & balances
    commission_payments = doctor.commission_payments.all().order_by('-payment_date')
    total_commission_paid = (
        commission_payments
        .filter(status='paid')
        .aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    total_commission_pending = total_commission - total_commission_paid
    if total_commission_pending < Decimal('0.00'):
        total_commission_pending = Decimal('0.00')

    context = {
        'doctor': doctor,
        'appointments': filtered_appointments,
        'total_appointments': total_appointments,
        'filtered_appointment_count': filtered_appointments.count(),
        'waiting_appointments': waiting_appointments,
        'visited_appointments': visited_appointments,
        'paid_appointments': paid_appointments,
        'unpaid_appointments': unpaid_appointments,
        'commission_per_appointment': commission_per_appointment,
        'total_commission': total_commission,
        'commission_payments': commission_payments,
        'total_commission_paid': total_commission_paid,
        'total_commission_pending': total_commission_pending,
        'patient_query': patient_query,
        'from_date': from_date,
        'to_date': to_date,
    }
    return render(request, 'doctors/doctor_detail.html', context)


# Pay Commission
def pay_commission(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    consultation_fee = doctor.fee or Decimal('0.00')
    commission_rate = doctor.commission or Decimal('0.00')

    # Total commission earned from all non-cancelled appointments with payments
    total_commission = Decimal('0.00')
    appointments = doctor.appointments.exclude(status='cancelled')

    for appt in appointments:
        paid = appt.paid_amount or Decimal('0.00')
        if paid > Decimal('0.00'):
            if doctor.commission_type == 'percentage':
                total_commission += (paid * commission_rate) / Decimal('100')
            else:
                if consultation_fee > Decimal('0.00'):
                    total_commission += (paid / consultation_fee) * commission_rate
                else:
                    total_commission += commission_rate

    total_commission_paid = (
        doctor.commission_payments
        .filter(status='paid')
        .aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    pending_amount = max(total_commission - total_commission_paid, Decimal('0.00'))

    if request.method == 'POST':
        form = CommissionPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.doctor = doctor
            payment.status = 'paid'

            if payment.amount > pending_amount:
                form.add_error('amount', f'Payment cannot exceed pending amount of Rs. {pending_amount:.2f}.')
            elif payment.amount <= 0:
                form.add_error('amount', 'Payment amount must be greater than zero.')
            else:
                payment.save()
                return redirect('doctor_detail', doctor_id=doctor.id)
    else:
        form = CommissionPaymentForm(initial={'amount': pending_amount})

    return render(request, 'doctors/pay_commission.html', {
        'doctor': doctor,
        'form': form,
        'pending_amount': pending_amount,
    })


# Edit Doctor
def edit_doctor(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect('doctor_detail', doctor_id=doctor.id)
    else:
        form = DoctorProfileForm(instance=doctor)
    return render(request, 'doctors/edit_doctor.html', {'form': form, 'doctor': doctor})


# Delete Doctor
def delete_doctor(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    if request.method == 'POST':
        doctor.delete()
        return redirect('dashboard')
    return redirect('doctor_detail', doctor_id=doctor.id)


# Add Patient
def add_patient(request):
    next_url = request.POST.get('next') or request.GET.get('next')
    if request.method == 'POST':
        form = PatientForm(request.POST)
        action = request.POST.get('action')
        if form.is_valid():
            patient = form.save()
            if action == 'save_appointment':
                return redirect(f"{reverse('add_appointment')}?patient={patient.id}")
            elif action == 'save':
                return redirect('patient_detail', patient_id=patient.id)
            elif next_url == 'appointment':
                return redirect(f"{reverse('add_appointment')}?patient={patient.id}")
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = PatientForm()
    return render(request, 'patients/add_patient.html', {'form': form})


# Edit Patient
def edit_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = PatientForm(instance=patient)
    return render(request, 'patients/edit_patient.html', {'form': form, 'patient': patient})


# Delete Patient
def delete_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    if request.method == 'POST':
        patient.delete()
        return redirect('patient_list')
    return redirect('patient_detail', patient_id=patient.id)


# # Patient Detail
# def patient_detail(request, patient_id):
#     patient = get_object_or_404(Patient, id=patient_id)
#     appointments = patient.appointments.select_related('doctor').order_by('-appointment_date', 'token_number')
#     doctor_count = appointments.values('doctor').distinct().count()

#     total_appointments = appointments.count()
#     waiting_appointments = appointments.filter(status='waiting').count()
#     visited_appointments = appointments.filter(status='visited').count()
#     cancelled_appointments = appointments.filter(status='cancelled').count()
#     paid_appointments = appointments.filter(payment_status='paid').count()
#     unpaid_appointments = appointments.filter(payment_status='unpaid').count()

#     doctor_query = request.GET.get('doctor', '').strip()
#     from_date = request.GET.get('from_date', '')
#     to_date = request.GET.get('to_date', '')

#     filtered_appointments = appointments
#     if doctor_query:
#         filtered_appointments = filtered_appointments.filter(doctor__name__icontains=doctor_query)
#     if from_date:
#         filtered_appointments = filtered_appointments.filter(appointment_date__gte=from_date)
#     if to_date:
#         filtered_appointments = filtered_appointments.filter(appointment_date__lte=to_date)

#     context = {
#         'patient': patient,
#         'doctor_count': doctor_count,
#         'appointments': filtered_appointments,
#         'total_appointments': total_appointments,
#         'filtered_appointment_count': filtered_appointments.count(),
#         'waiting_appointments': waiting_appointments,
#         'visited_appointments': visited_appointments,
#         'cancelled_appointments': cancelled_appointments,
#         'paid_appointments': paid_appointments,
#         'unpaid_appointments': unpaid_appointments,
#         'doctor_query': doctor_query,
#         'from_date': from_date,
#         'to_date': to_date,
#     }
#     return render(request, 'patients/patient_detail.html', context)


# Patient Detail
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    # 1. DEFINE 'appointments' FIRST AT THE TOP
    appointments = patient.appointments.select_related('doctor').order_by(
        '-appointment_date', 'token_number'
    )

    # 2. ONLY COUNT VISITED DOCTORS AND VISITED APPOINTMENTS (0 if waiting/cancelled)
    visited_appointments_qs = appointments.filter(status='visited')
    doctor_count = visited_appointments_qs.values('doctor').distinct().count()
    total_visits = visited_appointments_qs.count()

    # 3. OVERALL APPOINTMENT COUNTS
    total_appointments = appointments.count()
    waiting_appointments = appointments.filter(status='waiting').count()
    visited_appointments = total_visits
    cancelled_appointments = appointments.filter(status='cancelled').count()
    paid_appointments = appointments.filter(payment_status='paid').count()
    partial_appointments = appointments.filter(payment_status='partial').count()
    unpaid_appointments = appointments.filter(payment_status__in=['unpaid', 'partial']).count()

    # 4. PENDING & PAID DUES CALCULATION
    active_appointments = appointments.exclude(status='cancelled').exclude(appointment_type='followup_free')
    total_pending_amount = Decimal('0.00')
    total_paid_amount = Decimal('0.00')

    for appt in active_appointments:
        total_fee = appt.total_amount if (appt.total_amount and appt.total_amount > Decimal('0.00')) else (appt.doctor.fee or Decimal('0.00'))
        paid = appt.paid_amount or Decimal('0.00')

        if appt.payment_status == 'paid':
            total_paid_amount += total_fee
        elif appt.payment_status == 'partial':
            total_paid_amount += paid
            total_pending_amount += max(total_fee - paid, Decimal('0.00'))
        else:  # unpaid
            total_pending_amount += total_fee

    # 5. FILTERS FROM URL
    doctor_query = request.GET.get('doctor', '').strip()
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    filtered_appointments = appointments
    if doctor_query:
        filtered_appointments = filtered_appointments.filter(doctor__name__icontains=doctor_query)
    if from_date:
        filtered_appointments = filtered_appointments.filter(appointment_date__gte=from_date)
    if to_date:
        filtered_appointments = filtered_appointments.filter(appointment_date__lte=to_date)

    context = {
        'patient': patient,
        'doctor_count': doctor_count,
        'total_visits': total_visits,
        'appointments': filtered_appointments,
        'total_appointments': total_appointments,
        'filtered_appointment_count': filtered_appointments.count(),
        'waiting_appointments': waiting_appointments,
        'visited_appointments': visited_appointments,
        'cancelled_appointments': cancelled_appointments,
        'paid_appointments': paid_appointments,
        'partial_appointments': partial_appointments,
        'unpaid_appointments': unpaid_appointments,
        'total_pending_amount': total_pending_amount,
        'total_paid_amount': total_paid_amount,
        'doctor_query': doctor_query,
        'from_date': from_date,
        'to_date': to_date,
    }
    return render(request, 'patients/patient_detail.html', context)


# Pay Appointment Due (For Partial or Unpaid Appointments)
def pay_appointment_due(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related('doctor', 'patient'),
        id=appointment_id
    )

    # Ensure total_amount is accurate
    total_fee = appointment.total_amount if (appointment.total_amount and appointment.total_amount > Decimal('0.00')) else (appointment.doctor.fee or Decimal('0.00'))
    current_paid = appointment.paid_amount or Decimal('0.00')
    remaining_due = max(total_fee - current_paid, Decimal('0.00'))

    # If already fully cleared
    if appointment.payment_status == 'paid' or remaining_due <= Decimal('0.00'):
        return redirect('patient_detail', patient_id=appointment.patient.id)

    error = None

    if request.method == 'POST':
        pay_amount_str = request.POST.get('pay_amount', '').strip()
        try:
            pay_amount = Decimal(pay_amount_str)
            if pay_amount <= Decimal('0.00'):
                error = "Payment amount must be greater than zero."
            elif pay_amount > remaining_due:
                error = f"Payment cannot exceed the remaining due of Rs. {remaining_due:.2f}."
            else:
                appointment.total_amount = total_fee
                appointment.paid_amount = current_paid + pay_amount
                appointment.remaining_amount = max(total_fee - appointment.paid_amount, Decimal('0.00'))

                if appointment.remaining_amount <= Decimal('0.00'):
                    appointment.payment_status = 'paid'
                else:
                    appointment.payment_status = 'partial'

                appointment.save()
                return redirect('patient_detail', patient_id=appointment.patient.id)
        except (ValueError, TypeError, ArithmeticError):
            error = "Please enter a valid payment amount."

    return render(
        request,
        'patients/pay_appointment_due.html',
        {
            'appointment': appointment,
            'total_fee': total_fee,
            'current_paid': current_paid,
            'remaining_due': remaining_due,
            'error': error,
        }
    )
    
    

# Add Appointment
def add_appointment(request):
    selected_patient_id = request.GET.get('patient')

    # Read temporary draft data from session if returning from payment page
    draft_data = request.session.get('draft_appointment', None)
    partial_payment_info = None

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        action = request.POST.get('action')

        # USER CLICKED "PAY HERE" BUTTON (AT LAST)
        if action == 'pay_here':
            doctor_id = request.POST.get('doctor')
            if not doctor_id:
                form.add_error('doctor', 'Please select a doctor to calculate the charges before proceeding to payment.')
                return render(request, 'appointments/add_appointment.html', {'form': form})

            # Save form inputs into session so no user input is lost
            request.session['draft_appointment'] = request.POST.dict()
            return redirect('appointment_payment')

        # USER CLICKED "SAVE APPOINTMENT"
        if form.is_valid():
            appointment = form.save(commit=False)

            # Auto-assign doctor's fee to total_amount
            if appointment.doctor and appointment.doctor.fee:
                appointment.total_amount = appointment.doctor.fee
            else:
                appointment.total_amount = Decimal('0.00')

            # Payment handling
            if appointment.payment_status == 'paid':
                appointment.paid_amount = appointment.total_amount
            elif appointment.payment_status == 'unpaid':
                appointment.paid_amount = Decimal('0.00')
            elif appointment.payment_status == 'partial':
                submitted_paid = request.POST.get('paid_amount') or (draft_data.get('paid_amount') if draft_data else None)

                if not submitted_paid or Decimal(str(submitted_paid)) <= Decimal('0.00'):
                    form.add_error('payment_status', 'Please click "Pay Here" to specify the partial payment amount.')
                    return render(request, 'appointments/add_appointment.html', {'form': form})

                appointment.paid_amount = Decimal(str(submitted_paid))

            appointment.save()

            if 'draft_appointment' in request.session:
                del request.session['draft_appointment']

            return redirect('dashboard')

    else:
        # If returning from payment form page, reload saved fields
        if draft_data:
            form = AppointmentForm(initial=draft_data)
            doctor_id = draft_data.get('doctor')
            paid_amount_str = draft_data.get('paid_amount')

            if doctor_id and paid_amount_str:
                try:
                    doctor = DoctorProfile.objects.get(id=doctor_id)
                    fee = doctor.fee or Decimal('0.00')
                    paid = Decimal(str(paid_amount_str))
                    partial_payment_info = {
                        'paid_amount': paid,
                        'total_amount': fee,
                        'remaining_amount': max(fee - paid, Decimal('0.00')),
                    }
                except DoctorProfile.DoesNotExist:
                    pass
        elif selected_patient_id:
            patient = get_object_or_404(Patient, id=selected_patient_id)
            form = AppointmentForm(initial={'patient': patient})
        else:
            form = AppointmentForm()

    return render(
        request,
        'appointments/add_appointment.html',
        {
            'form': form,
            'partial_payment_info': partial_payment_info,
        }
    )


# Appointment Payment
def appointment_payment(request):
    draft_data = request.session.get('draft_appointment')
    if not draft_data:
        return redirect('add_appointment')

    doctor_id = draft_data.get('doctor')
    patient_id = draft_data.get('patient')

    doctor = get_object_or_404(DoctorProfile, id=doctor_id) if doctor_id else None
    patient = Patient.objects.filter(id=patient_id).first() if patient_id else None
    appointment_date = draft_data.get('appointment_date', '')

    total_fee = doctor.fee if (doctor and doctor.fee) else Decimal('0.00')
    error = None

    if request.method == 'POST':
        paid_amount_str = request.POST.get('paid_amount', '').strip()
        try:
            paid_amount = Decimal(paid_amount_str)
            if paid_amount <= Decimal('0.00'):
                error = "Paid amount must be greater than zero."
            elif paid_amount >= total_fee:
                error = f"For partial payment, paid amount must be less than total fee of Rs. {total_fee:.2f}."
            else:
                # Save configured paid amount to the session draft
                draft_data['paid_amount'] = str(paid_amount)
                request.session['draft_appointment'] = draft_data
                request.session.modified = True

                # Redirect BACK to add_appointment to review everything and submit
                return redirect('add_appointment')
        except (ValueError, TypeError, ArithmeticError):
            error = "Please enter a valid numeric amount."

    current_paid = draft_data.get('paid_amount', '')

    return render(
        request,
        'appointments/payment_form.html',
        {
            'doctor': doctor,
            'patient': patient,
            'appointment_date': appointment_date,
            'total_fee': total_fee,
            'current_paid': current_paid,
            'error': error,
        }
    )