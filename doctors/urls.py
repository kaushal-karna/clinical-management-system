from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Doctors
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctors/<int:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    path('doctors/add-doctor', views.add_doctor, name="add_doctor"),
    path('doctors/<int:doctor_id>/edit/', views.edit_doctor, name='edit_doctor'),
    path('doctors/<int:doctor_id>/delete/', views.delete_doctor, name='delete_doctor'),
    path('doctors/<int:doctor_id>/pay-commission/', views.pay_commission, name='pay_commission'),

    # Patient
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patients/add-patient', views.add_patient, name='add_patient'),
    path('patients/<int:patient_id>/edit/', views.edit_patient, name='edit_patient'),
    path('patients/<int:patient_id>/delete/', views.delete_patient, name='delete_patient'),
    

    # Appointments
    path('appointments/add-appointment/', views.add_appointment, name='add_appointment'),
    path('appointments/payment/', views.appointment_payment, name='appointment_payment'),
    path('appointments/<int:appointment_id>/pay-due/', views.pay_appointment_due, name='pay_appointment_due'),
]