// Kiosk home clock: the exam-day time in the corner.
// Kept tiny and dependency-free so it can run all day on a tablet.

(function () {
    var timeEl = document.getElementById('home-clock-time');
    var dateEl = document.getElementById('home-clock-date');

    if (!timeEl) {
        return;
    }

    function tick() {
        var now = new Date();
        var hours = now.getHours();
        var minutes = String(now.getMinutes()).padStart(2, '0');
        var suffix = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12 || 12;

        timeEl.textContent = hours + ':' + minutes + ' ' + suffix;
        dateEl.textContent = now.toLocaleDateString(undefined, {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }

    tick();
    // 1s keeps the minute accurate without noticeable timer drift.
    setInterval(tick, 1000);
})();
