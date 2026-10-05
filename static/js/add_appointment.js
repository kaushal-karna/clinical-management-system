document.addEventListener("DOMContentLoaded", function () {

    const paymentStatusField = document.getElementById("id_payment_status");
    const payHereBtn = document.getElementById("pay-here-btn");
    const doctorField = document.getElementById("id_doctor");
    const dateField = document.getElementById("id_appointment_date");
    const offDaysMessage = document.getElementById("doctor-off-days");

    // =================================================
    // SHOW / HIDE "PAY HERE" BUTTON AT THE BOTTOM
    // =================================================
    function checkPaymentStatus() {
        if (!paymentStatusField || !payHereBtn) return;

        if (paymentStatusField.value === "partial") {
            payHereBtn.style.display = "inline-flex";
        } else {
            payHereBtn.style.display = "none";
        }
    }

    if (paymentStatusField) {
        paymentStatusField.addEventListener("change", checkPaymentStatus);
        checkPaymentStatus(); // Run on initial page load
    }

    // =================================================
    // DOCTOR OFF-DAYS & FLATPICKR
    // =================================================
    if (!doctorField || !dateField) return;

    let doctorOffDays = {};
    const doctorOffDaysElement = document.getElementById("doctor-off-days-data");

    if (doctorOffDaysElement) {
        try {
            doctorOffDays = JSON.parse(doctorOffDaysElement.textContent);
        } catch (error) {
            console.error("Unable to read doctor off-days:", error);
            doctorOffDays = {};
        }
    }

    const dayNumbers = {
        sunday: 0,
        monday: 1,
        tuesday: 2,
        wednesday: 3,
        thursday: 4,
        friday: 5,
        saturday: 6
    };

    let datePicker = null;

    function getCurrentDoctorOffDays() {
        const doctorId = doctorField.value;
        if (!doctorId) return [];

        const offDaysString = doctorOffDays[doctorId] || "";
        return offDaysString
            .split(",")
            .map(function (day) { return day.trim().toLowerCase(); })
            .filter(function (day) { return day !== ""; });
    }

    function updateOffDayMessage() {
        if (!offDaysMessage) return;

        const offDays = getCurrentDoctorOffDays();

        if (!doctorField.value) {
            offDaysMessage.style.display = "none";
            offDaysMessage.textContent = "";
            return;
        }

        if (offDays.length === 0) {
            offDaysMessage.style.display = "block";
            offDaysMessage.style.background = "#f0fdf4";
            offDaysMessage.style.border = "1px solid #bbf7d0";
            offDaysMessage.style.color = "#166534";
            offDaysMessage.textContent = "This doctor has no configured off-days.";
            return;
        }

        const formattedDays = offDays
            .map(function (day) {
                return day.charAt(0).toUpperCase() + day.slice(1);
            })
            .join(", ");

        offDaysMessage.style.display = "block";
        offDaysMessage.style.background = "#fef2f2";
        offDaysMessage.style.border = "1px solid #fecaca";
        offDaysMessage.style.color = "#991b1b";
        offDaysMessage.textContent = "Doctor's off days: " + formattedDays;
    }

    function initializeDatePicker() {
        if (typeof flatpickr === "undefined") {
            console.error("Flatpickr is not loaded.");
            return;
        }

        if (datePicker) {
            datePicker.destroy();
            datePicker = null;
        }

        const offDays = getCurrentDoctorOffDays();
        const offDayNumbers = offDays
            .map(function (day) { return dayNumbers[day]; })
            .filter(function (dayNumber) { return dayNumber !== undefined; });

        datePicker = flatpickr(dateField, {
            dateFormat: "Y-m-d",
            altInput: true,
            altFormat: "F j, Y",
            minDate: "today",
            disableMobile: true,
            disable: [
                function (date) {
                    return offDayNumbers.includes(date.getDay());
                }
            ],
            locale: {
                firstDayOfWeek: 1
            }
        });
    }

    doctorField.addEventListener("change", function () {
        updateOffDayMessage();
        initializeDatePicker();
    });

    updateOffDayMessage();
    initializeDatePicker();
});