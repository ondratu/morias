var M = M || {};

M.e = M.e || function(text){
    return $('<textarea/>').html(text).html();
}

M.Redirect = function(params){
    if (params == null) params = {};

    this.$btn_add = $(('add' in params ? params['add'] : 'a[add]'));
    this.$list = $(('list' in params ? params['list'] : 'table'));

    this.$btn_edit = $(('edit' in params ? params['edit'] : 'a[edit]'));
    this.$btn_delete = $(('delete' in params ? params['delete'] : 'a[delete]'));
    this.$btn_save = $(('save' in params ? params['save'] : 'button[save]'));
    this.$btn_cancel = $(('cancel' in params ? params['cancel'] : 'button[cancel]'));
    this.$input_src = $(('input_src' in params ? params['input_src'] : 'input[name=src]'));
    this.$input_dst = $(('input_dst' in params ? params['input_dst'] : 'input[name=dst]'));
    this.$input_code = $(('input_code' in params ? params['input_code'] : 'select[name=code]'));
    this.$input_state = $(('input_state' in params ? params['input_state'] : 'input[name=state]'));

    this.token = 'token' in params ? params['token'] : null;
    this.id = null;
    this.constructor();
}

M.Redirect.prototype.constructor = function () {
    this.$btn_add.on('click', this._add.bind(this));
    this.$btn_edit.on('click', this._edit.bind(this));
    this.$btn_delete.on('click', this._delete.bind(this));
    this.$btn_save.on('click', this._save.bind(this));
    this.$btn_cancel.on('click', this._cancel.bind(this));
}

M.Redirect.prototype._add = function(ev){
    var $target = $(ev.target);
    var src = this.$input_src.val();
    var dst = this.$input_dst.val();
    var code = this.$input_code.val();
    var state = (this.$input_state[0].checked) ? 1 : 0;

    var spinner = new M.Spinner();
    $.ajax({url: $target.attr('add'),
            type: 'post',
            accepts : {'json': 'application/json', 'html': 'text/html'},
            data: {'src': src, 'dst': dst, 'code': code, 'state': state, 'token': this.token},
            context: this,
            success: function(data){
                this.$input_src.val('');
                this.$input_src.parent().removeClass('has-error');
                this.$input_dst.val('');
                this.$input_dst.parent().removeClass('has-error');
                this.$input_code.val(301);
                this.$input_state.attr('checked', 'checked');
                setTimeout(function(){  // litle wrap for working history
    	            window.location.reload();
                    delete spinner.stop();
                },0);
            },
            error: function(xhr, status, http_status) {
                if (xhr.status == 400){
                    var src_errs = ['empty_src', 'bad_src', 'src_exist'];
                    var reason = xhr.responseJSON.reason;
                    if (src_errs.find(function(it){return it == reason}))
                        this.$input_src.parent().addClass('has-error');
                    else if (reason == 'empty_dst')
                        this.$input_dst.parent().addClass('has-error');
                    alert(M._(reason));
                } else {
                    this.$btn_add.parent().addClass('has-error');
                    alert(http_status);
                }
                delete spinner.stop();
                console.error(http_status);
            }
        });
}

M.Redirect.prototype._edit = function(ev){
    if (this.id != null)
        return;

    this.id = $(ev.target).attr('edit');
    var $tr = $('tr[idx='+this.id+']', this.$list);
    var $src = $('td[src]', $tr);
    var $dst = $('td[dst]', $tr);
    var $code = $('td[code]', $tr);
    var $state = $('td[state]', $tr);

    $tr.removeClass('disabled');
    $src.html(
        $('<input>', {'type': 'text', 'name': 'src',
                      'class': 'form-control input-sm'})
            .val($src.attr('src')));
    $dst.html(
        $('<input>', {'type': 'text', 'name': 'dst',
                      'class': 'form-control input-sm'})
            .val($dst.attr('dst')));

    var $_code = $('<select>', {'name': 'code', 'class': 'form-control'})
        .append($('<option>', {'value': '301'}).text(M._('301 Moved Permanently')))
        .append($('<option>', {'value': '302'}).text(M._('302 Moved Temporarily')));
    $_code.val($code.attr('code'));
    $code.html($_code);

    $_state = $('<input>', {'type': 'checkbox', 'name': 'state'});
    if ($state.attr('state') == '1')
        $_state.attr('checked', 'checked');
    $state.html($('<div>', {'class': 'checkbox'})
        .html($('<label>')
            .html($_state)
            .append(M._('Enabled'))));

    // disable links and show buttons
    this.$btn_edit.addClass('disabled');
    this.$btn_delete.addClass('disabled');
    this.$btn_add.addClass('disabled');
    $('span[role=links]', $tr).css('display', 'none');
    $('span[role=buttons]', $tr).css('display', 'inline');
}

M.Redirect.prototype._save = function(ev){
    if (this.id == null)
        return;

    var $target = $(ev.target);
    var $tr = $('tr[idx='+this.id+']', this.$list);

    var $input_src = $('input[name=src]', $tr);
    var $input_dst = $('input[name=dst]', $tr);

    var src = $input_src.val();
    var dst = $input_dst.val();
    var code = $('select[name=code]', $tr).val();
    var state = ($('input[name=state]', $tr)[0].checked) ? 1 : 0;

    var $value = $('input[name=value]', $tr);

    var spinner = new M.Spinner();
    $.ajax({url: $target.attr('save'),
            type: 'put',
            accepts : {'json': 'application/json', 'html': 'text/html'},
            data: {'src': src, 'dst': dst, 'code': code, 'state': state, 'token': this.token},
            context: this,
            success: function(data){
                $input_src.parent().removeClass('has-error');
                $input_dst.parent().removeClass('has-error');
                setTimeout(function(){  // litle wrap for working history
    	            window.location.reload();
                    delete spinner.stop();
                },0);
            },
            error: function(xhr, status, http_status) {
                if (xhr.status == 400) {
                    var src_errs = ['empty_src', 'bad_src', 'src_exist'];
                    var reason = xhr.responseJSON.reason;
                    if (src_errs.find(function(it){return it == reason}))
                        $input_src.parent().addClass('has-error');
                    else if (reason == 'empty_dst')
                        $input_dst.parent().addClass('has-error');
                    alert(M._(reason));
                } else {
                    this.$btn_add.parent().addClass('has-error');
                    alert(http_status);
                }
                delete spinner.stop();
                console.error(http_status);
            }
        });
}

M.Redirect.prototype._cancel = function(ev){
    if (this.id == null)
        return;

    var $tr = $('tr[idx='+this.id+']', this.$list);
    var $src = $('td[src]', $tr);
    var $dst = $('td[dst]', $tr);
    var $code = $('td[code]', $tr);
    var $state = $('td[state]', $tr);

    if ($state.attr('state') == 0)
        $tr.addClass('disabled');
    $src.text($src.attr('src'));
    $dst.text($dst.attr('dst'));
    var code = $code.attr('code');
    if (code == '301')
        $code.text(M._('301 Moved Permanently'));
    else if (code == '302')
        $code.text(M._('302 Moved Temporarily'));
    else
        $code.text(code);
    if ($state.attr('state') == '0')
        $state.text(M._('Disabled'));
    else
        $state.text(M._('Enabled'));

    this.id = null;

    // enable links and hide buttons
    this.$btn_edit.removeClass('disabled');
    this.$btn_delete.removeClass('disabled');
    this.$btn_add.removeClass('disabled');
    $('span[role=links]', $tr).css('display', 'inline');
    $('span[role=buttons]', $tr).css('display', 'none');
}

M.Redirect.prototype._delete = function(ev){
    if (this.id != null)
        return;

    var $target = $(ev.target);
    var id = $target.attr('idx');
    var $tr = $('tr[idx='+id+']', this.$list);
    var message = M._('mpm_sure_delete').replace("%s",
        $('td[src]', $tr).attr('src'));

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
