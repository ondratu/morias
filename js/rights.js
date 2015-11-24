var M = M || {};

M.rights = {
    add : function(){},
    remove : function(){}
};

M.rights.add = function (){
    var _this = $(this);

    _this.remove();

    _this.removeClass('btn-add');
    _this.addClass('btn-remove');
    _this.click(M.rights.remove);

    var _attache_rights = $('#attache_rights');
    _attache_rights.append(_this);

    var _input = $('<input>', {
                        type: 'hidden',
                        name: 'rights',
                        value: _this.attr('value')
                    });
    _attache_rights.append(_input);
}

M.rights.remove = function (){
    var _this = $(this);

    _this.next().remove();      // input

    _this.remove();

    _this.removeClass('btn-remove');
    _this.addClass('btn-add');
    _this.click(M.rights.add);

    _this.insertBefore('#possible_rights >:last-child');
}

$(document).ready(function() {
    $('.btn-add').click(M.rights.add);
    $('.btn-remove').click(M.rights.remove);
});
