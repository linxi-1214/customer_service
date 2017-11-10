/**
 * Created by wangxb on 17/11/5.
 */

$(function () {
    var alert_length = 0;
    function flush_alert() {
        $.get("/customer-service/alert/all/", function (alerts, status) {
            if (status == "success") {
                if (alerts.length > 0) {
                    if (alert_length == 0) {
                        $("a[kind=bell]").prepend('<span class="badge" style="color: #fff; background-color: #d9534f">' + alerts.length + '</span>');
                    } else if (alerts.length != alert_length)
                        $("a[kind=bell]>span[class=badge]").html(alerts.length);
                } else {
                    $("a[kind=bell]>span.badge").remove();
                }
                alert_length = alerts.length;
                var origin_alert_ids = new Array();
                var new_alert_ids = new Array();
                $("li.my-alert").each(function () {
                    origin_alert_ids.push(parseInt( $(this).attr('alert_id') ));
                });
                $.each(alerts, function (ind, single_alert) {
                    if ( $.inArray(single_alert.id, origin_alert_ids) == -1) {
                        var li_html = '<li class="my-alert" alert_id="' + single_alert.id + '">' +
                            '<a kind="alert" href="#" url="' + single_alert.href + '" alert_id="' + single_alert.id + '">' +
                            '<div>' +
                            '<i class="fa fa-comment fa-fw"></i> ' + single_alert.content +
                            '<span class="pull-right text-muted small">' + single_alert.time + '</span>' +
                            '</div>' +
                            '</a>' +
                            '</li>';
                        $("ul.dropdown-alerts").prepend(li_html);
                    }
                    new_alert_ids.push(single_alert.id);
                });

                $.each(origin_alert_ids, function(ind, alert_id) {
                    if ($.inArray( alert_id, new_alert_ids) == -1) {
                        $("li.my-alert[alert_id=" + alert_id + "]").remove();
                    }
                });

                $("a[kind=alert]").click(function () {
                    var url = $(this).attr('url');
                    var alert_id = $(this).attr('alert_id');

                    var update_alert_url = "/customer-service/alert/has-seen/" + alert_id + "/";

                    $.get(update_alert_url);

                    location.href = url;
                });
            }
        }, 'json')
    }
    flush_alert();
    // setInterval(flush_alert, 2000);
});