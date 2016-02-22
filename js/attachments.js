var M = M || {};

M.ajax_upload_progress = function() {
    var xhr = new XMLHttpRequest();
    return !! (xhr && ('upload' in xhr) && ('onprogress' in xhr.upload));
}

/* ------------------------------------------------------------------------ *
 *                              AttachmensUploader                          *
 * ------------------------------------------------------------------------ */
M.AttachmensUploader = function(object_type, object_id, params){
    params = params || {};
    this.$tab = $('tab' in params ? params['tab'] : '#attachments_upload');
    this.$select = $('[action=select]', this.$tab);
    this.$upload = $('[action=upload]', this.$tab);

    this.object_type = object_type;
    this.object_id   = object_id;

    this._uploading_files = [];
    this._selected_files = [];

    this._uploding_file = null;
    this.$_uploding_row = null;

    this.constructor();
}

M.AttachmensUploader.prototype.constructor = function (){
    this.input = $('<input>', { type: 'file',
                               multiple: 'multiple',
                               style: 'display: none;'});
    //this.input.on('change', this._start_upload.bind(this));
    this.input.on('change', this._select.bind(this));
    this.input.appendTo(this.$select.parent());

    this.$select.on('click', this._input_click.bind(this));

    this.$upload.on('click', this._start_upload.bind(this));

}

M.AttachmensUploader.prototype._select = function() {
    var _new_files = this.input.prop('files');
    for (var i = 0; i < _new_files.length; i++){
        var it = _new_files[i];
        var preview = '';
        if (window.FileReader && it.type.search('image/') == 0){
            preview = $('<img>', {style: "max-width: 100%;",
                                  alt: M._('preview')});

            preview._onload = function(e) {
                this.attr('src', e.target.result);
            }
            var reader = new FileReader();
            reader.onload = preview._onload.bind(preview);
            reader.readAsDataURL(it);

        }
        var remove = $('<a>',{'file-name': it.name}).html(M._('Remove'));
        remove.on('click', this.remove_selected.bind(this));
        //var upload = $('<a>',{'file-name': it.name}).html(M._('Upload'));
        //upload.on('click', this._start_upload.bind(this));

        var row = $('<div>', {'class': 'row'})
            .append($('<div>', {'class': 'col-md-5'}).html(it.name))
            .append($('<div>', {'class': 'col-md-2'}).html(preview))
            .append($('<div>', {'class': 'col-md-3'})
                //.append(remove).append(' / ').append(upload) );
                .append(remove) );
        row.appendTo(this.$tab);
        this._selected_files.push(it);
    }
}

M.AttachmensUploader.prototype.remove_selected = function(ev){
    var $target = $(ev.target);
    var file_name = $target.attr('file-name')
    for (var i = 0; i < this._selected_files.length; i++){
        if (this._selected_files[i].name == file_name){
            this._selected_files.splice(i,1);
            break;
        }
    }
    $target.parent().parent().fadeOut('fast', function(){ $(this).remove(); });
}

M.AttachmensUploader.prototype._input_click = function (ev){
    this.input.trigger('click', ev);
}

M.AttachmensUploader.prototype._start_upload = function (){
    this._uploading_files = this._uploading_files.concat(this._selected_files);
    if (! this._uploding_file)
        this._upload();
}

M.AttachmensUploader.prototype._next_upload = function (){
    for (var i = 0; i < this._selected_files.length; i++){
        if (this._selected_files[i].name == this._uploding_file.name){
            this._selected_files.splice(i,1);
            break;
        }
    }
    // TODO: refresh ao
    this.$_uploding_row.fadeOut(2000, function(){ $(this).remove()});
    this.$_uploding_row = null;
    this._uploding_file = null;
    if (this._uploading_files.length > 0){
        this._upload();
    }
}

M.AttachmensUploader.prototype._upload = function (){
    this._uploding_file = this._uploading_files.shift();
    this.$_uploding_row = $('a[file-name="'+this._uploding_file.name+'"]', this.$tab).parent().parent();
    $('<div>', {'class': 'col-md-2'})
        .append($('<div>',{'class': 'progress progress-striped active'})
            .append($('<div>', {'class': 'progress-bar', role : 'progressbar', style:'width : 0px;'})))
        .appendTo(this.$_uploding_row);
    var form_data = new FormData();
    // send first file from selected files queue
    form_data.append("object_type", this.object_type);
    form_data.append("object_id", this.object_id);
    form_data.append("attachment", this._uploding_file);

    var ao = {
        url: "/admin/attachments/add",
        dataType: 'json',
        cache: false,
        contentType: false, // Set content type to false as jQuery will tell the server its a query string request
        processData: false, // Don't process the files
        data: form_data,
        type: 'post',
        context: this,
        complete: function() {this._complete();},
        success: function(data){this._next_upload(data);}
    };
    if (M.ajax_upload_progress()){
        var _this = this;
        ao.xhr = function() {
            var xhr = new window.XMLHttpRequest();
            xhr.upload.onprogress =  function(e) { _this._progress(e) };
            return xhr;
        }
    }

    $.ajax(ao);
}

M.AttachmensUploader.prototype._progress = function(e){
    var done = e.position || e.loaded;
    var total = e.totalSize || e.total;
    var percents = Math.floor((done * 100)/total);
    $('div[role="progressbar"]', this.$_uploding_row).attr('style', 'width: '+percents+'%;');
}

M.AttachmensUploader.prototype._complete = function(){
    $('div[role="progressbar"]', this.$_uploding_row).attr('style', 'width: 100%;');
}


/* ------------------------------------------------------------------------ *
 *                              AttachmensObject                            *
 * ------------------------------------------------------------------------ */
M.AttachmensObject = function(object_type, object_id, params){
    params = params || {};
    tab = 'tab' in params ? params['tab'] : '#attachments_object';
    this.thumb_size = 'thumb_size' in params ? params['thumb_size'] : '320x200';

    this.$tab = $(tab);

    this.object_type = object_type;
    this.object_id = object_id;

    this.update();
    $('a[data-toggle="tab"][href="'+tab+'"]').on('show.bs.tab',
                                                  this.update.bind(this) );
}

M.AttachmensObject.prototype.update = function(){
    $.ajax({ url: "/admin/attachments/"+this.object_type+'/'+this.object_id
                 +"?thumb_size="+this.thumb_size,
             type: 'get',
             accepts : {json: 'application/json', html: 'text/html'},
             dataType: 'json',
             context: this,
             success: function(data){this._view(data)}
    });
}

M.AttachmensObject.prototype._remove = function (ev){
    var $target = $(ev.target);
    $.ajax({ url: '/admin/attachments/'+$target.attr('object-type')
                 +'/'+$target.attr('object-id')+'/'+$target.attr('webname')
                 +'/detach?thumb_size='+this.thumb_size,
             type: 'post',
             accepts : {json: 'application/json', html: 'text/html'},
             dataType: 'json',
             context: this,
             success: function(data){
                    this.$tab.children().remove();
                    this._view(data);
             },
             error: function(xhr, status, http_status){
                    console.error(status);
                    console.error(http_status);
             }
    });
}

M.AttachmensObject.prototype._view = function(data){
    this.$tab.html('');
    for (var i = 0; i < data.items.length; i++){
        var it = data.items[i];
        var preview = '';
        if (it.mime_type.search('image/svg') == 0 ) {
            preview = $('<div>', {
                style: "background-image: url('/attachments/data/"+it.webname+"');"
                     + "background-repeat: no-repeat;"
                     + "background-size: 100%;"
                     + "background-position: 50% 50%;"
            });
        } else if (it.mime_type.search('image/') == 0){
            preview = $('<div>', {
                style: "background-image: url('/attachments/"+it.webname+"/"
                                                +this.thumb_size+"?hash="+it.resize_hash+"');"
                     + "background-repeat: no-repeat;"
                     + "background-size: 100%;"
                     + "background-position: 50% 50%;"
            });
        }
        var remove = $('<a>', { 'webname': it.webname,
                                'object-type': this.object_type,
                                'object-id': this.object_id}).html(M._('Dettach'));
        remove.on('click', this._remove.bind(this));
        var row = $('<div>',{'class': 'row', md5: it.data.md5})
                        .append($('<div>', {'class': 'col-md-5 text', webname: it.webname})
                                    .html($('<a>', {'href': '/attachments/'+ it.webname+'/realname'}).text(it.file_name)))
                        .append($('<div>', {'class': 'col-md-2 preview'}).html(preview))
                        .append($('<div>', {'class': 'col-md-3 text'}).html(it.mime_type))
                        .append($('<div>', {'class': 'col-md-2 text'}).append(remove) );
        row.appendTo(this.$tab);
    };
}


/* ------------------------------------------------------------------------ *
 *                              AttachmensServer                            *
 * ------------------------------------------------------------------------ */
M.AttachmensServer = function(object_type, object_id, params){
    params = params || {};
    this.$tab = $('tab' in params ? params['tab'] : '#attachments_server');
    this.thumb_size = 'thumb_size' in params ? params['thumb_size'] : '320x200';

    this.object_type = object_type;
    this.object_id = object_id;

    this.update();
}

M.AttachmensServer.prototype.update = function(){
    $.ajax({ url: "/admin/attachments/"+this.object_type+'/'+this.object_id
                 +"/not?thumb_size="+this.thumb_size,
             type: 'get',
             accepts : {json: 'application/json', html: 'text/html'},
             dataType: 'json',
             context: this,
             success: function(data){this._view(data)}
    });
}

M.AttachmensServer.prototype._view = function(data){
    for (var i = 0; i < data.items.length; i++){
        var it = data.items[i];
        var preview = '';

        if (it.mime_type.search('image/') == 0){
            preview = $('<div>', {
                style: "background-image: url('/attachments/"+it.webname+"/"
                                             +this.thumb_size+"?hash="
                                             +it.resize_hash+"');"
                     + "background-repeat: no-repeat;"
                     + "background-size: 100%;"
                     + "background-position: 50% 50%;"
            });
        }
        var actions = '';
        var row = $('<div>',{'class': 'row', md5: it.data.md5})
                        .append($('<div>', {'class': 'col-md-5 text', webname: it.webname}).html(it.file_name))
                        .append($('<div>', {'class': 'col-md-2 preview'}).html(preview))
                        .append($('<div>', {'class': 'col-md-3 text'}).html(it.mime_type))
                        .append($('<div>', {'class': 'col-md-2 text'}).html(actions));
        row.appendTo(this.$tab);
    };
}
