/**
 * Created by wangxb on 17/10/8.
 */


function delete_result(url, result_id, result_label) {
    var modal = $("#_result_delete_modal");
    modal.find('.modal-title').text('删除确认');
    modal.find('.modal-body').text('请确认是否删除［' + result_label + '］');
    modal.find('#_game_del_modal_submit').on('click', function (e) {
        modal.modal('hide');
        delete_result_submit(url, result_id);
    });
    modal.modal('show');
}

function delete_result_submit(url, result_id) {
    $.post(url, {id: result_id}, function (data, status) {
        if (status == "success") {
            // $("#_game_del_modal_submit").modal('hide');
            alert("删除成功！");
            window.location.reload();
        } else {
            alert("删除失败！");
        }
    })
}