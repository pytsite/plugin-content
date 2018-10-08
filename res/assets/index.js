import '@pytsite/form';

const $ = require('jquery');
const httpApi = require('@pytsite/http-api');
const responsive = require('@pytsite/responsive');

$('.content-entity, #content-entity').each(function () {
    var model = $(this).data('model');
    var entityId = $(this).data('entityId');

    // Views count
    if (model && entityId)
        httpApi.patch('content/view/' + model + '/' + entityId);

    // Responsive images and iframes
    responsive.all();
});

// Auto fill of 'Description' input
$('.content-m-form').on('forward:form:pytsite', function (e, form) {
    form.em.find('.widget-uid-description input').focus(function () {
        var descriptionInput = $(this);
        var titleInput = form.em.find('.widget-uid-title input');

        if (descriptionInput.val() === '')
            descriptionInput.val(titleInput.val());
    });
});
