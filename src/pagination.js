(function() {
    var sections = document.querySelectorAll('section[data-date]');
    if (!sections.length) return;

    var dates = Array.from(sections, function(s) { return s.dataset.date; });
    var today = dates[0];

    var label = document.getElementById('date-label');
    var btnNewer = document.getElementById('btn-newer');
    var btnOlder = document.getElementById('btn-older');

    var current = '';

    function fmt(d) {
        var dt = new Date(d + 'T00:00:00');
        return dt.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    }

    function show(d) {
        var i;
        for (i = 0; i < sections.length; i++) {
            sections[i].hidden = sections[i].dataset.date !== d;
        }
        current = d;
        i = dates.indexOf(d);
        label.textContent = fmt(d) + (d === today ? ' (today)' : '');
        btnNewer.disabled = i === 0;
        btnOlder.disabled = i === dates.length - 1;
        if (d !== window.location.hash.slice(1)) {
            history.replaceState(null, '', '#' + d);
        }
    }

    btnNewer.onclick = function() {
        var i = dates.indexOf(current);
        if (i > 0) show(dates[i - 1]);
    };
    btnOlder.onclick = function() {
        var i = dates.indexOf(current);
        if (i < dates.length - 1) show(dates[i + 1]);
    };

    var hash = window.location.hash.slice(1);
    show(dates.indexOf(hash) !== -1 ? hash : today);
})();
