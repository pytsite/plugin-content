$(function () {
    // Views count
    $('.content-entity').each(function () {
        var model = $(this).data('model');
        var id = $(this).data('entityId');
        if (model && id) {
            pytsite.httpApi.patch('content/view_count', {
                model: model,
                id: id
            });
        }
    });
});
