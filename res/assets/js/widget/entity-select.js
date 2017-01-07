$(window).on('pytsite.widget.init:plugins.content._widget.EntitySelect', function (e, widget) {
    $(window).trigger('pytsite.widget.init:pytsite.widget._select.Select2', [widget]);
});
