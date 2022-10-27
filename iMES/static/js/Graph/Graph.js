function newDateHour(h, m, s) {
    var now = new Date();
    var day = now.getDate();
    var month = now.getMonth();
    var year = now.getFullYear();
    var time = new Date(year, month, day, h, m, s, 0);
    return time;
};

function shiftTime() {
    if (new Date() >= newDateHour(7, 0, 0) && new Date() <= newDateHour(19, 0, 0)) {
        return [newDateHour(7, 0, 0), newDateHour(19, 0, 0)];
    } else if (new Date() >= newDateHour(19, 0, 0)) {
        return [newDateHour(19, 0, 0), newDateHour(31, 0, 0)];
    } else if (new Date() <= newDateHour(7, 0, 0)) {
        return [newDateHour(-5, 0, 0), newDateHour(7, 0, 0)];
    }
}

function loadJson(selector) {
    return JSON.parse(document.querySelector(selector).getAttribute('data-json'));
}


function graph(td, pn) {
    if (td == '' && pn == '') {

    }
    else {
        trend = td
        plan = pn
        let chart = document.getElementById("myChart");
        if (typeof (chart) != 'undefined' && chart != null) {
            var ctx = chart.getContext('2d'),
                count = 100,
                max = 25
            if (max !== '0' && max !== 'null') {
                var stepsize = +max / count;
                var maxscale = +max;
            } else {
                var stepsize = false;
                var maxscale = 1000;
            }

            if (typeof Chart !== 'undefined') {
                myChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        datasets: [{
                            data: trend,
                            backgroundColor: 'rgba(117, 211, 130, 0.2)',
                            borderColor: 'rgba(117, 211, 130, 1)',
                            tension: 0,
                            fill: false,
                            borderWidth: 3,
                            label: 'Факт'
                        },
                        {
                            data: plan,
                            borderColor: 'rgba(54, 162, 235, 1)',
                            tension: 0,
                            fill: false,
                            borderWidth: 1,
                            label: 'План'
                        }]
                    },
                    options:
                    {
                        spanGaps: true, // для пустой точки
                        animation: false,
                        hover: {
                            mode: null
                        },
                        elements: {
                            point: {
                                radius: 0
                            }
                        },
                        scales: {
                            x: {
                                type: 'time',
                                time: {
                                    unit: 'hour',
                                    min: plan[0].x,
                                    max: plan[1].x,
                                    displayFormats: {
                                        hour: 'HH:mm'
                                    }
                                }
                            },
                            y: {
                                ticks: {
                                    beginAtZero: true,
                                    min: 0,
                                    max: plan.length + 1,
                                    stepSize: ((plan.length + 1) / 12),
                                    callback: function (value) { return Math.floor(value) }
                                }
                            }
                        },
                        tooltip: {
                            enabled: false
                        },
                        title: {
                            display: false
                        },
                        plugins: {
                            legend: {
                                display: false
                            }
                        }
                    }
                });
            }
        }
        return myChart
    }
}

function UpdateGraph()
{
    setInterval(
        () => {
            socket.emit('getTrendPlanData','')
        },
        60000
    );
}

chr = ''

socket.emit('getTrendPlanData','')
socket.on('receiveTrendPlanData',function (data)
{
    arr = JSON.parse(data)
    if (address == Object.keys(arr))
    {
        TrendPlan = arr[address]
        if (chr == '')
        {
            chr = graph(TrendPlan['trend'], TrendPlan['plan'])
        }
        else
        {
            chr.destroy()
            chr = graph(TrendPlan['trend'], TrendPlan['plan'])
        }
    }
})

UpdateGraph()