var M = M || {};

M.page_menu = {
    table: function(){},
    insert: function(){},
    dialog: function(){},
    edit: function(){},
    delete: function(){},

    post: function(){}
};

/*
 * Fill row with columns of item values
 */
M.page_menu.tr = function(tr, item){
    tr.attr('md5', item.md5);
    tr.append($('<td>').html(item.id));
    tr.append($('<td>').html(item.parent));
    tr.append($('<td>').html(item.next));
    tr.append($('<td>').html(item.order));
    tr.append($('<td>').html(item.title));
    tr.append($('<td>').html( $('<textarea/>').html(item.link).html()) );
    tr.append($('<td>').html(item.locale));
    var actions = $('<td>');
    tr.append(actions);
    var a = $('<a/>', { href: '#',
                        edit: "/admin/menu/"+item.id }).append(
                                                        M._('Edit'));
    a.click(M.page_menu.edit);
    actions.append(a);
    actions.append(' / ');
    var a = $('<a/>', { href: '#',
                    delete: "/admin/menu/"+item.id+"/delete" }).append(
                                                        M._('Delete'));
    a.click(M.page_menu.dialog);
    actions.append(a);
}

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

    console.log("append some rows");
    // append new rows if there are some new items
    var last = $(trows[i]);
    for (; i < items_length; i++ ){
        var tr = $('<tr>');
        M.page_menu.tr(tr, items[i]);
        last.insertAfter(tr);
        last = tr;
    }

    M.page_menu.insert();   // allways create insert row at the end
}

M.page_menu.insert = function(next){
    var table = $('#page-menu-items');
    var tr = $('<tr>', {md5: ''});
    tr.append($('<td>'));    // id
    tr.append($('<td>'));    // parent
    tr.append($('<td>').append(
        $('<input/>', { name: 'next',
                        type: 'text',
                        value: next != null ? next : ''}) ));
    tr.append($('<td>'));    // order
    tr.append($('<td>').append(
        $('<input/>', { name: 'title',
                        type: 'text',
                        'class': 'form-control input-sm' }) ));

    tr.append($('<td>').append($('<input/>', { name: 'link',
                        type: 'text',
                        'class': 'form-control input-sm' }) ));

    tr.append($('<td>').append($('<input/>', { name: 'locale',
                        type: 'text',
                        'class': 'form-control input-sm' }) ));

    var a = $('<a/>', { href: '#',
                        'class': 'btn btn-default btn-sm',
                        post: '/admin/menu/add' });
    a.append($('<i/>', {'class': 'fa fa-plus'}));
    a.click(M.page_menu.post);
    tr.append($('<td>').append(a));

    $('#page-menu-items').append(tr);
}

M.page_menu.edit = function (){
    var tds = $(this).parent().siblings();
    $(tds[4]).html($('<input/>', { value: $(tds[4]).html(),
                                   name: 'title',
                                  'class': 'form-control input-sm'}));
    $(tds[5]).html($('<input/>', { value: $(tds[5]).html(),
                                   name: 'link',
                                   'class': 'form-control input-sm'}));
    $(tds[6]).html($('<input/>', { value: $(tds[6]).html(),
                                   name: 'locale',
                                  'class': 'form-control input-sm'}));
    var a = $('<a/>', { href: '#',
                        'class': 'btn btn-default btn-sm',
                        post: '/admin/menu/'+$(tds[0]).html()});
    a.append($('<i/>', {'class': 'fa fa-save'}));
    a.click(M.page_menu.post);
    $(this).parent().html(a);
}

M.page_menu.dialog = function() {
    var dialog = $('#sure_delete');
    $('h3', dialog[0]).text(M._('sure_delete').replace("%s", $(this).attr('data')));
    $('button[delete]', dialog[0]).attr('delete', $(this).attr('delete'));
    dialog.modal('show');
}

M.page_menu.post = function (){
    var tr = $(this).parent().parent();
    $.ajax({ url: $(this).attr('post'),
             type: 'post',
             data : { 'next': $('input[name=next]', tr).val(),
                      'title': $('input[name=title]', tr).val(),
                      'link': $('input[name=link]', tr).val(),
                      'locale':  $('input[name=locale]', tr).val()},
             success: function (data) {
                console.log('200 Ok');
                console.log(data);
                M.page_menu.table(data.items);
             },
             statusCode: {
                400: function (data) {
                    alert(M._(data.responseJSON.reason));
                    $(tr).addClass('has-error');
                }
             }
    });
}

M.page_menu.delete = function() {
    var dialog = $('#sure_delete');
    $.ajax({ url: $(this).attr('delete'),
             type: 'post',
             success: function (data) {
                M.page_menu.table(data.items);
             },
             statusCode: {
                400: function (data) {
                    alert(M._(data.responseJSON.reason));
                }
             }
    });
    dialog.modal('hide');
}

$(document).ready(function() {
    $('a[edit]').click(M.page_menu.edit);
    $('a[delete]').click(M.page_menu.dialog);
    $('button[delete]').click(M.page_menu.delete);
    M.page_menu.insert();

});
