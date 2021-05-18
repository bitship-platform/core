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
            $('#refreshSection').html(data);
            $('#fileModalCenter').modal('hide');
            alertSuccess("File is uploaded");
        },
        error: function (response) {
            switch (response.status) {
                case 500: alertDanger("Internal server error"); break;
                case 403: alertWarning("Forbidden file type uploaded"); break;
                case 503: alertWarning("Some files exceed max upload limit."); break;
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

    $('#beta_features').on('change',function() {
            $.ajax({data: {beta_tester: this.checked}});
    });
    $('#become_affiliate').on('change',function() {
            $.ajax({data: {affiliate: this.checked}});
    });
})


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
              $("#manageRefreshSection").html(data);
              $("#appDeployButton").prop('disabled', false);
              $("#appStopButton").prop('disabled', false);
              $("#appStartButton").prop('disabled', true);
              alertSuccess(`Deployment in progress...`);

                let interval = setInterval(function (){
                  $.ajax({
                    url: `/app/panel/options/` + '?' + $.param({"app_id": app_id,}) ,
                    headers: {'X-CSRFToken': csrftoken},
                    type: 'GET',
                    success:function (data)
                    {
                      $("#manageRefreshSection").html(data);
                      $("#appDeployButton").prop('disabled', false);
                      $("#appStopButton").prop('disabled', false);
                      $("#appStartButton").prop('disabled', true);
                      swal("Deployed!", "Your app should now be running", "success");
                      clearInterval(interval);
                    },
                    error: function (jqXHR, textStatus, errorThrown){
                        if(jqXHR.status===503){
                           $("#manageRefreshSection").html(jqXHR.responseText);
                          $("#appDeployButton").prop('disabled', false);
                          swal("Deploy Failed!", "Please try running your app locally and see if it works", "error");
                          clearInterval(interval);
                        }
                        else if(jqXHR.status===500){
                          $("#manageRefreshSection").html(jqXHR.responseText);
                          $("#appDeployButton").prop('disabled', false);
                          swal("Build Rejected!", "Please inspect your code and try again", "error");
                          clearInterval(interval);
                        }
                    }
                    });
                }, 5000)

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
        $("#appStartButton").prop('disabled', true);

        $.ajax({
            url: `/app/manage/`,
            headers: {'X-CSRFToken': csrftoken},
            type: 'PUT',
            data: {app_id: app_id, action: "start"},
            success:function (data)
            {
              $("#manageRefreshSection").html(data);
              $("#appStopButton").prop('disabled', false);
              alertSuccess(`App started successfully...`);
            },
            error:function () {
                $("#appStartButton").prop('disabled', false);
                swal("Failed!", "Failed to start app. Please try redeploying.", "error");
            },
        });
    });

    $(document).on('click','#appStopButton', function(e) {
        const csrftoken = getCookie('csrftoken');
        let app_id = $('input[name="app_id"]').val();

        $("#appStopButton").prop('disabled', true);

        $.ajax({
            url: `/app/manage/`,
            headers: {'X-CSRFToken': csrftoken},
            type: 'PUT',
            data: {app_id: app_id, action: "stop"},
            success:function (data)
            {
              $("#manageRefreshSection").html(data);
              $("#appStartButton").prop('disabled', false);
              alertSuccess(`App stopped successfully...`);
            },
            error:function () {
                $("#appStopButton").prop('disabled', true);
                swal("Failed!", "Failed to stop app. Please refresh the page and try again.", "error");
            },
        });
    });

    $(document).on('click','.appRestartButton', function(e) {
        const csrftoken = getCookie('csrftoken');
        let app_id = $('input[name="app_id"]').val();
        $(".appRestartButton").prop('disabled', true);

        $.ajax({
            url: `/app/manage/`,
            headers: {'X-CSRFToken': csrftoken},
            type: 'PUT',
            data: {app_id: app_id, action: "restart"},
            success:function (data)
            {
              $("#appStopButton").prop('disabled', false);
              $("#appStartButton").prop('disabled', true);
              alertSuccess(`App restarted successfully...`);
            },
            error:function () {
                $(".appRestartButton").prop('disabled', false);
                swal("Failed!", "Failed to restart app. Please try redeploying.", "error");
            },
        });
    });

    $(document).on('click','.appTerminateButton', function(e) {
        const csrftoken = getCookie('csrftoken');
        let input_value = $('input[name="appTerminationField"]').val();
        let app_id = $('input[name="app_id"]').val();
        if(input_value.toLowerCase() === "terminate"){
            $(".appTerminateButton").prop('disabled', true);
        $.ajax({
            url: `/app/manage/` + '?' + $.param({"app_id": app_id,}) ,
            headers: {'X-CSRFToken': csrftoken},
            type: 'DELETE',
            success:function (data)
            {
              window.location.replace("https://dashboard.novanodes.com/panel/");
            },
            error:function () {
                $(".appTerminateButton").prop('disabled', false);
                swal("Failed!", "Failed to terminate app. Please contact Administrator.", "error");
            },
        });}
        else{
            alertInfo('Incorrect input format! Please try again. ')
        }
    });


    $(document).on('click','#savePythonConfigurationButton', function(e) {
        const csrftoken = getCookie('csrftoken');
        let script = $("#appMainSelect").val()
        let version = $("#pythonVersionSelectPref").val()
        if((script!==null)&&(version!==null))
        {
            $.ajax({
                url: `/app/config/`,
                headers: {'X-CSRFToken': csrftoken},
                type: 'PUT',
                data: {script: script, version: version, stack: "python"},
                success: function (data) {
                    $("#appStopButton").prop('disabled', false);
                    $("#appStartButton").prop('disabled', false);
                    $('#pythonAppConfigurationModal').modal('hide');
                    $("#unsetConfigNotifier").hide()
                    swal("Success!", "App configuration set successfully", "success");
                },
                error: function () {
                    swal("Failed!", "Failed to set configuration. Contact admin", "error");
                },
            });
        }
        else {
            swal("Uh huh!", "Some configurations seems missing", "info");
        }
    });


    $(document).on('click','#saveNodeConfigurationButton', function(e) {
        const csrftoken = getCookie('csrftoken');
        let script = $("#appStartSelect").val()
        let version = $("#nodeVersionSelectPref").val()
        if((script!==null)&&(version!==null))
        {
            $.ajax({
                url: `/app/config/`,
                headers: {'X-CSRFToken': csrftoken},
                type: 'PUT',
                data: {script: script, version: version, stack: "node"},
                success: function (data) {
                    $("#appStopButton").prop('disabled', false);
                    $("#appStartButton").prop('disabled', false);
                    $('#nodeAppConfigurationModal').modal('hide');
                    $("#unsetConfigNotifier").hide()
                    swal("Success!", "App configuration set successfully", "success");
                },
                error: function () {
                    swal("Failed!", "Failed to set configuration. Contact admin", "error");
                },
            });
        }
        else {
            swal("Uh huh!", "Some configurations seems missing", "info");
        }
    });

    $(document).on('keyup', "#coinInput", function (e){
        let coin_count = $("#coinInput").val()
        if (!isNaN(coin_count)) {
            if (coin_count>10&&coin_count<1001){
                let amount = 0.12 * coin_count;
             $("#coinSpan").html(`${coin_count}c = $${amount.toFixed(2)}`);
            }
            else{
            $("#coinSpan").html("10c = $1.2");
        }
        }
        else {
            $("#coinSpan").html("10c = $1.2");
        }
    });


});


$(document).ready(function() {

    $(document).on('click','#transactionButton', function(e) {
        e.preventDefault();
        $("#transactionButton").prop('disabled', true);
        let account_no = $('input[name="account_id"]').val();
        let account_no_conf = $('input[name="account_id_conf"]').val();
        let amount = $('input[name="transaction_amount"]').val();
        let msg = document.getElementById("formGroupExampleInput4").value;
        const csrftoken = getCookie('csrftoken');

        if (account_no!==""){
            if (account_no===account_no_conf){
                if (!isNaN(account_no)){
                $.ajax({
                    url: `/transactions/`,
                    headers: {'X-CSRFToken': csrftoken},
                    type: 'POST',
                    data: {account_no: account_no, amount: amount, msg: msg},
                    success:function (data)
                    {
                      $('#transactionModalCenter').modal('toggle');
                      $('#transactionRefreshSection').html(data);
                      $("#transactionButton").prop('disabled', false);
                    },
                    error: function (response) {
                        $("#transactionButton").prop('disabled', false);
                        switch (response.status) {
                            case 404:
                                alertInfo("User not found");
                                break;
                            case 403:
                                alertWarning("Please enter an amount greater than or equal to $1");
                                break;
                            case 405:
                                alertWarning("Method not allowed");
                                break;
                            case 501:
                                alertWarning("You need to recharge your account at least once before" +
                                    " transferring credits");
                                break;
                            case 503:
                                alertWarning("You don't have enough credits to process this transaction");
                                break;
                            default:
                                alertDanger("Something went wrong.");
                        }
                    },
                });
                }
                else{
                    alertWarning("Enter a valid account no")
                }

            }else{
                alertWarning("Account id doesn't match");
            }
        }
    });

    $(document).on('click','#transactionAuthorizationButton', function(e) {
        let transaction_id = $('input[name="transaction_id"]').val();
        let otp = $('input[name="transaction_otp"]').val();
        $("#transactionAuthorizationButton").prop('disabled', true);
        const csrftoken = getCookie('csrftoken');
        $.ajax({
            url: `/transactions/`,
            headers: {'X-CSRFToken': csrftoken},
            type: 'PUT',
            data: {transaction_id: transaction_id, otp: otp},
            success:function (data)
            {
              $("#transactionAuthorizationButton").prop('disabled', false);
              $('#transactionModalCenter').modal('toggle');
              $('#pendingTransactionRefresh').html(data)
                alertSuccess("Transaction is successful!")
            },
            error: function (response) {
                $("#transactionAuthorizationButton").prop('disabled', false);
                switch (response.status) {
                    case 400:
                        alertWarning("OTP does not match, Transaction failed.");
                        $('#transactionModalCenter').modal('toggle');
                        break;
                    case 503:
                        alertWarning("You don't have enough credits to process this transaction");
                        $('#transactionModalCenter').modal('toggle');
                        break;
                    default:
                        alertDanger("Something went wrong.");
                }
            },
        });
    });

    $(document).on('click','#cancelTransactionButton', function(e) {
        let transaction_id =  $('input[name="cancel_transaction"]').val();
        const csrftoken = getCookie('csrftoken');
        $.ajax({
            url: `/transactions/`+ '?' + $.param({"transaction_id": transaction_id}),
            headers: {'X-CSRFToken': csrftoken},
            type: 'DELETE',
            success:function (data)
            {
              $('#cancelTransactionModalCenter').modal('toggle');
              $('#pendingTransactionRefresh').html(data)
                alertSuccess("Transaction canceled successfully!")
            },
            error: function (response) {
                switch (response.status) {
                    default:
                        alertDanger("Something went wrong.");
                }
            },
        });
    });

    $(document).on('click','#resendOtpButton', function(e) {
        let transaction_id = $('input[name="transaction_id"]').val();
        $("#resendOtpButton").prop('disabled', true);
        const csrftoken = getCookie('csrftoken');
        $.ajax({
            url: `/transactions/utility/`,
            headers: {'X-CSRFToken': csrftoken},
            type: 'POST',
            data: {transaction_id: transaction_id},
            success:function (data)
            {
              alertSuccess("New OTP has been sent!")
            },
            error: function (response) {
                switch (response.status) {
                    case 503:
                        alertWarning("Please wait at least 2 minutes before requesting another OTP");
                        break;
                    default:
                        alertDanger("Something went wrong.");
                }
            },
        });

    });

    $(document).on('click','#transactionTriggerButton', function(e) {

        let transaction_id = $('input[name="transaction_id"]').val();
        $("#resendOtpButton").prop('disabled', true);
        const csrftoken = getCookie('csrftoken');
        $.ajax({
            url: `/transactions/utility/`,
            headers: {'X-CSRFToken': csrftoken},
            type: 'PUT',
            data: {transaction_id: transaction_id},
            success:function (data)
            {
              $("#transactionRefreshSection").html(data);
            },
            error: function (response) {
                switch (response.status) {
                    default:
                        alertDanger("Something went wrong.");
                }
            },
        });
    });

    $(document).on('click','#promocodeButton', function(e) {

        let promo_code = $('input[name="promo_code"]').val();
        if(promo_code!==""){
            $("#promocodeButton").prop('disabled', true);
            const csrftoken = getCookie('csrftoken');
            $.ajax({
                url: `/promocode/`,
                headers: {'X-CSRFToken': csrftoken},
                type: 'POST',
                data: {promo_code: promo_code},
                success:function (data)
                {
                  $("#statsRefreshSection").html(data);
                  alertSuccess("Promocode successfully applied!")
                },
                error:function (resp) {
                    switch (resp.status) {
                        case 403:
                            alertWarning("This promocode/offer has expired");
                            break;
                        case 404:
                            alertWarning("Promocode not found");
                            break;
                        case 503:
                            alertWarning("You have already claimed this offer");
                            break;
                        default:
                            alertDanger("Something went wrong.");
                    }
                },
            });
            $("#promocodeButton").prop('disabled', false);
        }

    });


    $(document).on('click','#exchangeCoinBtn', function(e) {
        let coins = $('input[name="coinInput"]').val();
        if(coins>=10){
            $("#exchangeCoinBtn").prop('disabled', true);
            const csrftoken = getCookie('csrftoken');
            $.ajax({
                url: `/exchange/`,
                headers: {'X-CSRFToken': csrftoken},
                type: 'POST',
                data: {coins: coins},
                success:function (data)
                {
                  $("#statsRefreshSection").html(data);
                  alertSuccess("Coins successfully exchanged!")
                },
                error:function (resp) {
                    switch (resp.status) {
                        case 503:
                            alertWarning("You don't have enough coins to exchange!!!");
                            break;
                        default:
                            alertDanger("Something went wrong.");
                    }
                },
            });
            $("#exchangeCoinBtn").prop('disabled', false);
        }
        else {
            alertWarning("The value should be 10 or higher");
        }

    });

    $(document).on('click','#exchangeAffiliateCreditsBtn', function(e) {
        let credits = $('input[name="convertCreditsField"]').val();
        if(credits>=1){
            $("#exchangeAffiliateCreditsBtn").prop('disabled', true);
            const csrftoken = getCookie('csrftoken');

            $.ajax({
                url: `/exchange/affiliate/`,
                headers: {'X-CSRFToken': csrftoken},
                type: 'POST',
                data: {credits: credits},
                success:function (data)
                {
                    $("#affiliateCommissionBox").text(`\$${data["balance"]}`)
                  alertSuccess("Credits successfully exchanged!")
                },
                error:function (resp) {
                    switch (resp.status) {
                        case 503:
                            alertWarning("You don't have enough credits to exchange!");
                            break;
                        default:
                            alertDanger("Something went wrong. please contact support");
                    }
                },
            });
            $('#affiliateConvertCreditsModal').modal('hide');
            $("#exchangeAffiliateCreditsBtn").prop('disabled', false);
        }
        else {
            alertWarning("Minimum amount to exchange is $1");
        }

    });

});


$(document).ready(function (){
    $(document).on('click', '.copyTransactionID', function (){
        let transaction_id = $(this).attr("transaction_id");
         var $temp = $("<input>");
         $("body").append($temp);
         $temp.val(transaction_id).select();
         document.execCommand("copy");
         $temp.remove()
         alertSuccess("Copied to clipboard!")
    })
    $(document).on('click', '#hiddenRefreshButton', function (){
        $('#hiddenRefreshButton').fadeOut();
        $('#logAutoUpdate').prop("checked", true);
    })
})

