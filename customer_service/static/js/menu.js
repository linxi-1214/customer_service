/**
 * Created by wangxb on 17/9/24.
 */

function delete_menu(url, menu_id, menu_label) {
    var modal = $("#_menu_delete_modal");
    modal.find('.modal-title').text('删除确认');
    modal.find('.modal-body').text('请确认是否删除［' + menu_label + '］');
    modal.find('#_game_del_modal_submit').on('click', function (e) {
        modal.modal('hide');
        delete_menu_submit(url, menu_id);
    });
    modal.modal('show');
}

function delete_menu_submit(url, menu_id) {
    $.post(url, {id: menu_id}, function (data, status) {
        if (status == "success") {
            // $("#_game_del_modal_submit").modal('hide');
            alert("删除成功！")
        }
    })
}
$(function () {
    $("select[kind=form-select]").select2({
        placeholder: {
            id: 0,
            text: '-- 请选择 --'
        },
        allowClear: true
    });
});