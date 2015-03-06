var M = M || {};

M.JobSingleton = function (el){
    this.el = el;
    this.$el = $(el);

    this.check();
}

M.JobSingleton.prototype.check = function (){
    $.ajax({ url: this.$el.attr('url'),
             type: 'get',
             accepts : {json: 'application/json', html: 'text/html'},
             dataType: 'json',
             context: this,     // switch context callbacks to this object
             //success: function(data){this._success(data);},
             statusCode : {
                200 : function(data){this._success(data);},
                201 : function(data){this._continue(data);},
                403 : function(data){this._denied(data);},
                404 : function(data){this._denied(data);},
                406 : function(data){this._denied(data);},
                412 : function(data){this._denied(data);},
             }
        });
}

M.JobSingleton.prototype.run = function(){
    $.ajax({ url: this.$el.attr('url'),
             type: 'post',
             accepts : {json: 'application/json', html: 'text/html'},
             dataType: 'json',
             context: this,     // switch context callbacks to this object
             statusCode : {
                200 : function(data){this._success(data);},     // if it not async
                201 : function(data){this._continue(data);},
                403 : function(data){this._denied(data);},
                404 : function(data){this._denied(data);},
                406 : function(data){this._denied(data);},
                412 : function(data){this._denied(data);},
             }
    });
}

M.JobSingleton.prototype._success = function(data){
    var link = $('<a>', { post: this.$el.attr('url') });
    link.html(this.$el.attr('background-action'));
    link.on('click', this.run.bind(this));
    this.$el.html(link);
}

M.JobSingleton.prototype._continue = function(data){
    var progress = $('div.progress',$(this.$el));
    if (progress.length == 0) {
        var progress = $('<div>', {'class': 'progress progress-striped active',
                                   style: 'width: 150px;' });
        var bar = $('<div>', {'class': 'progress-bar',
                              role: 'progressbar',
                              style: 'width: 0;' });
        progress.append(bar);
        this.$el.html(progress);
    } else {
        var bar = $('div.progress-bar', progress);
        bar.width(data.progress+"%");
    }
    window.setTimeout(this.check.bind(this), 1000);
}

M.JobSingleton.prototype._denied = function(data){
    var link = $('<a>', {});
    link.html(this.$el.attr('background-action'));
    this.$el.addClass('disabled');
    this.$el.html(link);
}
