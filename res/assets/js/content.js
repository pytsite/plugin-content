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

// Auto fill of 'Description' input
$('.content-m-form').on('pytsiteFormForward', function (e, form) {
    form.em.find('.widget-uid-description input').focus(function () {
        var descriptionInput = $(this);
        var titleInput = form.em.find('.widget-uid-title input');

        if (descriptionInput.val() == '')
            descriptionInput.val(titleInput.val());
    });
});
