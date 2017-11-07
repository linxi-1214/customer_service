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

function select_current_all(reverse, table_id) {
    var table = $("#" + table_id).DataTable();
    if (reverse) {
        var rows_selected = table.rows({search: 'applied', page: 'current', selected: true})
    }
    table.rows({search: 'applied', page: 'current'}).select();

    if (reverse) {
        rows_selected.deselect();
    }
}