/**
 * Created by wangxb on 17/10/16.
 */

function draw_report(url) {
    $.post(url, $("form").serialize(), function (data, status) {
        if (status == "success") {
            $.jqplot("_customer-service-chart", data.line_data, {
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
                        render: $.jqplot.DateAxisRenderer,
                        label: '玩家联系数',
                        pad: 1.01,
                        tickOptions: {
                            showGridline: false
                        }
                    },
                    yaxis: {
                        label: '时间范围',
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

            })
        } else {

        }
    });
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
    time_str += '-' + start_date.getDate() + ' ~ ';
    time_str += end_date.getFullYear() + '-';
    time_str += end_date.getMonth()+1 > 9 ? (end_date.getMonth()+1) : '0' + (end_date.getMonth()+1);
    time_str += '-' + end_date.getDate();

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
});
