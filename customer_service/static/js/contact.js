/**
 * Created by wangxb on 17/10/30.
 */

function save(url, callback) {
    var top_alert_div = $("div.top-alert");
    var top_content = $("#top-alert-content");
    var tmp_alert_class = "alert top-alert alert-dismissible show col-md-6 col-lg-offset-3";
    var top_alert_class;
    if (is_form_modified()) {
        var form_data = $("form").serialize();
        $.post(url, form_data, function(data, status) {
            if (status == "success") {
                if (data.code == 0) {
                    top_alert_class = tmp_alert_class + ' alert-success';
                    if ($("input[name=form_changed]").length > 0)
                        $("input[name=form_changed]").attr({value: 0});
                    window.origin_form_data = $("form").serializeArray();
                } else {
                    top_alert_class = tmp_alert_class + ' alert-danger';
                }
                top_alert_div.attr({'class': top_alert_class});
                top_content.html(data.message);
            } else {
                top_alert_class += ' alert-danger';
                top_alert_div.attr({'class': top_alert_class});
                top_content.html('服务器内部错误！');
            }

            top_alert_div.css({top: '-' + (top_alert_div.height() + 24) + 'px'});

            if ( status == 'success' && data.code == 0 && callback != undefined) {
                $("div.top-alert").animate({top: '0'}, 'slow', callback);
            } else
                $("div.top-alert").animate({top: '0'}, 'slow');

        }, 'json');
    } else {
        top_alert_class = tmp_alert_class + ' alert-success';
        top_alert_div.attr({'class': top_alert_class});
        top_content.html('保存成功 ！');
        top_alert_div.css({top: '-' + (top_alert_div.height() + 24) + 'px'});
        $("div.top-alert").animate({top: '0'}, 'slow');

        if (callback != undefined) {
            callback();
        }
    }
}

function save_and_next(url, next_url) {
    save(url, function() {
        location.href = next_url;
    });
}

$(function () {

});