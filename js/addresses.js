var M = M || {};

M.Addresses = function (addresses, params){
    this.$form = $(('form' in params ? params['form'] : 'form'));
    this.$list = $(('list' in params ? params['list'] : 'table'));
    this.$flink = $(('formlink' in params ? params['formlink'] : 'a[role=add]'));
    this.$llink = $(('listlink' in params ? params['listlink'] : 'a[role=list]'));
    this.$sbtn = $(('savebtn' in params ? params['savebtn'] : 'button[role=save]'));
    this.$cbtn = $(('cancelbtn' in params ? params['cancelbtn'] : 'button[role=cancel]'));

    this.addresses = [];            // addresses are html escaped
    var _sp = $('<span>');          // and this object work with original text
    for (var i = 0; i < addresses.length; i++){
        var addr = {};
        for (var it in addresses[i])
            addr[it] = _sp.html(addresses[i][it]).text();
        this.addresses.push(addr);
    }

    this._visible = null;
    this._edited = null;

    this.constructor();
}

M.Addresses.prototype.constructor = function (){
    this.$flink.on('click', this.show_form.bind(this));
    this.$llink.on('click', this.show_list.bind(this));
    this.$sbtn.on('click', this._save.bind(this));
    this.$cbtn.on('click', this._cancel.bind(this));

    if (this.addresses.length > 0) {
        this.show_list();
        this.refresh();
    } else
        this.show_form();
}

M.Addresses.prototype.show_form = function(){
    this.$list.addClass('hidden');
    this.$flink.addClass('hidden');

    this.$form.removeClass('hidden');
    this.$llink.removeClass('hidden');
    this._visible = this.$form;
}

M.Addresses.prototype.show_list = function(){
    this.$form.addClass('hidden');
    this.$llink.addClass('hidden');

    this.$list.removeClass('hidden');
    this.$flink.removeClass('hidden');
    this._visible = this.$form;
}

M.Addresses.prototype.edit = function(ev){
    var i = $(ev.target).attr('l-index');
    this._edited = i;

    $('select[name=type]', this.$form).val(this.addresses[i].type || '');
    $('input[name=name]', this.$form).val(this.addresses[i].name || '');
    $('input[name=address1]', this.$form).val(this.addresses[i].address1 || '');
    $('input[name=address2]', this.$form).val(this.addresses[i].address2 || '');
    $('input[name=city]', this.$form).val(this.addresses[i].city || '');
    $('input[name=region]', this.$form).val(this.addresses[i].region || '');
    $('input[name=zip]', this.$form).val(this.addresses[i].zip || '');
    $('input[name=country]', this.$form).val(this.addresses[i].country || '');

    this.show_form();
}

M.Addresses.prototype.delete = function(ev){
    var i = $(ev.target).attr('l-index');
    addr = this.addresses[i];
    list = [];
    if (addr.name) list.push(addr.name);
    if (addr.address1) list.push(addr.address1);
    if (addr.address2) list.push(addr.address2);
    if (addr.city) list.push(addr.city);
    if (addr.region) list.push(addr.region);
    if (addr.zip) list.push(addr.zip);
    if (addr.country) list.push(addr.country);

    M.confirm(
        M._('mla_sure_delete').replace("%s",
            (addr.type ? addr.type + ': ' : 'Address: ') + list.join(', ') ),
        this._delete.bind(this, i) );
}

M.Addresses.prototype._delete = function(i){
    this.addresses.splice(i,1);

    $.ajax({ url: window.location,
             type: 'put',
             accepts : {json: 'application/json', html: 'text/html'},
             contentType: 'application/json',
             dataType: 'json',
             data: JSON.stringify({ addresses: this.addresses }),
             context: this,
             success: function(data){
                this.addresses = data;
                this.refresh();
             },
             error: function(xhr, status, http_status){
                    console.error(status);
                    console.error(http_status);
                    // TODO: info to user....
             }
    });
}

M.Addresses.prototype._save = function(){
    var addr = {
        'type': $('select[name=type]', this.$form).val(),
        'name': $('input[name=name]', this.$form).val(),
        'address1': $('input[name=address1]', this.$form).val(),
        'address2': $('input[name=address2]', this.$form).val(),
        'city': $('input[name=city]', this.$form).val(),
        'region': $('input[name=region]', this.$form).val(),
        'zip': $('input[name=zip]', this.$form).val(),
        'country': $('input[name=country]', this.$form).val()
    };

    if (this._edited != null)
        this.addresses[this._edited] = addr;
    else
        this.addresses.push(addr);

    $.ajax({ url: window.location,
             type: 'put',
             accepts : {json: 'application/json', html: 'text/html'},
             contentType: 'application/json',
             dataType: 'json',
             data: JSON.stringify({ addresses: this.addresses }),
             context: this,
             success: function(data){
                this.addresses = data;
                this.refresh();
                this._cancel();
             },
             error: function(xhr, status, http_status){
                    console.error(status);
                    console.error(http_status);
                    // TODO: info to user....
             }
    });
}

M.Addresses.prototype._cancel = function(){
    $('input', this.$form).val('');
    $('select', this.form).val('');
    this._edited = null;

    this.show_list();
}

M.Addresses.prototype.refresh = function() {
    this.$list.find('*').remove();
    for (i = 0; i < this.addresses.length; i++) {
        var $div = $('<div>', {'class': 'col-sm-4'});
        var $adr = $('<div>', {'class': 'col-s-m-12', 'itemprop': 'adr'});

        var $delete = $('<a>', {'l-index': i}).text(M._('Delete'));
        $delete.on('click', this.delete.bind(this));
        var $edit = $('<a>', {'l-index': i}).text(M._('Edit'));
        $edit.on('click', this.edit.bind(this));
        $('<div>', {'class': 'pull-right'})
                .append($edit)
                .append(' / ')
                .append($delete)
                .appendTo($adr);

        var type = (this.addresses[i].type && type.length ? this.addresses[i].type + ' ' : '') + 'address';
        type = M._(type[0].toUpperCase() + type.substr(1)) + ':';
        $adr.append($('<div>', {'class': 'pull-left', 'itemprop': 'type'})
                            .text(type));

        $adr.append($('<h3>').text(this.addresses[i].name || ''));
        $adr.append($('<div>', {'itemprop': 'street-address'})
                            .text(this.addresses[i].address1 || ''));
        $adr.append($('<div>', {'itemprop': 'street-address'})
                            .text(this.addresses[i].address2 || ''));
        $adr.append($('<div>', {'itemprop': 'locality'})
                            .text(this.addresses[i].city || ''));
        $adr.append($('<div>', {'itemprop': 'region'})
                            .text(this.addresses[i].region || ''));
        $adr.append($('<div>', {'itemprop': 'postal-code'})
                            .text(this.addresses[i].zip || ''));
        $adr.append($('<div>', {'itemprop': 'country-name'})
                            .text(this.addresses[i].country || ''));

        $adr.appendTo($div);
        $div.appendTo(this.$list);
    }
}
