var M = M || {};
M.Eshop = M.Eshop || {};

M.Eshop.Actions = function (item_id, item_price, item_count, token){
    this.item_id = item_id;
    this.$item_price = $(item_price);
    this.$item_count = $(item_count);
    this.item_price = Number(this.$item_price.html());
    this.token = token

    this.$switchs = $('li>a[role=switch]');
    this.$fast = $('li>a[role=fast]');
    this.$table = $('table[view=actions]');
    this.$form_count = $('tr[role=count]',this.$table);
    this.$form_price = $('tr[role=price]',this.$table);

    this.constructor();
}

M.Eshop.Actions.prototype.constructor = function (){
    this.refresh('all');
    this.$switchs.on('click', this._show.bind(this));
    this.$fast.on('click', this._show.bind(this));
    $('a[add]').on('click', this.add.bind(this));
    $('a[set]').on('click', this.set.bind(this));
}

M.Eshop.Actions.prototype._show = function(ev){
    var show = $(ev.target).attr('show');
    this.refresh(show);
}

M.Eshop.Actions.prototype.set = function(){
    var $note = $('input[name=note]', this.$form_price);
    var $value = $('input[name=value]', this.$form_price);
    data = { 'note': $note.val(), 'price': $value.val(), 'token': this.token };

    if (data['price'] == this.item_price) {
        $value.parent().addClass('has-error');
        return;
    }

    var show = this.$switchs.filter('li.active >').attr('show');    // get active show
    $.ajax({ url: '/admin/eshop/store/'+this.item_id+'/pri',
             type: 'post',
             accepts : {json: 'application/json', html: 'text/html'},
             dataType: 'json',
             data: data,
             context: this,
             success: function(data){
                    this.item_price = data.item.price;
                    this.$item_price.html(data.item.price);
                    this.$item_count.html(data.item.count);

                    $value.parent().removeClass('has-error');
                    $value.val(this.item_price);
                    $note.val('');

                    this.refresh(show);
             },
             error: function(xhr, status, http_status){
                    console.error(status);
                    console.error(http_status);
                    // TODO: info to user....
             }
    });
}

M.Eshop.Actions.prototype.add = function(){
    var $note = $('input[name=note]', this.$form_count);
    var $value = $('input[name=value]', this.$form_count);
    data = { 'note': $note.val(), 'count': $value.val(), 'token': this.token };

    if (data['count'] == 0) {
        $value.parent().addClass('has-error');
        return;
    }

    var show = this.$switchs.filter('li.active >').attr('show');    // get active show
    $.ajax({ url: '/admin/eshop/store/'+this.item_id+'/inc',
             type: 'post',
             accepts : {json: 'application/json', html: 'text/html'},
             dataType: 'json',
             data: data,
             context: this,
             success: function(data){
                    this.item_price = data.item.price;
                    this.$item_price.html(data.item.price);
                    this.$item_count.html(data.item.count);

                    $value.parent().removeClass('has-error');
                    $value.val(0);
                    $note.val('');

                    this.refresh(show);
             },
             error: function(xhr, status, http_status){
                    console.error(status);
                    console.error(http_status);
                    // TODO: info to user....
             }
    });
}

M.Eshop.Actions.prototype.refresh = function(show){
    this.$switchs.parent().filter('li').removeClass('active');  // switch active
    this.$switchs.filter('a[show='+show+']').parent().addClass('active');

    if (show == 'inc') {
        this.$form_price[0].style.display = 'none';
        this.$form_count[0].style.display = 'table-row';

    } else if (show == 'pri') {
        this.$form_count[0].style.display = 'none';
        this.$form_price[0].style.display = 'table-row';
    } else {
        this.$form_price[0].style.display = 'none';
        this.$form_count[0].style.display = 'none';
    }

    this.$table.find('tr:not([role])').remove();
    $.ajax({ url: '/admin/eshop/store/'+this.item_id+'/actions',
             data: { 'type':show, 'token': this.token },
             context: this,
             success: function(data){
                    this._view(data, show);
             },
             error: function(xhr, status, http_status){
                    alert(http_status);
             }
    });
}

M.Eshop.Actions.prototype._view = function(data){
    var ch = this.$table.children();
    for (var i = 0; i < data.actions.length; i++){
        var it = data.actions[i];
        var d = new Date(it.timestamp*1000);
        var tr = $('<tr>');
        tr.append($('<td>').append(d.format('hh:mm dd.MM.yyyy')));
        if (it.action_type == 1)
            tr.append($('<td>').append('<i title="'+M._('Stored')+'" class="fa fa-sign-in">'));
        else if (it.action_type == 2)
            tr.append($('<td>').append('<i title="'+M._('Sold')+'" class="fa fa-sign-out">'));
        else if (it.action_type == 3)
            tr.append($('<td>').append('<i title="'+M._('Pricing')+'" class="fa fa-money">'));
        else
            tr.append($('<td>').append(it.action_type));

        if (it.action_type == 3)
            tr.append($('<td>').append(it.data.price));
        else
            tr.append($('<td>').append(it.data.count));
        tr.append($('<td>')
            .text((it.data.order) ? '' : it.data.note)
            .append((it.data.order) ? $('<a>', {'href': '/admin/eshop/orders/'+it.data.order}).text(M._('Order')+': '+it.data.order) : '') );

        ch.append(tr);
    }
}
