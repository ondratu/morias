var M = M || {};

M.e = M.e || function(text){
    return $('<textarea/>').html(text).html();
}

M.Codebook = function(params){
    if (params == null) params = {};

    this.$btn_add = $(('add' in params ? params['add'] : 'a[add]'));
    this.$list = $(('list' in params ? params['list'] : 'table'));

    this.$btn_edit = $(('edit' in params ? params['edit'] : 'a[edit]'));
    this.$btn_delete = $(('delete' in params ? params['delete'] : 'a[delete]'));
    this.$btn_save = $(('save' in params ? params['save'] : 'button[save]'));
    this.$btn_cancel = $(('cancel' in params ? params['cancel'] : 'button[cancel]'));
    this.$input = $(('input' in params ? params['input'] : 'input[name=value]'));

    this.token = 'token' in params ? params['token'] : null;
    this.id = null;
    this.constructor();
}

M.Codebook.prototype.constructor = function () {
    this.$btn_add.on('click', this._add.bind(this));
    this.$btn_edit.on('click', this._edit.bind(this));
    this.$btn_delete.on('click', this._delete.bind(this));
    this.$btn_save.on('click', this._save.bind(this));
    this.$btn_cancel.on('click', this._cancel.bind(this));
}

M.Codebook.prototype._add = function(ev){
    var $target = $(ev.target);
    var value = this.$input.val();

    if (value) {
        var spinner = new M.Spinner();
        $.ajax({ url: $target.attr('add'),
                 type: 'post',
                 accepts : {'json': 'application/json', 'html': 'text/html'},
                 data: { 'value': value, 'token': this.token },
                 context: this,
                 success: function(data){
                    this.$input.val('');
                    this.$input.parent().removeClass('has-error');
                    setTimeout(function(){  // litle wrap for working history
    	                window.location.reload();
                        delete spinner.stop();
                    },0);
                 },
                 error: function(xhr, status, http_status) {
                    this.$input.parent().addClass('has-error');
                    if (xhr.status == 400){
                        alert(M._(xhr.responseJSON.reason));
                    } else {
                        alert(http_status);
                    }
                    delete spinner.stop();
                    console.error(http_status);
                 }
        });
    }
}

M.Codebook.prototype._edit = function(ev){
    if (this.id != null)
        return;

    this.id = $(ev.target).attr('edit');
    var $tr = $('tr[idx='+this.id+']', this.$list);
    var $value = $('td[value]', $tr);

    $value.html(
        $('<input>', {'type': 'text', 'name': 'value',
                      'class': 'form-control input-sm'})
            .val($value.attr('value')));

    // disable links and show buttons
    this.$btn_edit.addClass('disabled');
    this.$btn_delete.addClass('disabled');
    this.$btn_add.addClass('disabled');
    $('span[role=links]', $tr).css('display', 'none');
    $('span[role=buttons]', $tr).css('display', 'inline');
}

M.Codebook.prototype._save = function(ev){
    if (this.id == null)
        return;

    var $target = $(ev.target);
    var $tr = $('tr[idx='+this.id+']', this.$list);
    var $value = $('input[name=value]', $tr);
    var value = $value.val();

    if (value) {
        var spinner = new M.Spinner();
        $.ajax({ url: $target.attr('save'),
                 type: 'put',
                 accepts : {'json': 'application/json', 'html': 'text/html'},
                 data: { 'value': value, 'token': this.token },
                 context: this,
                 success: function(data){
                    $value.parent().removeClass('has-error');
                    setTimeout(function(){  // litle wrap for working history
    	                window.location.reload();
                        delete spinner.stop();
                    },0);
                 },
                 error: function(xhr, status, http_status) {
                    $value.parent().addClass('has-error');
                    if (xhr.status == 400){
                        alert(M._(xhr.responseJSON.reason));
                    } else {
                        alert(http_status);
                    }
                    delete spinner.stop();
                    console.error(http_status);
                 }
        });
    }
}

M.Codebook.prototype._cancel = function(ev){
    if (this.id == null)
        return;

    var $tr = $('tr[idx='+this.id+']', this.$list);
    var $value = $('td[value]', $tr);
    $value.html($value.attr('value'));
    this.id = null;

    // enable links and hide buttons
    this.$btn_edit.removeClass('disabled');
    this.$btn_delete.removeClass('disabled');
    this.$btn_add.removeClass('disabled');
    $('span[role=links]', $tr).css('display', 'inline');
    $('span[role=buttons]', $tr).css('display', 'none');
}

M.Codebook.prototype._delete = function(ev){
    if (this.id != null)
        return;

    var $target = $(ev.target);
    var id = $target.attr('idx');
    var $tr = $('tr[idx='+id+']', this.$list);
    var message = M._('mpm_sure_delete').replace("%s",
        $('td[value]', $tr).attr('value'));

    if (! confirm(message))
        return;

    var spinner = new M.Spinner();

    $.ajax({url: $target.attr('delete')+'?token='+encodeURIComponent(this.token),
            type: 'delete',
            accepts : {'json': 'application/json', 'html': 'text/html'},
            context: this,
            success: function(data){
                $tr.removeClass('text-danger');
                setTimeout(function(){  // litle wrap for working history
                    window.location.reload();
                    delete spinner.stop();
                },0);
            },
            error: function(xhr, status, http_status) {
                $tr.addClass('text-danger');
                if (xhr.status == 400){
                    alert(M._(xhr.responseJSON.reason));
                } else {
                    alert(http_status);
                }
                delete spinner.stop();
                console.error(http_status);
            }
    });
}
