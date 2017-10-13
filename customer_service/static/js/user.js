/**
 * Created by wangxb on 17/9/25.
 */


function delete_user(url, user_id, user_label) {
    var modal = $("#_user_delete_modal");
    modal.find('.modal-title').text('删除确认');
    modal.find('.modal-body').text('请确认是否删除［' + user_label + '］');
    modal.find('#_game_del_modal_submit').on('click', function (e) {
        modal.modal('hide');
        delete_user_submit(url, user_id);
    });
    modal.modal('show');
}

function delete_user_submit(url, user_id) {
    $.post(url, {id: user_id}, function (data, status) {
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
        allowClear: true,
        containerCss: {'height': '34px'}
    });
});