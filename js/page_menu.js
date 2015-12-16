var M = M || {};

M.e = function(text){
    return $('<textarea/>').html(text).html();
}

M.page_menu = {
    tr: function(tr, item){},
    table: function(items){},
    insert: function(next){},
    stopedit: function(tr){},
    edit: function (){},
    confirm_delete: function(message, url){},

    post: function(){},
    put: function(){},
    delete: function(url){},

    /* Drag & Drop methods for moving items */
    drag: function(env){},
    dnd_move: function(){},
    remove_drop: function(){},
    drop: function(env){},
    drag_n_drop: function (obj){},

    token: ''
};

/* Fill row with columns of item values */
M.page_menu.tr = function(tr, item){
    tr.attr('md5', item.md5);
    tr.attr('item', item.id);
    tr.attr('parent', item.parent || '');
    tr.attr('next', item.next || '');
    tr.attr('order', item.order);

    tr.append($('<td>').html(item.id) );
    tr.append($('<td>').attr('level', item.level).html(M.e(item.title)) );
    tr.append($('<td>').html(M.e(item.link)) );
    tr.append($('<td>').html(M.e(item.locale)) );

    var actions = $('<td>');
    tr.append(actions);

    var p_span = $('<span/>', { 'class': 'btn-link'+((item.parent) ? '' :' disabled'),
                                put: '/admin/menu/'+item.id+'/to_parent'}).append(
                                        '&laquo;&laquo;');
    if (item.parent)
        p_span.on('click', M.page_menu.put);
    actions.append(p_span);
    actions.append(' / ');

    var i_span = $('<span/>', { 'class': 'btn-link',
                                insert: item.id }).append(
                                                                  M._('Insert'));
    i_span.click( function(){
        var new_tr = M.page_menu.insert(item.id);
        new_tr.insertBefore(tr);
    });
    actions.append(i_span);
    actions.append(' / ');

    var e_span = $('<span/>', { 'class': 'btn-link',
                                edit: "/admin/menu/"+item.id }).append(
                                                                  M._('Edit'));
    e_span.click(M.page_menu.edit);
    actions.append(e_span);
    actions.append(' / ');
    var d_span = $('<span/>', { 'class': 'btn-link',
                                data: item.title,
                                delete: "/admin/menu/"+item.id+"/delete" }).append(
                                                                  M._('Delete'));
    d_span.click( function(){
        M.page_menu.confirm_delete(
                M._('mpm_sure_delete').replace("%s", item.title),
                "/admin/menu/"+item.id+"/delete"
            );
    });
    actions.append(d_span);
    actions.append(' / ');

    var c_span = $('<span/>', { 'class': 'btn-link',
                                put: '/admin/menu/'+item.id+'/to_child'}).append(
                                        '&raquo;&raquo;');
    c_span.on('click', M.page_menu.put);
    actions.append(c_span);

    M.page_menu.drag_n_drop(tr);    // register drag n drop functionality
}

/* Update table rows */
M.page_menu.table = function(items){
    var trows = $('tr[md5]');
    var trows_length = trows.length;
    var items_length = items.length;
    var i = 0;
    // replace existing rows
    for ( ; i < items_length && i < trows_length; i++ ){
        var tr = $(trows[i]);
        if (tr.attr('md5') != items[i].md5) {
            tr.html('');
            M.page_menu.tr(tr, items[i]);
        }
    }

    // remove useless rows
    for ( ; i < trows_length; i++)
        $(trows[i]).remove();

    // append new rows if there are some new items
    var last = $(trows[i]);
    for (; i < items_length; i++ ){
        var tr = $('<tr>');
        M.page_menu.tr(tr, items[i]);
        last.insertAfter(tr);
        last = tr;
    }

    // allways create insert row at the end
    $('#page-menu-items').append(M.page_menu.insert());
}

/* Create table row inline form for new item */
M.page_menu.insert = function(next){
    var table = $('#page-menu-items');
    var tr = $('<tr>', {md5: ''});
    var plus = $('<span/>', { 'class': 'btn btn-default btn-sm',
                              post: '/admin/menu/add' });
    plus.append($('<i/>', {'class': 'fa fa-plus'}));
    plus.click(M.page_menu.post);

    var minus = $('<span>');
    if (next) {
        minus.addClass('btn btn-default btn-sm');
        minus.append($('<i/>', {'class': 'fa fa-minus'}));
        minus.click( function() {
            tr.remove()
        });
    } else {
        tr.mouseover(M.page_menu.dnd_move);
    }

    tr.append($('<td>').append(
        $('<input/>', { name: 'next',
                        type: 'hidden',
                        value: next != null ? next : ''}) ));

    var input = $('<input/>', { name: 'title',
                                type: 'text',
                                autofocus: '',
                                'class': 'form-control input-sm' });
    input.keydown(function(env){
        if (env.keyCode == 13) plus.click();
        else if (next && env.keyCode == 27) minus.click();
    });
    tr.append($('<td>').append( input ));

    var input = $('<input/>', { name: 'link',
                                type: 'url',
                                'class': 'form-control input-sm' });
    input.keydown(function(env){
        if (env.keyCode == 13) plus.click();
        else if (next && env.keyCode == 27) minus.click();
    });
    tr.append($('<td>').append( input ));

    var input = $('<input/>', { name: 'locale',
                                type: 'text',
                                'class': 'form-control input-sm' });
    input.keydown(function(env){
        if (env.keyCode == 13) plus.click();
        else if (next && env.keyCode == 27) minus.click();
    });
    tr.append($('<td>').append( input ));

    tr.append($('<td>').append(plus)
                       .append(' ')
                       .append(minus)
    );
    return tr;
}

/* Swap form from edit to normal row */
M.page_menu.stopedit = function (tr){
    var button = $('button', tr);
    actions = button.parent();
    button.remove();

    var p_span = $('<span/>', { 'class': 'btn-link'+(tr.attr('parent') ? '' :' disabled'),
                                put: '/admin/menu/'+tr.attr('item')+'/to_parent'}).append(
                                        '&laquo;&laquo;');
    if (tr.attr('parent'))
        p_span.on('click', M.page_menu.put);
    actions.append(p_span);
    actions.append(' / ');

    var i_span = $('<span/>', { 'class': 'btn-link',
                                insert: tr.attr('item') }).append(
                                                            M._('Insert'));
    i_span.click( function(){
        var new_tr = M.page_menu.insert(tr.attr('item'));
        new_tr.insertBefore(tr);
    });
    actions.append(i_span);
    actions.append(' / ');

    var e_span = $('<span/>', { 'class': 'btn-link',
                                edit: "/admin/menu/"+tr.attr('item') }).append(
                                                                  M._('Edit'));
    e_span.click(M.page_menu.edit);
    actions.append(e_span);
    actions.append(' / ');
    var d_span = $('<span/>', { 'class': 'btn-link',
                                data: $('input[name=title]', tr).attr('orig'),
                                delete: "/admin/menu/"+tr.attr('item')+"/delete" }).append(
                                                                  M._('Delete'));
    d_span.click( function(){
        M.page_menu.confirm_delete(
                M._('mpm_sure_delete').replace("%s", $('input[name=title]', tr).attr('orig')),
                "/admin/menu/"+tr.attr('item')+"/delete"
            );
    });
    actions.append(d_span);
    actions.append(' / ');

    var c_span = $('<span/>', { 'class': 'btn-link',
                                put: '/admin/menu/'+tr.attr('item')+'/to_child'}).append(
                                        '&raquo;&raquo;');
    c_span.on('click', M.page_menu.put);
    actions.append(c_span);

    var inputs = $('input', tr);
    for (var i = 0; i < inputs.length; i++){
        var nod = $(inputs[i]);
        nod.replaceWith(nod.attr('orig'));
    }
}

/* Swap row to inline form */
M.page_menu.edit = function (){
    var btn = $(this);
    var actions = btn.parent();
    // to table function refresh row allways
    actions.parent().attr('md5', '');
    var tds = actions.siblings();

    var save = $('<button/>', { type: 'button',
                                'class': 'btn btn-default btn-sm',
                                put: btn.attr('edit') });
    save.append($('<i/>', {'class': 'fa fa-save'}));
    save.click(M.page_menu.post);

    var input = $('<input/>', { value: $(tds[1]).html(),
                                orig: $(tds[1]).html(),
                                name: 'title',
                                autofocus: '',
                                type: 'text',
                                'class': 'form-control input-sm'});
    input.keydown(function(env){
        if (env.keyCode == 13) save.click();
        else if (env.keyCode == 27) M.page_menu.stopedit(actions.parent());
    });
    $(tds[1]).html(input);

    var input = $('<input/>', { value: $(tds[2]).html(),
                                orig: $(tds[2]).html(),
                                name: 'link',
                                type: 'url',
                                'class': 'form-control input-sm'})
    input.keydown(function(env){
        if (env.keyCode == 13) save.click();
        else if (env.keyCode == 27) M.page_menu.stopedit(actions.parent());
    });
    $(tds[2]).html(input);
    var input = $('<input/>', { value: $(tds[3]).html(),
                                orig: $(tds[3]).html(),
                                name: 'locale',
                                type: 'text',
                                'class': 'form-control input-sm'});
    input.keydown(function(env){
        if (env.keyCode == 13) save.click();
        else if (env.keyCode == 27) M.page_menu.stopedit(actions.parent());
    });
    $(tds[3]).html(input);

    actions.html(save);
}

/* Ask user with modal dialog, to confirm deleting item */
M.page_menu.confirm_delete = function(message, url) {
    M.page_menu.confirm_delete._url = url;
    var dialog = $('#confirm_delete');
    $('.popup-message', dialog).text(message);
    dialog.modal('show');
}

/* Send form (append/insert or update) by ajax */
M.page_menu.post = function (){
    var tr = $(this).parent().parent();
    var method = 'post';
    var url = $(this).attr('post');
    if (! url) {
        url = $(this).attr('put');
        method = 'put';
    }
    $.ajax({ url: url,
             type: method,
             data : { 'token': M.page_menu.token,
                      'next': $('input[name=next]', tr).val(),
                      'title': $('input[name=title]', tr).val(),
                      'link': $('input[name=link]', tr).val(),
                      'locale':  $('input[name=locale]', tr).val()},
             success: function (data) {
                M.page_menu.table(data.items);
             },
             statusCode: {
                400: function (data) {
                    M.alert(M._(data.responseJSON.reason));
                    $(tr).addClass('has-error');
                }
             }
    });
}

/* Send put commands by ajax (to_child/to_parent) */
M.page_menu.put = function (){
    $.ajax({ url: $(this).attr('put'),
             type: 'put',
             data: {'token': M.page_menu.token},
             success: function (data) {
                M.page_menu.table(data.items);
             },
             statusCode: {
                400: function (data) {
                    M.alert(M._(data.responseJSON.reason));
                }
            }
    });
}

/* Send delete request by ajax */
M.page_menu.delete = function(url) {
    $.ajax({ url: url+'?token='+encodeURIComponent(M.page_menu.token),
             type: 'delete',
             success: function (data) {
                M.page_menu.table(data.items);
             },
             statusCode: {
                400: function (data) {
                    M.alert(M._(data.responseJSON.reason));
                }
             }
    });
}

/* ---------------------------------------------------------------- *
 *                  Drag & Drop methods for moving items            *
 * ---------------------------------------------------------------- */
M.page_menu._drag = null;

/* Drag row -> start moving */
M.page_menu.drag = function(env) {
    var tg = $(env.target);
    if (tg.is('a') || tg.is('button') || tg.is('input') || tg.hasClass('btn-link'))
        return;

    //console.log('drag & drop -> drag');
    M.page_menu._drag = $(this);
    M.page_menu._drag.addClass('drag');
    M.page_menu._drag.attr('nnext', M.page_menu._drag.attr('next'));
    $(document.body).addClass('grabbing');

    document.body.focus();  // cancel out any text selections
                            // prevent text selection in IE
    document.onselectstart = function () { return false; };
    return false;           // prevent text selection (except IE)
}

/* Moving with row to anoter position */
M.page_menu.dnd_move = function() {
    //console.log('drag & drop -> move');
    if (M.page_menu._drag) {
        $(this).addClass('drop');
        M.page_menu._drag.remove();
        M.page_menu._drag.insertBefore(this);
        M.page_menu._drag.attr('nnext', $(this).attr('item') || '');
    }
}

/* Detach drop positioin */
M.page_menu.remove_drop = function () {
    //console.log('drag & drop -> detach drop');
    if (M.page_menu._drag){
        $(this).removeClass('drop');
    }
}

/* Drop row -> end moving to new position */
M.page_menu.drop = function(env) {
    //console.log('drag & drop -> drop');
    if (M.page_menu._drag) {
        var item = M.page_menu._drag.attr('item');
        var next = M.page_menu._drag.attr('next');
        var nnext = M.page_menu._drag.attr('nnext') || '';
        M.page_menu._drag.removeClass('drag');
        M.page_menu.drag_n_drop(M.page_menu._drag); // TODO: why ?
        M.page_menu._drag = null;
        $(document.body).removeClass('grabbing');
        document.onselectstart = null;
        if (next != nnext){
            $.ajax({ url: '/admin/menu/' + item + '/move',
                    type: 'put',
                    data : { 'token': M.page_menu.token, 'next': nnext },
                    success: function (data) {
                        M.page_menu.table(data.items);
                    },
                    statusCode: {
                        400: function (data) {
                            M.alert(M._(data.responseJSON.reason));
                        }
                    }
            });
        }
    }
}

/* Bind row (obj) to could be drag or drop */
M.page_menu.drag_n_drop = function (obj){
    //cnsole.log('drag & drop -> bind functionality');
    obj.mousedown(M.page_menu.drag);
    obj.mouseup(M.page_menu.remove_drop);
    obj.mouseout(M.page_menu.remove_drop);
    obj.mouseover(M.page_menu.dnd_move);
}

$(document).ready(function() {
    $('body').on('DOMNodeInserted', function(event) {
        var focused = $('input[autofocus]', event.target);
        if (focused.length) {               // if some child is input[autofocuse]
            focused.focus();
        } else {
            focused = $(event.target);      // if target is input[autofocuse]
            if (focused.is('input[autofocus]')) {
                focused.focus();
            }
        }
    });

    // bind drag & drop
    M.page_menu.drag_n_drop($('tr[md5]'));
    $(document).mouseup(M.page_menu.drop);

    // data-ok button on confirm_delete dialog call delete method
    $('button[data-ok]', $('#confirm_delete')).click( function() {
        M.page_menu.delete(M.page_menu.confirm_delete._url);
        $('#confirm_delete').modal('hide');
    });

    // insert, edit end delete span links doning right action
    $('span[insert]').click( function(){
        var btn = $(this);
        var tr = M.page_menu.insert(btn.attr('insert'));
        tr.insertBefore(btn.parent().parent());
    });
    $('span[edit]').click(M.page_menu.edit);
    $('span[delete]').click( function(){
        M.page_menu.confirm_delete(
                M._('mpm_sure_delete').replace("%s", $(this).attr('data')),
                $(this).attr('delete')
            );
    });
    $('span[put]').click(M.page_menu.put);

    // insert empty row form at the end of table
    $('#page-menu-items').append(M.page_menu.insert());
});
