var M = M || {};

M.Options = function (params) {
    if (params == null) params = {};
    this.$list = $(('list' in params ? params['list'] : 'table'));

    this.constructor();
}

M.Options.prototype.constructor = function () {
    $('a[edit]', this.$list).on('click', this._edit.bind(this));
}

/* Replace value of cell to input box with select of default values */
M.Options.prototype._edit = function (ev) {
    var $target = $(ev.target);
    var $value = $('div[role=value]', $target.parent().parent())
    var value = $value.text().trim();

    var $save = $('<button/>', { type: 'button',
                     'class':'btn btn-default btn-sm',
                     title: M._('Save'),
                     save: $target.attr('edit') })
        .append($('<i>', { 'class': 'fa fa-save' }))
        .on('click', this._save.bind(this))
        .replaceAll($target);
    $('<button/>', { type: 'button',
                     'class':'btn btn-default btn-sm',
                     title: M._('Cancel'),
                     save: $target.attr('edit') })
        .append($('<i>', { 'class': 'fa fa-close' }))
        .on('click', function(ev) {this._value($value, value, $save)}.bind(this))
        .appendTo($save.parent());

    $value.html(
        $('<input>', { type: 'text', 'class': 'form-control input-sm' })
            .keydown(function(ev) {
                if (ev.keyCode == 13) $save.click();
                else if (ev.keyCode == 27) this._value($value, value, $save);
            }.bind(this))
            .val(value));
    $('<span>', { 'class': 'input-group-addon' })
        .append($('<i>', { 'class': 'fa fa-angle-down' }))
        .appendTo($value);
}

/* Replace cell value back to value and save button to edit link */
M.Options.prototype._value = function ($value, value, $save) {
    $value.text(value);
    $($save.parent()).html(
        $('<a>', { edit: $save.attr('save') })
            .text(M._('Edit'))
            .on('click', this._edit.bind(this)));
}

M.Options.prototype._save = function (ev) {
    var $target = $(ev.target);
    var $input = $('input', $target.parent().parent());

    $.ajax({ url: $target.attr('save'),
             type: 'put',
             accepts : {json: 'application/json', html: 'text/html'},
             data: { value: $input.val() },
             context: this,
             success: function(data){
                this._value($($input.parent()), data.value, $target);
             },
             statusCode: {
                400: function (data) {
                    M.alert(M._(data.responseJSON.reason));
                    $input.addClass('has-error');
                }
             },
             error: function(xhr, status, http_status) {
                console.error(status);
                console.error(http_status);
             }
    });
}
