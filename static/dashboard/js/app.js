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
        const csrftoken = getCookie('csrftoken');

        req = $.ajax({
            url : `/manage/${app_id}/${current_folder}`+ '?' + $.param({"folder_id": folder_id, "file_id" : file_id}),
            headers: {'X-CSRFToken': csrftoken},
            type : 'DELETE',
            data : { file_id: file_id, folder_id: folder_id}
        });
        req.done(function (data) {
            $('#refreshSection').html(data);
            $('#deleteModalCenter').modal('hide');
        })
    });

});