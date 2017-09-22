/**
 * Created by wangxb on 17/9/22.
 */
function delete_game(url, game_id, game_name) {
    var modal = $("#_game_delete_modal");
    modal.find('.modal-title').text('删除确认');
    modal.find('.modal-body').text('请确认是否删除［' + game_name + '］');
    modal.find('#_game_del_modal_submit').on('click', function (e) {
        modal.modal('hide');
        delete_game_submit(url, game_id);
    });
    modal.modal('show');
}

function delete_game_submit(url, game_id) {
    $.post(url, {id: game_id}, function (data, status) {
        if (status == "success") {
            // $("#_game_del_modal_submit").modal('hide');
            alert("删除成功！")
        }
    })
}
$(function () {

});