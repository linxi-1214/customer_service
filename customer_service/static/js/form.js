/**
 * Created by wangxb on 17/10/30.
 */

$(function () {
    // 在页面初始化的时候，将form的原始内容保存好。
    window.origin_form_data = $("form").serializeArray();
    
    window.is_form_modified = function isFormModified() {
        var modified_form_data = $("form").serializeArray();

        var has_changed = JSON.stringify(modified_form_data) != JSON.stringify(origin_form_data);
        if (has_changed)
            $("input[name=form_changed]").attr({value: 1});

        return has_changed
    }
});