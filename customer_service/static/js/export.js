/**
 * Created by wangxb on 17/10/15.
 */

$(function () {
    var modal = $("#_export_modal");
    modal.find('#_export_player_submit').on('click', function (e) {
        var fname = modal.find('#_file-name').val();
        if (fname == "")
            fname = 'player';
        var time_suffix = modal.find('#_time').attr('checked') == "checked";
        modal.modal('hide');
        _export_player(fname, time_suffix);
        modal.find('#_file-name').val('');
    });
});

function export_player() {
    var modal = $("#_export_modal");
    modal.find('.modal-title').text('输入导出文件名');
    modal.modal('show');
}


function s2ab(s) {
	if(typeof ArrayBuffer !== 'undefined') {
		var buf = new ArrayBuffer(s.length);
		var view = new Uint8Array(buf);
		for (var i=0; i!=s.length; ++i) view[i] = s.charCodeAt(i) & 0xFF;
		return buf;
	} else {
		var buf = new Array(s.length);
		for (var i=0; i!=s.length; ++i) buf[i] = s.charCodeAt(i) & 0xFF;
		return buf;
	}
}

function export_data_to_excel(table_data, type, fn) {
    var wb = XLSX.utils.book_new(), ws = XLSX.utils.aoa_to_sheet(table_data);
    XLSX.utils.book_append_sheet(wb, ws, "玩家信息");
    var wbout = XLSX.write(wb, {bookType: type, bookSST: true, type: 'binary'});
    var fname = (fn || 'test.') + type;
    try {
	    saveAs(new Blob([s2ab(wbout)],{type:"application/octet-stream"}), fname);
    } catch(e) {
        if(typeof console != 'undefined') console.log(e, wbout);
    }
    return wbout;
}

function _export_player(fname, time_suffix) {
    var arr = new Array();
    for (var i=1; i<=16; i++)
        arr[i-1] = i
    var table_data = $("#_player-table").DataTable().buttons.exportData({
        'columns': arr
    });

    var excel_data = [];

    excel_data.push(table_data.header);
    $.each(table_data.body, function(ind, row_data) {
        excel_data.push(row_data)
    });

    if (time_suffix) {
        var curr_date = new Date();
        fname += '_' + curr_date.getFullYear() + curr_date.getMonth() + curr_date.getDay() + curr_date.getHours() + curr_date.getMinutes() + curr_date.getSeconds();
        fname += '.'
    }

    return export_data_to_excel(excel_data, 'xlsx', fname);
}

function export_table_to_excel(id, type, fn) {
    var wb = XLSX.utils.table_to_book(document.getElementById(id), {sheet:"玩家信息"});
    var wb = XLSX.utils
    var wbout = XLSX.write(wb, {bookType:type, type: 'binary'});
    var fname = fn || 'test.' + type;
    try {
	    saveAs(new Blob([s2ab(wbout)],{type:"application/octet-stream"}), fname);
    } catch(e) {
        if(typeof console != 'undefined') console.log(e, wbout);
    }
    return wbout;
}

function doit(type, fn) {
    return export_table_to_excel('table', type || 'xlsx', fn);
}
