var M = M || {};
M.Eshop = M.Eshop || {};

M.Eshop.ShoppingCart = function(data, currency, params){
    params = params || {};
    this._set(data);
    this.currency = currency;

    this.$table = $('table' in params ? params['table'] : 'table[role=cart-items]');
    this.$recalculate = $('recalculate' in params ? params['recalculate'] : 'a[role=recalculate]');
    this.$next = $('next' in params ? params['next'] : 'a[way=next]');

    this.constructor();
}

M.Eshop.ShoppingCart.prototype.constructor = function (){
    this.refresh();
    this.$recalculate.on('click', this.on_recalculate.bind(this));
    this.$next.on('click', this.on_next.bind(this));
}

M.Eshop.ShoppingCart.prototype._set = function (data){
    for (var it in data) if (it != 'items') this[it] = data[it];
    this.items = {};
    for (var i = 0; i < data.items.length; i++){
        this.items[data.items[i][0]] = data.items[i][1];
    }
}

M.Eshop.ShoppingCart.prototype.refresh = function() {
    this.$table.find('tr[role!=header]').remove();
    for (var item_id in this.items){
        item_id = Number(item_id);  //XXX: need to convert to number, do't know why
        var item = this.items[item_id];
        var $tr = $('<tr>');
        $('<td>').text(item_id).appendTo($tr);
        $('<td>').text(item.name).appendTo($tr);
        $('<td>', {'class': 'price'})
            .text(item.price.toFixed(1) + ' ' + this.currency)
            .appendTo($tr);
        $('<td>', {'class': 'count'})
            .append($('<input>', {'class': 'form-control', 'type': 'number',
                                  'name': 'count', 'item-id': item_id })
                        .val(item.count))
            .appendTo($tr);
        $('<td>', {'class': 'summary'})
            .text(item.summary.toFixed(1) + ' ' + this.currency)
            .appendTo($tr);
        $('<td>', {'class': 'actions'})
            .append($('<a>')
                        .text(M._('Remove'))
                        .on('click', this.on_remove.bind(this, item_id)))
            .appendTo($tr);

        $tr.appendTo(this.$table);
    }

    $('<tr>', {'class': 'active summary'})
        .append($('<td>'))
        .append($('<td>').text(M._('Summary')))
        .append($('<td>'))
        .append($('<td>',{'class': 'count'}).text(this.count))
        .append($('<td>',{'class': 'summary'})
                    .text(this.summary.toFixed(1) + ' ' + this.currency))
        .append($('<td>'))
        .appendTo(this.$table);

}

M.Eshop.ShoppingCart.prototype.on_remove = function(item_id) {
    var spinner = new M.Spinner();

    $.ajax({ url: '/eshop/cart',
             type: 'patch',
             accepts : {json: 'application/json', html: 'text/html'},
             contentType: 'application/merge-patch+json',
             dataType: 'json',
             data: JSON.stringify({'items': [
                    [item_id, {count: this.items[item_id].count * -1}] ]}),
             context: this,
             success: function(data){
                this._set(data.cart);
                this.refresh();
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

M.Eshop.ShoppingCart.prototype.on_recalculate = function() {
    var spinner = new M.Spinner();

    var $inputs = $('input[name=count]',this.$table);
    var items = [];
    for (var i = 0; i < $inputs.length; i++){
        var item_id = Number($($inputs[i]).attr('item-id'));
        items.push([item_id,
                    {count: $($inputs[i]).val() - this.items[item_id].count} ]);
    }

    $.ajax({ url: '/eshop/cart',
             type: 'patch',
             accepts : {json: 'application/json', html: 'text/html'},
             contentType: 'application/merge-patch+json',
             dataType: 'json',
             data: JSON.stringify({'items': items }),
             context: this,
             success: function(data){
                this._set(data.cart);
                this.refresh();
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

M.Eshop.ShoppingCart.prototype.on_next = function() {
    var spinner = new M.Spinner();

    var $inputs = $('input[name=count]',this.$table);
    var items = [];
    for (var i = 0; i < $inputs.length; i++){
        var item_id = Number($($inputs[i]).attr('item-id'));
        items.push([item_id,
                    {count: $($inputs[i]).val() - this.items[item_id].count} ]);
    }

    $.ajax({ url: '/eshop/cart',
             type: 'patch',
             accepts : {json: 'application/json', html: 'text/html'},
             contentType: 'application/merge-patch+json',
             dataType: 'json',
             data: JSON.stringify({'items': items }),
             context: this,
             success: function(data){
                window.location = "/eshop/cart/address";
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
