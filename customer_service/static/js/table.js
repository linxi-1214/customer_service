/**
 * Created by wangxb on 17/10/26.
 */

function select_all(reverse, table_id) {
    var table = $("#" + table_id).DataTable();
    if (reverse) {
        var rows_selected = table.rows({search: 'applied', selected: true})
    }
    table.rows({search: 'applied'}).select();

    if (reverse) {
        rows_selected.deselect();
    }
}

function recycle_selected(table_id, url) {
    if ($("#" + table_id).DataTable().rows({search: 'applied', selected: true})[0].length == 0) {
        alert("请先选择要恢复的玩家！");
        return true;
    }

    var modal = $("#_player_delete_modal");
    modal.find('.modal-title').text('恢复确认');
    modal.find('.modal-body').text('请确认是否恢复所选玩家？');
    modal.find('#_game_del_modal_submit').on('click', function (e) {
        modal.modal('hide');
        _recycle_selected(table_id, url);
        modal.find('#_game_del_modal_submit').off('click');
    });
    modal.modal('show');
}

function _recycle_selected(table_id, url) {
    var table = $("#" + table_id).DataTable();
    var rows_selected = table.rows({search: 'applied', selected: true}).data();
    var id_arr = [];

    $.each(rows_selected, function(ind, data) {
        id_arr[ind] = data[1]
    });

    var id_str = id_arr.join();

    $.post(url, {'id': id_str}, function(data, status) {
        if (status == "success") {
            if (data.code == 0) {
                table
                    .rows({ search: 'applied', selected: true})
                    .remove()
                    .draw();
            }
            alert(data.message);
        } else
            alert("恢复失败，内部错误！");
    });
}

function delete_selected(table_id, url, really) {
    if ($("#" + table_id).DataTable().rows({search: 'applied', selected: true})[0].length == 0) {
        alert("请先选择要删除的玩家！");
        return true;
    }
    var modal = $("#_player_delete_modal");
    modal.find('.modal-title').text('删除确认');
    var delete_tip = "请确认是否删除所选玩家？";
    if (really)
        delete_tip += "<b>删除后将无法恢复！！！</b>";
    modal.find('.modal-body').html(delete_tip);
    modal.find('#_game_del_modal_submit').on('click', function (e) {
        modal.modal('hide');
        _delete_selected(table_id, url, really);
        modal.find('#_game_del_modal_submit').off('click');
    });
    modal.modal('show');
}

function _delete_selected(table_id, url, really) {
    var table = $("#" + table_id).DataTable();

    var rows_selected = table.rows({ search: 'applied', selected: true}).data();

    var id_arr = [];
    $.each(rows_selected, function(ind, data) {
        id_arr[ind] = data[1];
    });

    var id_str = id_arr.join();

    $.post(url, {'id': id_str, 'really': really}, function(data, status) {
        if (status == "success") {
            if (data.need_verify) {
                var _confirm = confirm(data.message);
                if (_confirm == true) {
                    $.post(url, {'id': id_str, 'force': true, 'really': really}, function (data, status) {
                        if (status == "success") {
                            if (data.code == 0) {
                                table
                                    .rows({ search: 'applied', selected: true})
                                    .remove()
                                    .draw();
                            }
                            alert(data.message);
                        } else {
                            alert("删除失败，服务器内部错误！");
                        }
                    })
                }
            } else {
                if (data.code == 0) {
                    // delete successfully
                    table
                        .rows({ search: 'applied', selected: true})
                        .remove()
                        .draw();

                }
                alert(data.message);
            }
        } else {
            alert("删除失败，服务器内部错误！");
        }
    })
}