var M = M || {};
M.Eshop = M.Eshop || {};

M.Eshop.ShoppingAddress = function(data, addresses, params){
    this.addresses = addresses || [];
    params = params || {};
    this.$way = $('way' in params ? params['way'] : 'a[way]');
    this.$form = $('form' in params ? params['form'] : 'form[role=shopping-address]');
    this.$billing_addr = $('billing_addr' in params ? params['billing_addr'] : '#billing_addr');
    this.$shipping_addr = $('shipping_addr' in params ? params['shipping_addr'] : '#shipping_addr');

    this.billing_address = data.billing_address;
    this.shipping_address = data.shipping_address;
    this.constructor();
}

M.Eshop.ShoppingAddress.prototype.constructor = function(){
    if (this.shipping_address.same_as_billing)
        $('.item', this.$shipping_addr).hide();
    $('select[name=billing_address]').on('change', this.select_address.bind(this));
    $('select[name=shipping_address]').on('change', this.select_address.bind(this));
    $('input[name=same_as_billing]').on('change', this.switch_shipping.bind(this));
    this.$way.on('click', this.send_form.bind(this));
}

M.Eshop.ShoppingAddress.prototype.select_address = function(ev){
    var $target = $(ev.target);
    var $parent = $target.parents('[role=form]');
    var index = $target.val();
    var name = ev.target.name;

    if ((index >= 0) &&
        ((name == 'billing_address') ||
         (name == 'shipping_address' && !this.shipping_address.same_as_billing) ))
     {
        var addr = this.addresses[index];
        var prefix = name.substring(0, name.search('_') + 1);
        $('input[name='+prefix+'name]', $parent).val(addr.name);
        $('input[name='+prefix+'address1]', $parent).val(addr.address1 || ' ');
        $('input[name='+prefix+'address2]', $parent).val(addr.address2 || ' ');
        $('input[name='+prefix+'city]', $parent).val(addr.city || ' ');
        $('input[name='+prefix+'region]', $parent).val(addr.region || ' ');
        $('input[name='+prefix+'zip]', $parent).val(addr.zip || ' ');
        $('input[name='+prefix+'country]', $parent).val(addr.country || ' ');
    }
}

M.Eshop.ShoppingAddress.prototype.switch_shipping = function(ev){
    if (ev.target.checked) {
        this.shipping_address.same_as_billing = true;
        $('.item', this.$shipping_addr).hide();
    } else {
        this.shipping_address.same_as_billing = false;
        $('.item', this.$shipping_addr).show();
    }
}

M.Eshop.ShoppingAddress.prototype.send_form = function(ev) {
    var spinner = new M.Spinner();
    $('input[name=way]', this.$form).val($(ev.target).attr('way'));
    this.$form.submit();
    delete spinner.stop();
}
