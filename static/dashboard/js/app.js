function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function alertDanger(msg){
    $('#alertType').text('Error');
    $('#alertMsg').text(msg);
    $('.alert').addClass('alert-danger').fadeIn('slow').delay(500).fadeOut('slow');
}

function alertSuccess(msg){
    $('#alertType').text('Success');
    $('#alertMsg').text(msg);
    $('.alert').addClass('alert-success').fadeIn('slow').delay(500).fadeOut('slow');
}

function alertWarning(msg){
    $('#alertType').text('Warning');
    $('#alertMsg').text(msg);
    $('.alert').addClass('alert-warning').fadeIn('slow').delay(1000).fadeOut('slow');
}

function alertInfo(msg){
    $('#alertType').text('Info');
    $('#alertMsg').text(msg);
    $('.alert').addClass('alert-info').fadeIn('slow').delay(2000).fadeOut('slow');
}

$('.custom-file input').change(function (e) {
    var files = [];
    for (var i = 0; i < $(this)[0].files.length; i++) {
        files.push($(this)[0].files[i].name);
    }
    $(this).next('.custom-file-label').html(files.join(', '));
});

$(document).ready(function() {

    $(document).on('click','.folderButton', function(e) {
        e.preventDefault();
        var folder_id = $('input[name="master"]').val();
        var app_id = $('input[name="app_id"]').val();
        var folder_name = $('input[name="folder"]').val();
        const csrftoken = getCookie('csrftoken');

        req = $.ajax({
            url : `/manage/${app_id}/${folder_id}`,
            headers: {'X-CSRFToken': csrftoken},
            type : 'POST',
            data : { folder: folder_name, master: folder_id}
        });
        req.done(function (data) {
            $('#refreshSection').html(data);
            $('#exampleModalCenter').modal('hide');
        })
    });

});

$(document).ready(function() {

    $(document).on('click','.fileButton', function(e) {
        e.preventDefault();

    // const axios = require('axios');
    const csrftoken = getCookie('csrftoken');
    var formData = new FormData();
    var ins = document.getElementById('file_upload').files.length;
    for (var x = 0; x < ins; x++) {
    formData.append("files_to_upload", document.getElementById('file_upload').files[x]);
    }
    var app_id = $('input[name="file_app_id"]').val();
    var folder_id = $('input[name="master"]').val();
    formData.append('master', folder_id);

    req = $.ajax({
        type: 'POST',
        url: `/manage/${app_id}/${folder_id}`,
        data: formData,
        processData: false,
        contentType: false,
        headers: {
            "X-CSRFToken": csrftoken,
        }
    });
    req.done(function (data) {
        $('#refreshSection').html(data);
        $('#fileModalCenter').modal('hide');
    })
});
});


$(document).ready(function() {

    $(document).on('click','.deleteButton', function(e) {
        e.preventDefault();
        var folder_id = $('input[name="folder_id"]').val();
        var current_folder = $('input[name="master"]').val();
        var file_id = $('input[name="file_id"]').val();
        var app_id = $('input[name="file_app_id"]').val();
        var ajax = $('input[name="ajax"]').val();
        const csrftoken = getCookie('csrftoken');

        req = $.ajax({
            url : `/manage/${app_id}/${current_folder}`+ '?' + $.param({"folder_id": folder_id, "file_id" : file_id, "ajax": ajax}),
            headers: {'X-CSRFToken': csrftoken},
            type : 'DELETE',
        });

        req.done(function (data) {
            if (ajax=="True"){
            $('#refreshSection').html(data);
            alertSuccess('Item deleted successfully');
            }
            else{location.reload()}
            $('#deleteModalCenter').modal('hide');
        })
    });

});

$(document).ready(function() {

    $(document).on('click','.deleteAccountButton', function(e) {
        const csrftoken = getCookie('csrftoken');
        e.preventDefault();
        req = $.ajax({
            url : `/settings`,
            headers: {'X-CSRFToken': csrftoken},
            type : 'DELETE',
        });
        req.done(function (data) {
            location.reload()
        })
    });
});


$(document).ready(function () {
    const csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        url: '/settings/',
        headers: {'X-CSRFToken': csrftoken},
        type : 'PUT',
        success: function (data) {
                alertSuccess("Your preference is saved!");
        },
        error: function () {
            alertDanger("Something went wrong!x");
        }
    });

    $('#ajax_option').on('change',function() {
            req=$.ajax({data: {ajax_enabled: this.checked}});
            req.done(function()
                {location.reload()}
            )
    });

    $('#offers_option').on('change',function() {
            $.ajax({data: {new_offers_alert: this.checked}});
    });

    $('#down_time_option').on('change',function() {
            $.ajax({data: {down_time_alert: this.checked}});
    });

    $('#maintenance_option').on('change',function() {
            $.ajax({data: {maintenance_break_alert: this.checked}});
    });

    $('#email_alert_option').on('change',function() {
            $.ajax({data: {email_notification: this.checked}});
    });

    $('#app_status_option').on('change',function() {
            $.ajax({data: {app_status_alert: this.checked}});
    });

    $('#terminated_apps').on('change',function() {
            $.ajax({data: {display_terminated_apps: this.checked}});
    });
})
