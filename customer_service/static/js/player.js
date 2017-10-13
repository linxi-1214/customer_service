/**
 * Created by wangxb on 17/9/26.
 */
var game_div_html;
var game_div_index = 0;
var game_count;

function delete_player(url, player_id, player_label) {
    var modal = $("#_player_delete_modal");
    modal.find('.modal-title').text('删除确认');
    modal.find('.modal-body').text('请确认是否删除［' + player_label + '］');
    modal.find('#_game_del_modal_submit').on('click', function (e) {
        modal.modal('hide');
        delete_player_submit(url, player_id);
    });
    modal.modal('show');
}

function delete_player_submit(url, player_id) {
    $.post(url, {id: player_id}, function (data, status) {
        if (status == "success") {
            // $("#_game_del_modal_submit").modal('hide');
            alert("删除成功！")
        }
    })
}

/* 当登记玩家信息的时候，添加注册游戏 */
function add_register_game() {
    if ($("div.register-game-none").length == 0)
        $("#add_game_button_id").before(game_div_html);
    else
        $("div.register-game-none:last").after(game_div_html);

    $("div.register-game-none:last>div:first>span").remove();
    $("div.register-game-none:last>div:first>select>option").remove("[selected]");
    var select_obj = $("div.register-game-none:last>div:first>select");
    var time_obj = $("div.register-game-none:last>div:eq(1)>input[type=text]");

    select_obj.removeClass("select2-hidden-accessible");
    var select_origin_name = select_obj.attr("name");
    var text_origin_name = time_obj.attr("name");
    select_obj.attr({name: select_origin_name + game_div_index});
    time_obj.attr({name: text_origin_name + game_div_index});
    game_div_index += 1;
    select_obj.select2({
        placeholder: {
            id: 0,
            text: '-- 请选择 --'
        },
        allowClear: true,
        containerCss: {height: '34px'}
    });

    select_obj.on('select2:select', function (e) {
        var option_value = e.params.data.id;
        var option = $($(select_obj).children('[value="' + option_value + '"]'));
        option.attr({selected: "selected"});
    });

    if ($("div.register-game-none").length == game_count) {
        $("#add_game_button_id").attr({disabled: "disabled"});
    }
}

/* 删除玩家的登记游戏 */
function delete_register_game(btn) {
    $(btn).closest("div.register-game-none").remove();
    $("div.tooltip").remove();
    $("#add_game_button_id").removeAttr("disabled");
}

$(function () {
    game_div_html = $("div.register-game-none:last").prop('outerHTML');
    game_count = $("#_game_id").children().length - 1;

    if (game_count == $("div.register-game-none").length)
        $("#add_game_button_id").attr({disabled: "disabled"});

    try {
        $("select[kind=form-select]").select2({
            placeholder: {
                id: 0,
                text: '-- 请选择 --'
            },
            allowClear: true,
            containerCss: {height: '34px'}
        });
        $("select[kind=form-select]").on('select2:select', function (e) {
            var option_value = e.params.data.id;
            var select_obj = e.target;
            var option = $($(select_obj).children('[value="' + option_value + '"]'));
            option.attr({selected: "selected"});
        });
    } catch (e) {
        console.log(e.message)
    }
    $(".form-group").tooltip({
        selector: "[data-toggle=tooltip]",
        container: "body"
    });
});