/**
 * Created by wangxb on 17/9/25.
 */

function delete_role(url, role_id, role_name) {
    var modal = $("#_role_delete_modal");
    modal.find('.modal-title').text('删除确认');
    modal.find('.modal-body').text('请确认是否删除［' + role_name + '］');
    modal.find('#_role_del_modal_submit').on('click', function (e) {
        modal.modal('hide');
        delete_role_submit(url, role_id);
    });
    modal.modal('show');
}

function delete_role_submit(url, role_id) {
    $.post(url, {id: role_id}, function (data, status) {
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