var M = M || {};

M.hiddener = {
    open : function(btn, duration) {
        var duration = (duration == null) ? 100 : duration;
        var chl = btn.children();
        var elm = $('#'+btn.attr('elm'));

        elm.slideDown(duration);
        btn.attr('state', 'open');
        chl.removeClass('glyphicon-chevron-down');
        chl.addClass('glyphicon-chevron-up');
    },

    close: function(btn) {
        var duration = (duration == null) ? 100 : duration;
        var chl = btn.children();
        var elm = $('#'+btn.attr('elm'));

        elm.slideUp(100);
        btn.attr('state', 'close');
        chl.removeClass('glyphicon-chevron-up');
        chl.addClass('glyphicon-chevron-down');
    },

    change : function() {
        var btn = $(this);

        if (btn.attr('state') == 'close') {
            M.hiddener.open(btn);
        } else {
            M.hiddener.close(btn);
        }
    }
};

$(document).ready(function() {
    $('.swittcher').click(M.hiddener.change);
});
