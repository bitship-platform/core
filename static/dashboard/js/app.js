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
    let files = [];
    for (let i = 0; i < $(this)[0].files.length; i++) {
        files.push($(this)[0].files[i].name);
    }
    $(this).next('.custom-file-label').html(files.join(', '));
});

$(document).ready(function() {

    $(document).on('click','.folderButton', function(e) {
        e.preventDefault();
        let folder_id = $('input[name="master"]').val();
        let app_id = $('input[name="app_id"]').val();
        let folder_name = $('input[name="folder"]').val();
        const csrftoken = getCookie('csrftoken');
        if(folder_name !== ""){
        $.ajax({
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
        });}
        else {alertInfo("Folder name cannot be empty");}
    });

});

$(document).ready(function() {

    $(document).on('click','.fileButton', function(e) {
        e.preventDefault();
    let exceeded_limit = false
    const csrftoken = getCookie('csrftoken');
    let formData = new FormData();
    let files =  document.getElementById('file_upload').files
    if(files.length===0){return}
    for (let x = 0; x < files.length; x++) {
      if(files[x].size > 2500000){
          exceeded_limit = true
      }
      else {
          formData.append("files_to_upload", files[x]);
      }
    }
    let app_id = $('input[name="file_app_id"]').val();
    let folder_id = $('input[name="master"]').val();
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
                let xhr = $.ajaxSettings.xhr();
                if (xhr.upload) {
                    xhr.upload.addEventListener('progress', function(event) {
                        let percent = 0;
                        let position = event.loaded || event.position;
                        let total = event.total;
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
        let folder_id = $('input[name="folder_id"]').val();
        let current_folder = $('input[name="master"]').val();
        let file_id = $('input[name="file_id"]').val();
        let app_id = $('input[name="file_app_id"]').val();
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
        let input_value = $('input[name="accountTerminationField"]').val();
        if(input_value.toLowerCase() === "terminate account"){
        req = $.ajax({
            url : `/settings`,
            headers: {'X-CSRFToken': csrftoken},
            type : 'DELETE',
        });
        req.done(function (data) {
            location.reload();
        })}
        else{
            alertInfo("Incorrect input format! Please try again.");
        }
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

// $(document).ready(function() {
//
//     $(document).on('click','.renameFolderButton', function(e) {
//         e.preventDefault();
//         let folder_name = $('input[name="rename_folder"]').val();
//         let folder_id = $('#renameFolderId').val();
//         const csrftoken = getCookie('csrftoken');
//         $.ajax({
//             url: `/manage/`,
//             headers: {'X-CSRFToken': csrftoken},
//             type: 'PUT',
//             data: {folder: folder_name, folder_id: folder_id},
//             success:function (data)
//             {
//               $('#refreshSection').html(data);
//               $('#renameFolderModal').modal('hide');
//               alertSuccess(`Folder renamed to ${folder_name}`);
//             },
//             error:function () {
//                 alertDanger('Something went wrong')
//             },
//         });
//     });
// });

$(document).ready(function() {

    $(document).on('click','.renameFileButton', function(e) {
        e.preventDefault();
        let file_name = $('input[name="rename_file"]').val();
        let file_id = $('#renameFileId').val();
        const csrftoken = getCookie('csrftoken');
        $.ajax({
            url: `/manage/`,
            headers: {'X-CSRFToken': csrftoken},
            type: 'PUT',
            data: {file_name: file_name, file_id: file_id},
            success:function (data)
            {
              $('#refreshSection').html(data);
              $('#renameFileModal').modal('hide');
              alertSuccess(`File renamed to ${file_name}`);
            },
            error:function (resp) {
                if(resp.status === 403)
                {
                    let r = jQuery.parseJSON(resp.responseText);
                    alertWarning(r["message"])
                }
                else {
                    alertDanger('Something went wrong')
                }
            },
        });
    });
});

$(document).ready(function() {

    $(document).on('click','.downloadFileButton', function(e) {
        let file_id = $(this).attr("data-value")
        const csrftoken = getCookie('csrftoken');

        $.ajax({
            url: `/media/download/`+ '?' + $.param({"file_id" : file_id}),
            headers: {'X-CSRFToken': csrftoken},
            type: 'GET',
            success:function (data)
            {
              alertSuccess(`File will be download shortly`);
            },
            error:function () {
                alertDanger('Something went wrong')
            },
        });
    });


    $(document).on('click','.refreshMainButton', function(e) {
        const csrftoken = getCookie('csrftoken');
        let app_id = $('input[name="app_id"]').val();

        $.ajax({
            url: `/app/manage/` + '?' + $.param({"app_id": app_id,}),
            headers: {'X-CSRFToken': csrftoken},
            type: 'GET',
            success:function (data)
            {
                console.log(data);
              $(".mainFileRefresh").html(data);
              alertSuccess(`Refreshed main file list.`);
            },
            error:function (resp) {

                alertDanger('Something went wrong... ');
            },
        });
    });


    $(document).on('click','#appDeployButton', function(e) {
        const csrftoken = getCookie('csrftoken');
        let app_id = $('input[name="app_id"]').val();
        $("#appDeployButton").prop('disabled', true);

        $.ajax({
            url: `/app/manage/`,
            headers: {'X-CSRFToken': csrftoken},
            type: 'POST',
            data: {app_id: app_id},
            success:function (data)
            {
              $(".manageRefreshSection").html(data);
              $("#appDeployButton").prop('disabled', false);
              $("#appStopButton").prop('disabled', false);
              $("#appStartButton").prop('disabled', true);
              let $response = $(data);
              let progressUrl = $response.filter('#progressBarUrl').val();
              CeleryProgressBar.initProgressBar(progressUrl)
              alertSuccess(`Deployment in progress...`);
            },
            error:function (resp) {
                $("#appDeployButton").prop('disabled', false);
                let r = jQuery.parseJSON(resp.responseText);
                if(resp.status === 503) {
                    alertInfo(r["message"])
                }else{
                    alertDanger(r["message"])
                }
            },
        });
    });

    $(document).on('click','#appStartButton', function(e) {
        const csrftoken = getCookie('csrftoken');
        let app_id = $('input[name="app_id"]').val();

        $.ajax({
            url: `/app/manage/`,
            headers: {'X-CSRFToken': csrftoken},
            type: 'PUT',
            data: {app_id: app_id, action: "start"},
            success:function (data)
            {
              $("#appStartButton").prop('disabled', true);
              $("#appStopButton").prop('disabled', false);
              alertSuccess(`App started successfully...`);
            },
            error:function () {
                alertDanger('Failed to start app... please try redeploying')
            },
        });
    });

    $(document).on('click','#appStopButton', function(e) {
        const csrftoken = getCookie('csrftoken');
        let app_id = $('input[name="app_id"]').val();

        $.ajax({
            url: `/app/manage/`,
            headers: {'X-CSRFToken': csrftoken},
            type: 'PUT',
            data: {app_id: app_id, action: "stop"},
            success:function (data)
            {
              $("#appStopButton").prop('disabled', true);
              $("#appStartButton").prop('disabled', false);
              alertSuccess(`App stopped successfully...`);
            },
            error:function () {
                alertDanger('Failed to stop app... please try again')
            },
        });
    });

    $(document).on('click','.appRestartButton', function(e) {
        const csrftoken = getCookie('csrftoken');
        let app_id = $('input[name="app_id"]').val();

        $.ajax({
            url: `/app/manage/`,
            headers: {'X-CSRFToken': csrftoken},
            type: 'PUT',
            data: {app_id: app_id, action: "restart"},
            success:function (data)
            {
              $("#appStopButton").prop('disabled', false);
              $("#appStartButton").prop('disabled', false);
              alertSuccess(`App restarted successfully...`);
            },
            error:function () {
                alertDanger('Failed to restart app... please try redeploying')
            },
        });
    });

    $(document).on('click','.appTerminateButton', function(e) {
        const csrftoken = getCookie('csrftoken');
        let input_value = $('input[name="appTerminationField"]').val();
        let app_id = $('input[name="app_id"]').val();
        if(input_value.toLowerCase() === "terminate"){
        $.ajax({
            url: `/app/manage/` + '?' + $.param({"app_id": app_id,}) ,
            headers: {'X-CSRFToken': csrftoken},
            type: 'DELETE',
            success:function (data)
            {
              $("#appStopButton").prop('disabled', false);
              $("#appStartButton").prop('disabled', false);
              window.location.replace("https://dashboard.novanodes.com/panel/");
            },
            error:function () {
                alertDanger('Failed to terminate app... please contact administrator')
            },
        });}
        else{
            alertInfo('Incorrect input format! Please try again. ')
        }
    });


    $(document).on('click','#savePythonConfigurationButton', function(e) {
        const csrftoken = getCookie('csrftoken');
        let main_executable = $("#appMainSelect").val()
        let python_version = $("#pythonVersionSelectPref").val()
        console.log(python_version, main_executable)
        if((main_executable!==undefined)||(python_version!==undefined))
        {
            $.ajax({
                url: `/app/config/`,
                headers: {'X-CSRFToken': csrftoken},
                type: 'PUT',
                data: {main_executable: main_executable, python_version: python_version},
                success: function (data) {
                    $("#appStopButton").prop('disabled', false);
                    $("#appStartButton").prop('disabled', false);
                    $('#pythonAppConfigurationModal').modal('hide');
                    alertSuccess(`App configuration set successfully...`);
                },
                error: function () {
                    alertDanger('Failed to set configuration... contact admin')
                },
            });
        }
        else {
            alertInfo("Some configration missing")
        }
    });


});