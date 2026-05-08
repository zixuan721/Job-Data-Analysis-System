/** 
 * 数据可视化模块 - datavis.js
 * 用于渲染各种数据可视化图表
 */
layui.define(['jquery', 'echarts'], function(exports) {
    var $ = layui.jquery,
        echarts = layui.echarts;
    
    // 存储所有图表实例
    var chartInstances = {};
    
    // 颜色配置
    var colors = [
        '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', 
        '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#1e90ff',
        '#ff7f50', '#32cd32', '#6a5acd', '#ff69b4', '#ba55d3'
    ];
    
    // 初始化图表
    function initChart(id) {
        // 如果已经初始化过，则销毁重新创建
        if (chartInstances[id]) {
            chartInstances[id].dispose();
        }
        
        // 创建新的图表实例
        var dom = document.getElementById(id);
        if (!dom) {
            console.error('找不到DOM元素：' + id);
            return null;
        }
        
        var chart = echarts.init(dom);
        chartInstances[id] = chart;
        return chart;
    }
    
    // 渲染薪资分布饼图
    function renderSalaryPie(data) {
        var chart = initChart('salary-chart');
        if (!chart) return;
        
        var option = {
            title: {
                text: '薪资分布',
                left: 'center'
            },
            tooltip: {
                trigger: 'item',
                formatter: '{a} <br/>{b}: {c} ({d}%)'
            },
            legend: {
                orient: 'vertical',
                left: 'left',
                data: data.map(function(item) { return item.name; })
            },
            series: [
                {
                    name: '薪资分布',
                    type: 'pie',
                    radius: ['40%', '70%'], // 环形图
                    avoidLabelOverlap: false,
                    itemStyle: {
                        borderRadius: 10,
                        borderColor: '#fff',
                        borderWidth: 2
                    },
                    label: {
                        show: true,
                        formatter: '{b}: {c} ({d}%)'
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: '16',
                            fontWeight: 'bold'
                        }
                    },
                    labelLine: {
                        show: true
                    },
                    data: data
                }
            ]
        };
        
        chart.setOption(option);
    }
    
    // 渲染学历分布饼图
    function renderEduPie(data) {
        var chart = initChart('edu-chart');
        if (!chart) return;
        
        var option = {
            title: {
                text: '学历要求分布',
                left: 'center'
            },
            tooltip: {
                trigger: 'item',
                formatter: '{a} <br/>{b}: {c} ({d}%)'
            },
            legend: {
                orient: 'vertical',
                left: 'left',
                data: data.map(function(item) { return item.name; })
            },
            series: [
                {
                    name: '学历要求',
                    type: 'pie',
                    radius: '70%',
                    center: ['50%', '50%'],
                    data: data,
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }
            ]
        };
        
        chart.setOption(option);
    }
    
    // 渲染职位关键词柱状图
    function renderKeywordBar(data) {
        var chart = initChart('keyword-chart');
        if (!chart) return;
        
        var option = {
            title: {
                text: '职位关键词分布',
                left: 'center'
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '10%',
                top: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: data.x,
                axisLabel: {
                    interval: 0,
                    rotate: 30,
                    textStyle: {
                        fontSize: 12
                    }
                }
            },
            yAxis: {
                type: 'value',
                name: '职位数量'
            },
            series: [
                {
                    name: '职位数量',
                    type: 'bar',
                    barWidth: '60%',
                    data: data.y,
                    itemStyle: {
                        normal: {
                            color: function(params) {
                                return colors[params.dataIndex % colors.length];
                            },
                            label: {
                                show: true,
                                position: 'top',
                                textStyle: {
                                    color: 'black',
                                    fontSize: 12,
                                    fontWeight: 'bold'
                                }
                            }
                        }
                    }
                }
            ]
        };
        
        chart.setOption(option);
    }
    
    // 渲染城市分布柱状图
    function renderCityBar(data) {
        var chart = initChart('city-chart');
        if (!chart) return;
        
        var option = {
            title: {
                text: '城市分布',
                left: 'center'
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '10%',
                top: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: data.x,
                axisLabel: {
                    interval: 0,
                    textStyle: {
                        fontSize: 12
                    }
                }
            },
            yAxis: {
                type: 'value',
                name: '职位数量'
            },
            series: [
                {
                    name: '职位数量',
                    type: 'bar',
                    barWidth: '60%',
                    data: data.y,
                    itemStyle: {
                        normal: {
                            color: function(params) {
                                return colors[params.dataIndex % colors.length];
                            },
                            label: {
                                show: true,
                                position: 'top',
                                textStyle: {
                                    color: 'black',
                                    fontSize: 12,
                                    fontWeight: 'bold'
                                }
                            }
                        }
                    }
                }
            ]
        };
        
        chart.setOption(option);
    }
    
    // 渲染薪资与学历关系散点图
    function renderSalaryEduScatter(eduData, salaryData) {
        var chart = initChart('salary-edu-chart');
        if (!chart) return;
        
        // 生成散点图数据
        var scatterData = [];
        var eduValues = {
            '博士': 5,
            '硕士': 4,
            '本科': 3,
            '大专': 2,
            '不限': 1
        };
        
        // 为每个学历生成一组数据点
        for (var edu in eduValues) {
            var eduValue = eduValues[edu];
            var series = {
                name: edu,
                type: 'scatter',
                data: []
            };
            
            // 为每个薪资范围生成数据点
            for (var i = 0; i < salaryData.length; i++) {
                var salaryItem = salaryData[i];
                var eduItem = eduData.find(function(item) { return item.name === edu; });
                
                // 只有当该学历有数据时才添加点
                if (eduItem && eduItem.value > 0) {
                    // 提取薪资范围的中间值
                    var salaryValue;
                    if (salaryItem.name === '5K及以下') {
                        salaryValue = 5;
                    } else if (salaryItem.name === '50K以上') {
                        salaryValue = 55;
                    } else {
                        // 解析类似 "5-10K" 的格式
                        var range = salaryItem.name.replace('K', '').split('-');
                        salaryValue = (parseFloat(range[0]) + parseFloat(range[1])) / 2;
                    }
                    
                    // 添加数据点 [薪资, 学历等级, 数量]
                    series.data.push([
                        salaryValue,
                        eduValue,
                        salaryItem.value > 0 ? Math.min(40, salaryItem.value / 10) : 5 // 气泡大小
                    ]);
                }
            }
            
            if (series.data.length > 0) {
                scatterData.push(series);
            }
        }
        
        var option = {
            title: {
                text: '薪资与学历关系分析',
                left: 'center'
            },
            legend: {
                data: Object.keys(eduValues),
                left: 'right'
            },
            tooltip: {
                trigger: 'item',
                formatter: function(params) {
                    var edu = params.seriesName;
                    var salary = params.value[0] + 'K';
                    return '学历: ' + edu + '<br>薪资: ' + salary + '<br>数量: ' + params.value[2];
                }
            },
            xAxis: {
                type: 'value',
                name: '薪资（K）',
                nameLocation: 'middle',
                nameGap: 30,
                min: 0,
                max: 60
            },
            yAxis: {
                type: 'value',
                name: '学历要求',
                nameLocation: 'middle',
                nameGap: 30,
                min: 0,
                max: 6,
                axisLabel: {
                    formatter: function(value) {
                        var labels = ['', '不限', '大专', '本科', '硕士', '博士'];
                        return labels[value] || '';
                    }
                }
            },
            series: scatterData
        };
        
        chart.setOption(option);
    }
    
    // 渲染职位技能词云图
    function renderWordCloud(keywordData) {
        var chart = initChart('wordcloud-chart');
        if (!chart) return;
        
        // 准备词云数据
        var data = [];
        for (var i = 0; i < keywordData.x.length; i++) {
            data.push({
                name: keywordData.x[i],
                value: keywordData.y[i]
            });
        }
        
        var option = {
            title: {
                text: '职位技能词云',
                left: 'center'
            },
            tooltip: {
                show: true
            },
            series: [{
                type: 'wordCloud',
                shape: 'circle',
                left: 'center',
                top: 'center',
                width: '80%',
                height: '80%',
                right: null,
                bottom: null,
                sizeRange: [12, 60],
                rotationRange: [-90, 90],
                rotationStep: 45,
                gridSize: 8,
                drawOutOfBound: false,
                textStyle: {
                    fontFamily: 'sans-serif',
                    fontWeight: 'bold',
                    color: function() {
                        return 'rgb(' + [
                            Math.round(Math.random() * 160),
                            Math.round(Math.random() * 160),
                            Math.round(Math.random() * 160)
                        ].join(',') + ')';
                    }
                },
                emphasis: {
                    textStyle: {
                        shadowBlur: 10,
                        shadowColor: '#333'
                    }
                },
                data: data
            }]
        };
        
        chart.setOption(option);
    }
    
    // 渲染薪资趋势折线图
    function renderSalaryTrend(salaryData) {
        var chart = initChart('salary-trend-chart');
        if (!chart) return;
        
        // 薪资范围名称和对应的平均值
        var categories = [];
        var values = [];
        
        // 提取薪资范围名称和数量
        for (var i = 0; i < salaryData.length; i++) {
            categories.push(salaryData[i].name);
            values.push(salaryData[i].value);
        }
        
        var option = {
            title: {
                text: '薪资分布趋势',
                left: 'center'
            },
            tooltip: {
                trigger: 'axis'
            },
            legend: {
                data: ['职位数量'],
                left: 'right'
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: categories
            },
            yAxis: {
                type: 'value',
                name: '职位数量'
            },
            series: [
                {
                    name: '职位数量',
                    type: 'line',
                    stack: '总量',
                    areaStyle: {},
                    emphasis: {
                        focus: 'series'
                    },
                    data: values,
                    smooth: true,
                    markPoint: {
                        data: [
                            {type: 'max', name: '最大值'},
                            {type: 'min', name: '最小值'}
                        ]
                    },
                    markLine: {
                        data: [
                            {type: 'average', name: '平均值'}
                        ]
                    }
                }
            ]
        };
        
        chart.setOption(option);
    }
    
    // 渲染所有图表
    function renderCharts(data) {
        // 确保数据存在
        if (!data) return;
        
        // 渲染薪资分布饼图
        if (data.salary_data && data.salary_data.length > 0) {
            renderSalaryPie(data.salary_data);
        }
        
        // 渲染学历分布饼图
        if (data.edu_data && data.edu_data.length > 0) {
            renderEduPie(data.edu_data);
        }
        
        // 渲染职位关键词柱状图
        if (data.keyword_data && data.keyword_data.x && data.keyword_data.x.length > 0) {
            renderKeywordBar(data.keyword_data);
        }
        
        // 渲染城市分布柱状图
        if (data.city_data && data.city_data.x && data.city_data.x.length > 0) {
            renderCityBar(data.city_data);
        }
        
        // 渲染薪资与学历关系散点图
        if (data.edu_data && data.edu_data.length > 0 && data.salary_data && data.salary_data.length > 0) {
            renderSalaryEduScatter(data.edu_data, data.salary_data);
        }
        
        // 渲染职位技能词云图
        if (data.keyword_data && data.keyword_data.x && data.keyword_data.x.length > 0) {
            renderWordCloud(data.keyword_data);
        }
        
        // 渲染薪资趋势折线图
        if (data.salary_data && data.salary_data.length > 0) {
            renderSalaryTrend(data.salary_data);
        }
    }
    
    // 重新调整所有图表大小
    function resizeCharts() {
        for (var id in chartInstances) {
            if (chartInstances.hasOwnProperty(id)) {
                chartInstances[id].resize();
            }
        }
    }
    
    // 导出模块接口
    var datavis = {
        renderCharts: renderCharts,
        resize: resizeCharts
    };
    
    exports('datavis', datavis);
}); 