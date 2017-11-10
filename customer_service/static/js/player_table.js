/**
 * Created by wangxb on 17/11/6.
 */

$(function () {
    $("#_player-table").on('draw.dt', function() {
        $("a[action=delete_player]").click(function () {
            var tr = $(this).closest('tr');
            var row = $("#_player-table").DataTable().row(tr);
            var row_data = row.data();
            var really_delete = $(this).attr('delete') == "1";
            var url = $(this).attr('url');

            if (row_data.loginame != "" && row_data.loginname != "" && row_data.loginname != null) {
                var _confirm = confirm("玩家［" +row_data.account + "］已被客服" + row_data.loginname + "绑定！请确认是否删除？");
                if (_confirm == false) {
                    return false;
                }
                delete_player(tr, url, row_data.id, really_delete);
            } else {
                var modal = $("#_player_delete_modal");
                modal.find('.modal-title').text('删除确认');
                var delete_tip = '请确认是否删除［' + row_data.account + '］';
                if (really_delete)
                    delete_tip += '<b>删除后将无法恢复！</b>';

                modal.find('.modal-body').html(delete_tip);
                modal.find('#_game_del_modal_submit').on('click', function (e) {
                    modal.modal('hide');
                    delete_player(tr, url, row_data.id, really_delete);
                    modal.find('#_game_del_modal_submit').off('click');
                });
                modal.modal('show');
            }
            return false;
        });

        $("a[action=contact_player]").click(function () {
            var tr = $(this).closest('tr');
            var row_data = $("#_player-table").DataTable().row(tr).data();

            var url = $(this).attr('url');
            location.href = url + '?player=' + row_data.id;

            return false;
        });

        $("a[action=edit_player]").click(function () {
            var tr = $(this).closest('tr');
            var row_data = $("#_player-table").DataTable().row(tr).data();

            var url = $(this).attr('url');

            location.href = url + '/' + row_data.id + '/';
            return false;
        });

        $("a[action=recycle_player]").click(function () {
            var tr = $(this).closest('tr');
            var row = $("#_player-table").DataTable().row(tr);
            var row_data = row.data();
            var url = $(this).attr('url');

            var modal = $("#_player_delete_modal");
            modal.find('.modal-title').text('恢复确认');
            modal.find('.modal-body').text('请确认是否恢复玩家［' + row_data.account + '］');
            modal.find('#_game_del_modal_submit').on('click', function (e) {
                modal.modal('hide');
                recycle_player(tr, url, row_data.id);
                modal.find('#_game_del_modal_submit').off('click');
            });
            modal.modal('show');
            return false;
        })
    })
});

function recycle_player(tr, url, player_id) {
    $.post(url, {id: player_id}, function (data, status) {
        if (status == "success") {
            if (data.code == 0) {
                $("#_player-table").DataTable()
                    .row(tr)
                    .remove()
                    .draw(false);
            }
            alert(data.message);
        } else {
            alert("玩家恢复失败，内部错误！");
        }
    })
}

function delete_player(tr, url, player_id, really_delete) {
    $.post(url, {id: player_id, force: true, really: really_delete}, function (data, status) {
        var row_data = $("#_player-table").DataTable().row(tr).data();
        var message = "玩家 [" + row_data.account +"] 删除成功！";
        if (status == "success") {
            if (data.code == 0) {
                $("#_player-table").DataTable()
                    .row(tr)
                    .remove()
                    .draw(false);
            } else {
                message = "玩家 [" + row_data.account +"] 删除失败！";
            }
        } else {
            message = "玩家 [" + row_data.account +"] 删除失败！内部错误！"
        }
        alert(message);
    })
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
        id_arr[ind] = data.id
    });

    var id_str = id_arr.join();

    $.post(url, {'id': id_str}, function(data, status) {
        if (status == "success") {
            if (data.code == 0) {
                table
                    .rows({ search: 'applied', selected: true})
                    .remove()
                    .draw(false);
            }
            alert(data.message);
        } else
            alert("恢复失败，内部错误！");
    });
}

function delete_selected(table_id, url, really) {
    var table = $("#" + table_id).DataTable();
    if (table.rows({search: 'applied', selected: true})[0].length == 0) {
        alert("请先选择要删除的玩家！");
        return true;
    }
    var rows_selected = table.rows({ search: 'applied', selected: true}).data();

    var id_arr = [];
    var account_arr = [];
    var has_locked_player = [];
    $.each(rows_selected, function(ind, data) {
        id_arr[ind] = data.id;
        account_arr.push(data.account);
        if (data.loginname != null && data.loginname != "--" && data.loginname != "") {
            has_locked_player.push(data.account);
        }
    });

    if (has_locked_player.length > 0) {
        var delete_tip = "玩家［" + has_locked_player.join() + "］已被客服绑定！请确认是否删除？";
        if (really)
            delete_tip += "<br><b>删除后将无法恢复！！！</b>";
        var _confirm = confirm(delete_tip);
        if (_confirm == false) {
            return false;
        }
        _delete_selected(table_id, url, id_arr, account_arr, really);
    } else {
        var modal = $("#_player_delete_modal");
        modal.find('.modal-title').text('删除确认');
        var delete_tip = "请确认是否删除所选玩家？";
        if (really)
            delete_tip += "<br><b>删除后将无法恢复！！！</b>";
        modal.find('.modal-body').html(delete_tip);
        modal.find('#_game_del_modal_submit').on('click', function (e) {
            modal.modal('hide');
            _delete_selected(table_id, url, id_arr, account_arr, really);
            modal.find('#_game_del_modal_submit').off('click');
        });
        modal.modal('show');
    }
}

function _delete_selected(table_id, url, id_arr, account_arr, really) {
    var table = $("#" + table_id).DataTable();

    var id_str = id_arr.join();

    $.post(url, {'id': id_str, 'really': really}, function(data, status) {
        if (status == "success") {
            var message = "玩家 [" + account_arr.join() + "] 删除成功！";
            if (data.code == 0) {
                $("#_player-table").DataTable()
                    .rows({search: 'applied', selected: true})
                    .remove()
                    .draw(false);
            } else {
                message = "玩家 [" + account_arr.join() + "] 删除失败！";
            }
        } else {
            message = "玩家 [" + account_arr.join() + "] 删除失败！内部错误！"
        }
        alert(message);
    })
}