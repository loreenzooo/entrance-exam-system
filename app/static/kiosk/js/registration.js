// Registration page: the full biometric consent notice opens in a modal, and
// the consent checkbox only unlocks once the applicant has read it.
//
// Without JavaScript the checkbox stays enabled, so the form still works -
// the server requires it either way.

(function () {
    var dialog = document.getElementById('consent-modal');
    var openButton = document.getElementById('open-consent');
    var acceptButton = document.getElementById('accept-consent');
    var checkbox = document.getElementById('consent-check');
    var hint = document.getElementById('consent-hint');

    if (!dialog || !openButton || !acceptButton || !checkbox) {
        return;  // not the registration page
    }

    checkbox.disabled = true;

    openButton.addEventListener('click', function () {
        dialog.showModal();
    });

    acceptButton.addEventListener('click', function () {
        dialog.close();
        checkbox.disabled = false;
        if (hint) {
            hint.hidden = true;
        }
        openButton.textContent = 'Review the biometric consent notice';
        checkbox.focus();
    });

    // Closing with Esc (or the backdrop) does not count as accepting, so the
    // box stays locked until the applicant presses "I understand".
})();
