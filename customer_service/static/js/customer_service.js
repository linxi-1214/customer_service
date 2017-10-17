/**
 * Created by wangxb on 17/10/16.
 */
var plot1;
var report_table;

function draw_chart(data) {
    plot1 = $.jqplot("_customer-service-chart", data.line_data, {
        seriesColors: [
            "#9ACD32", "#D02090",
            "#EE82EE", "#40E0D0",
            "#FF6347", "#008080",
            "#4682B4", "#6A5ACD",
            "#87CEEB", "#2E8B57",
            "#4169E1", "#6B8E23"
        ], // 默认显示的分类颜色，如果分类的数量超过这里的颜色数量，则从该队列中第一个位置开始重新取值赋给相应的分类
        title: {
            text: '客服工作报告曲线图', //设置当前图的标题
            show: true,//设置当前图的标题是否显示
        },
        legend: {
            show: true,
            placement: 'outsideGrid',
            location: 'ne',
            rowSpacing: '0px',
            labels: data.labels,
        },
        axes: {
            xaxis: {
                renderer: $.jqplot.DateAxisRenderer,
                rendererOptions:{
                    tickRenderer:$.jqplot.CanvasAxisTickRenderer
                },
                label: '时间',
                pad: 1.01,
                tickOptions:{
                    fontSize:'10pt',
                    fontFamily:'Tahoma',
                    angle:40,
                    formatString: '%Y-%#m-%#d',
                    showGridline: false
                }
            },
            yaxis: {
                label: '玩家联系数',
                padMin: 0,
                padMax: 1.05,
                tickOptions: {
                    angle: -30
                }
            }
        },
        grid: {
            drawBorder: false,
            shadow: false,
            background: "white"
        }

    });
}

function draw_table(data) {
    var columns = new Array();
    $.each(data.titles, function (ind, val) {
        columns.push({title: val})
    });
    if ( report_table != undefined ) {
        report_table
            .rows()
            .remove()
            .draw();

        report_table
            .rows.add(data.values)
            .draw();
    } else {
        report_table = $('#_contact-data-table')
            .on('init.dt', function () {
                $("label > select").select2({
                    placeholder: {
                        id: 0,
                        text: '-- 请选择 --'
                    },
                    allowClear: false,
                    containerCssClass: 'table-select'
                });
            })
            .DataTable({
                data: data.values,
                columns: columns,
                lengthMenu: [[10, 15, 20, 25, 30, 40, 50, -1], [10, 15, 20, 25, 30, 40, 50, "All"]],
                autoWidth: false,
                paging: true,
                fixedColumns: {
                    heightMatch: 'auto',
                    leftColumns: 2,
                    rightColumns: 1
                },
                language: {
                    emptyTable: "暂无数据",
                    info: "当前显示<b>_START_</b>至<b>_END_</b>项  共 <b>_TOTAL_</b> 项",
                    lengthMenu: "每页显示 _MENU_ 项",
                    loadingRecords: "正在加载...",
                    search: "搜索:",
                    zeroRecords: "无匹配项",
                    paginate: {
                        "next": "下一页",
                        "previous": "上一页"
                    }
                }
            });
    }
}

function draw_report(url) {
    $("#_customer-service-chart").html('');
    plot1 = undefined;
    $.jqplot.config.enablePlugins = true;
    $.post(url, $("form").serialize(), function (data, status) {
        if (status == "success") {
            draw_chart(data);
            draw_table(data.table_data);
        } else {

        }
    }, "json");
}

function getLastDay(d){
     var current=new Date(d);
     var currentMonth=current.getMonth();
     var nextMonth=++currentMonth;
     var nextMonthDayOne =new Date(current.getFullYear(),nextMonth,1);
     var minusDate=1000*60*60*24;
     return new Date(nextMonthDayOne.getTime()-minusDate);
}

function getCurrentMonthLastDay(){
     var current=new Date();
     var currentMonth=current.getMonth();
     var nextMonth=++currentMonth;
     var nextMonthDayOne =new Date(current.getFullYear(),nextMonth,1);
     var minusDate=1000*60*60*24;
     return new Date(nextMonthDayOne.getTime()-minusDate);
}

function getDaysAgo(days){
     var current=new Date();
     var minusDate=1000*60*60*24;
     return new Date(current.getTime()-(minusDate * days));
}

function getMonthsAgo(current_date, months) {
    var current_month = current_date.getMonth();
    var current_year = current_date.getFullYear();

    var prev_month = current_month - months;
    var prev_year = current_year;
    if (prev_month <= 0) {
        prev_month = 12 + prev_month;
        prev_year = current_year - 1;
    }

    return new Date(prev_year, prev_month, 1);
}

function generate_date(time_str) {
    var current_date = new Date();
    var start_date = current_date;
    var end_date = current_date;
    if (time_str == "week") {
        start_date = getDaysAgo(7);
    } else if (time_str == "one month") {
        start_date = getMonthsAgo(current_date, 0);
        end_date = getCurrentMonthLastDay();
    } else if (time_str == "three month") {
        start_date = getMonthsAgo(current_date, 2);
        end_date = getCurrentMonthLastDay();
    }

    var time_str = start_date.getFullYear() + '-';
    time_str += start_date.getMonth()+1 > 9 ? (start_date.getMonth()+1) : '0' + (start_date.getMonth()+1);
    time_str += '-' + (start_date.getDate()>9 ? start_date.getDate() : '0' + start_date.getDate()) + ' ~ ';
    time_str += end_date.getFullYear() + '-';
    time_str += end_date.getMonth()+1 > 9 ? (end_date.getMonth()+1) : '0' + (end_date.getMonth()+1);
    time_str += '-' + (end_date.getDate()>9 ? end_date.getDate(): '0'+end_date.getDate());

    $("#_time-range").val(time_str);

}

$(function () {
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

    $("#_series_form").find("input[type=checkbox]").on('change', function () {
        if ( plot1 === undefined )
            return;
        var series_index = parseInt( $(this).val() );
        if ( this.checked === true )
            plot1.series[series_index].show = true;
        else
            plot1.series[series_index].show = false;

        plot1.replot();
    });

    new pickerDateRange('_time-range', {
        isTodayValid : true,
        //startDate : '2013-04-14',
        //endDate : '2038-04-21',
        //needCompare : true,
        //isSingleDay : true,
        //shortOpr : true,
        stopToday: false,
        defaultText : ' ~ ',
        inputTrigger : 'input_trigger_demo3'
    });
});
