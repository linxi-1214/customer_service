/**
 * Created by wangxb on 17/9/28.
 */

$(function () {
    var csrf_token = $.cookie('csrftoken');

    $("#input-id").fileinput({
        browseLabel: '浏览',
        removeLabel: '删除',
        uploadLabel: '导入',
        showPreview: true,

        msgSelected: '已选择 {n} 个文件',
        msgPlaceholder: '请选择导入文件',
        msgUploadEnd: '导入完成',
        allowedFileExtensions: ['xls', 'xlsx'],


        uploadExtraData: {'csrfmiddlewaretoken': csrf_token}
    });
});
