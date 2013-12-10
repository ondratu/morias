var M = M || {};

M.rights = {
    add : function(){},
    remove : function(){}
};

M.rights.add = function (){
    var _this = $(this);
    var _next = _this.next();
        
    _this.remove();
    _next.remove();

    _this.removeClass('btn-add');
    _this.addClass('btn-remove');
    _this.click(M.rights.remove);

    var _attache_rights = $('#attache_rights');
    _attache_rights.append(_this);
    _attache_rights.append(_next);

    var _input = $('<input>', {
                        type: 'hidden',
                        name: 'rights',
                        value: _this.attr('value')
                    });
    _attache_rights.append(_input);
}

M.rights.remove = function (){
    var _this = $(this);
    var _next = _this.next();
    
    _next.next().remove();      // input

    _this.remove();
    _next.remove();

    _this.removeClass('btn-remove');
    _this.addClass('btn-add');
    _this.click(M.rights.add);

    var _attache_rights = $('#possible_rights');
    _attache_rights.append(_this);
    _attache_rights.append(_next);
}

$(document).ready(function() {
    $('.btn-add').click(M.rights.add);
    $('.btn-remove').click(M.rights.remove);
});
