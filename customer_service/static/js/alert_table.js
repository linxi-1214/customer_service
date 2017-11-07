/**
 * Created by wangxb on 17/11/5.
 */

function marked_alert_selected(url) {
    var table = $("#_alert-table").DataTable();

    var rows_selected = table.rows({ search: 'applied', selected: true});
    var row_ids = table.rows({ search: 'applied', selected: true}).ids(true);

    var id_arr = [];
    $.each(rows_selected.data(), function(ind, data) {
        id_arr[ind] = data.id;
    });

    var id_str = id_arr.join();

    $.post(url, {'id': id_str}, function(data, status) {
        if (status == "success") {
            $.each(row_ids, function (ind, id) {
                var tmp_data = table.row(id).data();
                tmp_data.marked = true;
                table.row(id).data(tmp_data).draw();
            })
        } else {
            alert("删除失败，服务器内部错误！");
        }
    })
}