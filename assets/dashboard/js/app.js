function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function alertDanger(msg){
    $('#dAlertMsg').text(msg);
    $('#dangerAlert').fadeIn('slow').delay(500).fadeOut('slow');
}

function alertSuccess(msg){
    $('#sAlertMsg').text(msg);
    $('#successAlert').fadeIn('slow').delay(500).fadeOut('slow');
}

function alertWarning(msg){
    $('#wAlertMsg').text(msg);
    $('#warningAlert').fadeIn('slow').delay(1000).fadeOut('slow');
}

function alertInfo(msg){
    $('#iAlertMsg').text(msg);
    $('#infoAlert').fadeIn('slow').delay(2000).fadeOut('slow');
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
            data : { folder: folder_name, master: folder_id},
            success: function (data) {
                $('#refreshSection').html(data);
                $('#exampleModalCenter').modal('hide');
                alertSuccess("Folder is created");
            },
            error: function (response) {
                switch (response.status) {
                    case 403:
                        alertWarning("Folder name should not contain spaces.");
                        break;
                    case 405:
                        alertWarning("Folder by that name already exist.");
                        break;
                    case 500:
                        alertDanger("Internal server error.");
                        break;
                    default:
                        alertDanger("Something went wrong.");
                }
            },
        });
    });

});

$(document).ready(function() {

    $(document).on('click','.fileButton', function(e) {
        e.preventDefault();
    let exceeded_limit = false
    const csrftoken = getCookie('csrftoken');
    var formData = new FormData();
    let files =  document.getElementById('file_upload').files

    for (var x = 0; x < files.length; x++) {
      if(files[x].size > 2500000){
          exceeded_limit = true
      }
      else {
          formData.append("files_to_upload", files[x]);
      }
    }
    var app_id = $('input[name="file_app_id"]').val();
    var folder_id = $('input[name="master"]').val();
    formData.append('master', folder_id);
    if(exceeded_limit===true && files.length===1){
                  alertWarning("Some files exceed the max size limit");
    }
    else{
        if(exceeded_limit===true){alertWarning("Some files exceed the max size limit");}
    $.ajax({
        type: 'POST',
        url: `/manage/${app_id}/${folder_id}`,
        data: formData,
        processData: false,
        contentType: false,
        headers: {
            "X-CSRFToken": csrftoken,
        },
        success: function (data) {
            console.log(data)
            $('#refreshSection').html(data);
            $('#fileModalCenter').modal('hide');
            alertSuccess("File is uploaded");
        },
        error: function (response) {
            switch (response.status) {
                case 500: alertDanger("Internal server error"); break;
                case 403: alertWarning("Some files exceed max upload limit."); break;
                default: alertDanger("Something went wrong!");
            }

        },
            xhr: function(){
                //upload Progress
                var xhr = $.ajaxSettings.xhr();
                if (xhr.upload) {
                    xhr.upload.addEventListener('progress', function(event) {
                        var percent = 0;
                        var position = event.loaded || event.position;
                        var total = event.total;
                        if (event.lengthComputable) {
                            percent = Math.ceil(position / total * 100);
                        }
                        //update progressbar
                        $("#progress-wrp" +" .progress-bar").css("width", + percent +"%");
                        $("#progress-wrp" + " .status").text(percent +"%");
                    }, true);
                }
                return xhr;
            },
    });}
});
});


$(document).ready(function() {

    $(document).on('click','.deleteButton', function(e) {
        e.preventDefault();
        $('#deleteModalCenter').modal('hide');
        var folder_id = $('input[name="folder_id"]').val();
        var current_folder = $('input[name="master"]').val();
        var file_id = $('input[name="file_id"]').val();
        var app_id = $('input[name="file_app_id"]').val();
        const csrftoken = getCookie('csrftoken');

        req = $.ajax({
            url : `/manage/${app_id}/${current_folder}`+ '?' + $.param({"folder_id": folder_id, "file_id" : file_id}),
            headers: {'X-CSRFToken': csrftoken},
            type : 'DELETE',
            success: function (data) {
                $('#refreshSection').html(data);
                alertSuccess("Item is deleted")
            },
            error: function () {
                alertDanger("Something went wrong!")
            }
        });
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
        error: function (jqXHR, textStatus, errorThrown) {
            alertDanger(errorThrown);
        }
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