var M   = M || {};
M.Eshop = M.Eshop || {};

M.Eshop.buy = function(item_id, count, fn) {
    var spinner = new M.Spinner();

    $.ajax({url: '/eshop/cart/add',
            type: 'put',
            accepts : { json: 'application/json', html: 'text/html' },
            contentType: 'application/json',
            dataType: 'json',
            data: JSON.stringify({ 'item_id': item_id, 'count': count || 1 }),
            success: function(data){
                if (fn) fn();
                delete spinner.stop();
                var $cart = $('a[role=shopping-cart]');
                $cart.fadeOut('slow',function(){
                    $('.count', $cart).text(data.cart.count);
                    $cart.fadeIn('slow')
                });
            },
            error: function(xhr, status, http_status){
                //console.log(JSON.stringify(xhr));
                var $error = $('<div>', {'class': 'alert alert-danger popup-alert'})
                    .append($('<div>', {'class': 'close',
                                         'data-dismiss': 'alert',
                                         'aria-hidden': 'true',}).html('&times'))
                    .append($('<h4>').text(M._('Error in Action')))
                    .append($('<p>').text(M._('me_error_in_action')))
                    .appendTo('body');
                delete spinner.stop();
            }
    });
}

$(document).ready(function() {
    var $menu_cart = $('a[role=shopping-cart]')
            .html($('<i>', {'class': 'fa fa-shopping-cart'}))
            .append(' ')
            .append($('<span>', {'class':'count'})
                        .text('?'));

    $.ajax({url: '/eshop/cart',
            type: 'get',
            accepts : { json: 'application/json', html: 'text/html' },
            success: function(data){
                $('span.count', $menu_cart).text(data.cart.count);
            },
            error: function(xhr, status, http_status){
                //console.log(JSON.stringify(xhr));
                var $error = $('<div>', {'class': 'alert alert-danger popup-alert'})
                    .append($('<div>', {'class': 'close',
                                         'data-dismiss': 'alert',
                                         'aria-hidden': 'true',}).html('&times'))
                    .append($('<h4>').text(M._('Error in Action')))
                    .append($('<p>').text(M._('me_error_in_action')))
                    .appendTo('body');
            }
    });
});
