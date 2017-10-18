/**
 * Created by wangxb on 17/9/26.
 */
var game_div_html;
var game_div_index = 0;
var game_count;
var table;

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

function player_query() {
    var account = $("#_account").val();
    var game = $("#_game_name option:selected").text();
    var mobile = $("#_mobile").val();

    $('#_player-table').DataTable().column( 1 ).search(
        account, true, true
    ).draw();
    $('#_player-table').DataTable().column( 5).search(
        game, true, true
    ).draw();
    $('#_player-table').DataTable().column( 3 ).search(
        mobile, true, true
    ).draw();

    $('#_player-table').DataTable().draw();
    return false;
}

function import_player_query() {
    var filename = $("#_filename").val();

    $("#_player-import-table").DataTable().column(2).search(
        filename, true, true
    ).draw();

    $('#_player-import-table').DataTable().draw();
}

function import_result_detail(url) {
    $.getJSON(url, function(data, status) {
        if (status == 'success') {
            var modal = $("#_import-result-modal");
            var _html = "";
            if (data.length == 0) {
                _html = '<div class="alert alert-success">';
                _html += '<h4><i class="fa fa-check-circle"></i> 全部导入成功！</h4>';
                _html += '</div>';
            } else {
                _html = '<table class="table">';
                _html += '<thead><tr><th>账号</th><th>导入失败原因</th></tr></thead>';
                _html += '<tbody>';
                $.each(data, function (ind, result_obj) {
                    _html += '<tr><td>' + result_obj.account + '</td><td>' + result_obj.error + '</td></tr>';
                });
                _html += '</tbody></table>';
            }
            modal.find('.modal-body').html(_html);
            modal.modal('show');
        }
    });
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

    if ( $("#_charge_money_min").length > 0 )
        $.fn.dataTable.ext.search.push(
            function( settings, data, dataIndex ) {
                var min = parseInt( $('#_charge_money_min').val(), 10 );
                var max = parseInt( $('#_charge_money_max').val(), 10 );
                var money = parseFloat( data[12] ) || 0; // use data for the age column

                if ( ( isNaN( min ) && isNaN( max ) ) ||
                     ( isNaN( min ) && money <= max ) ||
                     ( min <= money   && isNaN( max ) ) ||
                     ( min <= money   && money <= max ) )
                {
                    return true;
                }
                return false;
            }
        );

    if ($("#_import-time-input").length > 0)
        $.fn.dataTable.ext.search.push(
            function( settings, data, dataIndex ) {
                var time_range = $('#_import-time-input').val();
                if (time_range == "")
                    return true;
                else
                    time_range = time_range.split(' ~ ');
                var regEx = new RegExp("\\-","gi");
                var start_time = time_range[0].replace(regEx, "/");
                var end_time = time_range[1].replace(regEx, "/");

                start_time = new Date(start_time);
                end_time = new Date(end_time);

                var import_time = data[3].replace(regEx, "/"); // use data for the age column

                import_time = new Date(import_time);

                if (isNaN(import_time))
                    return true;

                if (start_time <= import_time && import_time <= end_time ) {
                    return true;
                }
                return false;
            }
        );


    $(".form-group").tooltip({
        selector: "[data-toggle=tooltip]",
        container: "body"
    });

    try {
        new pickerDateRange('_time-range', {
            isTodayValid : true,
            stopToday: false,
            defaultText : ' ~ ',
            inputTrigger : 'input_trigger_demo3'
        });
    } catch (e) {
        console.log(e.message)
    }
    var time_range = $("#_time-range");
    if (time_range.length > 0)
        time_range.val(time_range.attr("value"));
});