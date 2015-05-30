var M = M || {};

M.Spinner = function(period){
    this.period = period || 100;
    this.constructor();
    this.angel = 0;
}

M.Spinner.prototype.constructor = function(){
    this.$icon = $('<i>', {'class': 'fa fa-spinner spinner'})
            .appendTo('body')
            .fadeIn();
    this.interval = setInterval(this._rotate.bind(this), this.period);
}

M.Spinner.prototype.destructor = function(){
    clearInterval(this.interval);
    this.$icon.remove();
}

M.Spinner.prototype.stop = function(){
    this.$icon.fadeOut('slow', this.destructor.bind(this));
    return this;
}

M.Spinner.prototype._rotate = function() {
    this.angel = (this.angel == 360) ? 45 : this.angel + 45;
    var icon = this.$icon[0];

    icon.style.WebkitTransform = 'rotate('+ this.angel +'deg)';
    icon.style.MozTransform = 'rotate('+ this.angel +'deg)';
    icon.style.MsTransform = 'rotate('+ this.angel +'deg)';
    icon.style.OTransform = 'rotate('+ this.angel +'deg)';
    icon.style.Transform = 'rotate('+ this.angel +'deg)';
}
