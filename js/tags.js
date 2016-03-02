var M = M || {};

M.e = M.e || function(text){
    return $('<textarea/>').html(text).html();
}

M.Tags = function(params){
    if (params == null) params = {};

    this.$table = $(('table' in params ? params['tabla'] : 'table[role=tags]'));
    this.$select = $(('select' in params ? params['select'] : 'select[name=tag]'));

    this.token = 'token' in params ? params['token'] : null;
    this.tags_link = 'tags_link' in params ? params['tags_link'] : null;
    this.tags_link_append = 'tags_link_append' in params ? params['tags_link_append'] : null;
    this.tags_link_remove = 'tags_link_remove' in params ? params['tags_link_remove'] : null;

    this.constructor();
}

M.Tags.prototype.constructor = function(){
    if (this.tags_link_append)
        this.$select.on('change', this._append.bind(this));
    if (this.tags_link_remove)
        $('a[remove]', this.$table).on('click', this._remove.bind(this))
}

M.Tags.prototype.refresh = function(){
    $.ajax({ url: this.tags_link,
             data: { 'token': this.token },
             context: this,
             success: function(data){
                    this.$table.find('tr').remove();
                    this._view(data);
             },
             error: function(xhr, status, http_status){
                    alert(http_status);
             }
    });
}

M.Tags.prototype._view = function(data){
    for (var i = 0; i < data.tags.length; i++){
        var it = data.tags[i];
        var $tr = $('<tr>')
            .append($('<td>').text(it.value))
            .append($('<td>')
                .append($('<a>')
                    .attr('remove', it.id.toString())   // can't be set in construct
                    .text(M._('Remove tag'))
                    .on('click', this._remove.bind(this))
            ));
        this.$table.append($tr);
    }
}

M.Tags.prototype._append = function(){
    var tag_id = Number(this.$select.val());

    if (tag_id) {
        var spinner = new M.Spinner();
        $.ajax({ url: this.tags_link_append.replace('{tag_id}', tag_id),
                 type: 'post',
                 accepts : {'json': 'application/json', 'html': 'text/html'},
                 data: { 'token': this.token },
                 context: this,
                 success: function(data){
                    $('option[value='+tag_id+']', this.$select)
                        .attr('disabled', 'disabled');
                    this.$select.val(0);
                    this.$select.parent().removeClass('has-error');
                    this.refresh();
                    delete spinner.stop();
                 },
                 error: function(xhr, status, http_status) {
                    this.$select.parent().addClass('has-error');
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

M.Tags.prototype._remove = function(ev){
    var $target = $(ev.target)
    var tag_id = Number($target.attr('remove'));

    var spinner = new M.Spinner();
    $.ajax({url: this.tags_link_remove.replace('{tag_id}', tag_id),
            type: 'post',
            accepts : {'json': 'application/json', 'html': 'text/html'},
            data: { 'token': this.token },
            context: this,
            success: function(data){
                $('option[value='+tag_id+']', this.$select)
                        .removeAttr('disabled');
                $target.parent().parent().removeClass('text-danger');
    	        this.refresh();
                delete spinner.stop();
            },
            error: function(xhr, status, http_status) {
                $target.parent().parent().addClass('text-danger');
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
