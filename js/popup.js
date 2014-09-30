var M = M || {};

M.alert = function(message) {
    var dialog = $('#alert');
    $('.popup-message', dialog).text(message);
    dialog.modal('show');
}

M.confirm = function(message, fn) {
    M.confirm._fn = fn || function (){};
    var dialog = $('#confirm');
    $('.popup-message', dialog).text(message);
    dialog.modal('show');
}

$(document).ready(function() {
    $('button[data-ok]', $('#confirm')).click( function() {
        M.confirm._fn(true);
        $('#confirm').modal('hide');
    });
});
