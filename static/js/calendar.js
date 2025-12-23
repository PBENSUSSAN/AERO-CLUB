let calendar;
let selectedStart, selectedEnd;

// Functions must be global to be accessible by HTML onclick attributes
window.initCalendar = function (config) {
    // Make config globally available for submitReservation
    window.calendarConfig = config;

    var calendarEl = document.getElementById('calendar');
    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        locale: 'fr',
        selectable: true,
        selectMirror: true,
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        slotMinTime: '08:00:00',
        slotMaxTime: '20:00:00',
        allDaySlot: false,
        events: config.eventsUrl,

        select: function (info) {
            selectedStart = info.startStr;
            selectedEnd = info.endStr;
            document.getElementById('startInput').value = new Date(selectedStart).toLocaleString();
            document.getElementById('endInput').value = new Date(selectedEnd).toLocaleString();
            openModal();
        },

        eventClick: function (info) {
            alert('Réservation: ' + info.event.title + '\nPilote: ' + info.event.extendedProps.pilot);
        }
    });
    calendar.render();
};

window.openModal = function () {
    document.getElementById('bookingModal').classList.remove('hidden');
    document.getElementById('errorMessage').classList.add('hidden');
};

window.closeModal = function () {
    document.getElementById('bookingModal').classList.add('hidden');
    if (calendar) calendar.unselect();
};

window.submitReservation = function () {
    const aircraftId = document.getElementById('aircraftSelect').value;
    const config = window.calendarConfig;

    fetch(config.createReservationUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': config.csrfToken
        },
        body: JSON.stringify({
            aircraft: aircraftId,
            start: selectedStart,
            end: selectedEnd
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                closeModal();
                calendar.refetchEvents(); // Refresh calendar
            } else {
                const errorDiv = document.getElementById('errorMessage');
                errorDiv.textContent = data.error;
                errorDiv.classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Erreur technique');
        });
};
