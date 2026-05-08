$(function () {
    // 定义全局颜色方案
    var mainColors = ['#8dff19', '#00d887', '#d81072', '#ff0c13'];
    
    // 辅助函数：调整颜色亮度
    function adjustBrightness(color, factor) {
        // 如果是十六进制颜色
        if (color.startsWith('#')) {
            var r = parseInt(color.substr(1, 2), 16);
            var g = parseInt(color.substr(3, 2), 16);
            var b = parseInt(color.substr(5, 2), 16);
            
            r = Math.floor(r * factor);
            g = Math.floor(g * factor);
            b = Math.floor(b * factor);
            
            r = Math.min(255, Math.max(0, r));
            g = Math.min(255, Math.max(0, g));
            b = Math.min(255, Math.max(0, b));
            
            return 'rgb(' + r + ',' + g + ',' + b + ')';
        }
        // 如果是rgb颜色
        else if (color.startsWith('rgb')) {
            var parts = color.match(/\d+/g);
            if (parts && parts.length >= 3) {
                var r = parseInt(parts[0]);
                var g = parseInt(parts[1]);
                var b = parseInt(parts[2]);
                
                r = Math.floor(r * factor);
                g = Math.floor(g * factor);
                b = Math.floor(b * factor);
                
                r = Math.min(255, Math.max(0, r));
                g = Math.min(255, Math.max(0, g));
                b = Math.min(255, Math.max(0, b));
                
                return 'rgb(' + r + ',' + g + ',' + b + ')';
            }
        }
        return color; // 如果无法解析，返回原始颜色
    }
    
    echarts_1();
    echarts_2();
    echarts_4();
    echarts_31();
    echarts_6();
    map_1();

    function echarts_1() {
        // 基于准备好的dom，初始化echarts实例
        var myChart = echarts.init(document.getElementById('echart1'));

        option = {
            title: {
                text: '城市职位数量分布',
                left: 'center',
                top: 0,
                textStyle: {
                    color: '#fff',
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow',
                    lineStyle: {
                        color: '#dddc6b'
                    }
                },
                formatter: '{b}: {c}个职位',
                backgroundColor: 'rgba(50,50,50,0.7)',
                borderColor: '#ccc',
                borderWidth: 1,
                textStyle: {
                    color: '#fff'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '10%',
                top: '25%',
                containLabel: true
            },
            xAxis: [{
                type: 'category',
                data: my.var_1,
                axisLine: {
                    show: true,
                    lineStyle: {
                        color: "rgba(255,255,255,.3)",
                        width: 2
                    },
                },
                axisTick: {
                    show: false,
                },
                axisLabel: {
                    interval: 0,
                    rotate: 30,
                    show: true,
                    splitNumber: 15,
                    textStyle: {
                        color: "rgba(255,255,255,.8)",
                        fontSize: 12,
                        fontWeight: 'bold'
                    },
                },
            }],
            yAxis: [{
                type: 'value',
                name: '职位数量',
                nameTextStyle: {
                    color: 'rgba(255,255,255,.8)',
                    fontSize: 12,
                    padding: [0, 0, 0, 5]
                },
                axisLabel: {
                    show: true,
                    textStyle: {
                        color: "rgba(255,255,255,.8)",
                        fontSize: 12
                    },
                },
                axisTick: {
                    show: false,
                },
                axisLine: {
                    show: true,
                    lineStyle: {
                        color: "rgba(255,255,255,.3)",
                        width: 2
                    },
                },
                splitLine: {
                    lineStyle: {
                        color: "rgba(255,255,255,.1)",
                        type: "dashed"
                    }
                }
            }],
            series: [
                {
                    name: '职位数量',
                    type: 'bar',
                    data: my1.var_2,
                    barWidth: '50%', //柱子宽度
                    itemStyle: {
                        normal: {
                            // 使用与echarts_6相似的颜色方案
                            color: function(params) {
                                // 基本颜色
                                var baseColor = mainColors[params.dataIndex % mainColors.length];
                                
                                // 创建渐变
                                return new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                                    offset: 0,
                                    color: baseColor // 起始颜色
                                }, {
                                    offset: 1,
                                    color: adjustBrightness(baseColor, 0.7) // 结束颜色，稍微调暗
                                }]);
                            },
                            barBorderRadius: [5, 5, 0, 0],
                            shadowColor: 'rgba(0, 0, 0, 0.3)',
                            shadowBlur: 10,
                            label: {
                                show: true,
                                position: 'top',
                                formatter: '{c}',
                                textStyle: {
                                    color: 'rgba(255,255,255,.9)',
                                    fontSize: 12,
                                    fontWeight: 'bold'
                                }
                            }
                        },
                        emphasis: {
                            barBorderRadius: [8, 8, 0, 0],
                            shadowBlur: 20,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    },
                    // 添加动画效果
                    animationDelay: function (idx) {
                        return idx * 100;
                    },
                    animationDuration: 1000,
                    animationEasing: 'elasticOut'
                }
            ]
        };

        // 使用刚指定的配置项和数据显示图表。
        myChart.setOption(option);
        window.addEventListener("resize", function () {
            myChart.resize();
        });
    }


    function echarts_2() {
        // 基于准备好的dom，初始化echarts实例
        var myChart = echarts.init(document.getElementById('echart2'));

        option = {
            title: {
                text: '各岗位平均薪资对比',
                left: 'center',
                top: 0,
                textStyle: {
                    color: '#fff',
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow',
                    lineStyle: {
                        color: '#dddc6b'
                    }
                },
                formatter: '{b}: {c}K',
                backgroundColor: 'rgba(50,50,50,0.7)',
                borderColor: '#ccc',
                borderWidth: 1,
                textStyle: {
                    color: '#fff'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '10%',
                top: '25%',
                containLabel: true
            },
            xAxis: [{
                type: 'category',
                data: job_prices.job_price_index,
                axisLine: {
                    show: true,
                    lineStyle: {
                        color: "rgba(255,255,255,.3)",
                        width: 2
                    },
                },
                axisTick: {
                    show: false,
                },
                axisLabel: {
                    interval: 0,
                    rotate: 30,
                    show: true,
                    splitNumber: 15,
                    textStyle: {
                        color: "rgba(255,255,255,.8)",
                        fontSize: 12,
                        fontWeight: 'bold'
                    },
                },
            }],
            yAxis: [{
                type: 'value',
                name: '平均薪资(K)',
                nameTextStyle: {
                    color: 'rgba(255,255,255,.8)',
                    fontSize: 12,
                    padding: [0, 0, 0, 5]
                },
                axisLabel: {
                    formatter: '{value}K',
                    show: true,
                    textStyle: {
                        color: "rgba(255,255,255,.8)",
                        fontSize: 12
                    },
                },
                axisTick: {
                    show: false,
                },
                axisLine: {
                    show: true,
                    lineStyle: {
                        color: "rgba(255,255,255,.3)",
                        width: 2
                    },
                },
                splitLine: {
                    lineStyle: {
                        color: "rgba(255,255,255,.1)",
                        type: "dashed"
                    }
                }
            }],
            series: [
                {
                    name: '平均薪资',
                    type: 'bar',
                    data: job_prices.job_price,
                    barWidth: '50%', //柱子宽度
                    itemStyle: {
                        normal: {
                            // 使用与echarts_6相似的颜色方案
                            color: function(params) {
                                // 基本颜色
                                var baseColor = mainColors[params.dataIndex % mainColors.length];
                                
                                // 创建渐变
                                return new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                                    offset: 0,
                                    color: baseColor // 起始颜色
                                }, {
                                    offset: 1,
                                    color: adjustBrightness(baseColor, 0.7) // 结束颜色，稍微调暗
                                }]);
                            },
                            barBorderRadius: [5, 5, 0, 0],
                            shadowColor: 'rgba(0, 0, 0, 0.3)',
                            shadowBlur: 10,
                            label: {
                                show: true,
                                position: 'top',
                                formatter: '{c}K',
                                textStyle: {
                                    color: 'rgba(255,255,255,.9)',
                                    fontSize: 12,
                                    fontWeight: 'bold'
                                }
                            }
                        },
                        emphasis: {
                            barBorderRadius: [8, 8, 0, 0],
                            shadowBlur: 20,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    },
                    // 添加动画效果
                    animationDelay: function (idx) {
                        return idx * 100;
                    },
                    animationDuration: 1000,
                    animationEasing: 'elasticOut'
                }
            ]
        };

        // 使用刚指定的配置项和数据显示图表。
        myChart.setOption(option);
        window.addEventListener("resize", function () {
            myChart.resize();
        });
    }


    function echarts_4() {
        // 基于准备好的dom，初始化echarts实例
        var myChart = echarts.init(document.getElementById('echart4'));

        option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    lineStyle: {
                        color: '#dddc6b'
                    }
                },
                formatter: function(params) {
                    // 构建显示所有系列数据的提示框
                    var result = params[0].name + '<br/>';
                    // 遍历所有系列
                    params.forEach(function(param) {
                        // 添加每个系列的名称和数值
                        var color = param.color;
                        var seriesName = param.seriesName;
                        var value = param.value;
                        result += '<span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:' + color + '"></span>';
                        result += seriesName + ': ' + value + 'K<br/>';
                    });
                    return result;
                }
            },
            legend: {
                top: '0%',
                data: ['Java', 'Python', 'Web', '算法'],
                textStyle: {
                    color: 'rgba(255,255,255,.5)',
                    fontSize: '12',
                }
            },
            grid: {
                left: '10',
                top: '30',
                right: '10',
                bottom: '10',
                containLabel: true
            },

            xAxis: [{
                type: 'category',
                boundaryGap: false,
                axisLabel: {
                    textStyle: {
                        color: "rgba(255,255,255,.6)",
                        fontSize: 12,
                    },
                },
                axisLine: {
                    lineStyle: {
                        color: 'rgba(255,255,255,.2)'
                    }
                },
                data: my.var_1.slice(0, 10)
            }, {
                axisPointer: {show: false},
                axisLine: {show: false},
                position: 'bottom',
                offset: 20,
            }],

            yAxis: [{
                type: 'value',
                axisTick: {show: false},
                axisLine: {
                    lineStyle: {
                        color: 'rgba(255,255,255,.1)'
                    }
                },
                axisLabel: {
                    textStyle: {
                        color: "rgba(255,255,255,.6)",
                        fontSize: 12,
                    },
                    formatter: '{value}K'
                },
                splitLine: {
                    lineStyle: {
                        color: 'rgba(255,255,255,.1)'
                    }
                }
            }],
            series: [
                {
                    name: 'Java',
                    type: 'line',
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 5,
                    showSymbol: false,
                    lineStyle: {
                        normal: {
                            color: '#8dff19',
                            width: 2
                        }
                    },
                    areaStyle: {
                        normal: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                                offset: 0,
                                color: 'rgba(1, 132, 213, 0.4)'
                            }, {
                                offset: 0.8,
                                color: 'rgba(1, 132, 213, 0.1)'
                            }], false),
                            shadowColor: 'rgba(0, 0, 0, 0.1)',
                        }
                    },
                    itemStyle: {
                        normal: {
                            color: '#8dff19',
                            borderColor: 'rgba(221, 220, 107, .1)',
                            borderWidth: 12
                        }
                    },
                    data: job_prices.java_cities_price,
                },
                {
                    name: 'Python',
                    type: 'line',
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 5,
                    showSymbol: false,
                    lineStyle: {
                        normal: {
                            color: '#00d887',
                            width: 2
                        }
                    },
                    areaStyle: {
                        normal: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                                offset: 0,
                                color: 'rgba(0, 216, 135, 0.4)'
                            }, {
                                offset: 0.8,
                                color: 'rgba(0, 216, 135, 0.1)'
                            }], false),
                            shadowColor: 'rgba(0, 0, 0, 0.1)',
                        }
                    },
                    itemStyle: {
                        normal: {
                            color: '#00d887',
                            borderColor: 'rgba(221, 220, 107, .1)',
                            borderWidth: 12
                        }
                    },
                    data: job_prices.python_cities_price,
                },
                {
                    name: 'Web',
                    type: 'line',
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 5,
                    showSymbol: false,
                    lineStyle: {
                        normal: {
                            color: '#d81072',
                            width: 2
                        }
                    },
                    areaStyle: {
                        normal: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                                offset: 0,
                                color: 'rgba(0, 216, 135, 0.4)'
                            }, {
                                offset: 0.8,
                                color: 'rgba(0, 216, 135, 0.1)'
                            }], false),
                            shadowColor: 'rgba(0, 0, 0, 0.1)',
                        }
                    },
                    itemStyle: {
                        normal: {
                            color: '#d81072',
                            borderColor: 'rgba(221, 220, 107, .1)',
                            borderWidth: 12
                        }
                    },
                    data: job_prices.web_cities_price,
                },
                {
                    name: '算法',
                    type: 'line',
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 5,
                    showSymbol: false,
                    lineStyle: {
                        normal: {
                            color: '#ff0c13',
                            width: 2
                        }
                    },
                    areaStyle: {
                        normal: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                                offset: 0,
                                color: 'rgba(1, 132, 213, 0.4)'
                            }, {
                                offset: 0.8,
                                color: 'rgba(1, 132, 213, 0.1)'
                            }], false),
                            shadowColor: 'rgba(0, 0, 0, 0.1)',
                        }
                    },
                    itemStyle: {
                        normal: {
                            color: '#ff0c13',
                            borderColor: 'rgba(221, 220, 107, .1)',
                            borderWidth: 12
                        }
                    },
                    data: job_prices.hadoop_cities_price,
                },
            ]
        };

        // 使用刚指定的配置项和数据显示图表。
        myChart.setOption(option);
        window.addEventListener("resize", function () {
            myChart.resize();
        });
    }


    function echarts_6() {
        // 基于准备好的dom，初始化echarts实例
        var myChart = echarts.init(document.getElementById('echart6'));

        // 提取job_titles中的数据
        var jobNames = [];
        var jobValues = [];
        
        console.log("job_titles数据:", job_titles);
        
        // 确保job_titles是数组且有数据
        if (Array.isArray(job_titles) && job_titles.length > 0) {
            // 提取名称和值
            for (var i = 0; i < job_titles.length; i++) {
                jobNames.push(job_titles[i].name);
                jobValues.push(job_titles[i].value);
            }
            console.log("解析后的岗位名称:", jobNames);
            console.log("解析后的岗位数量:", jobValues);
        } else {
            console.error("job_titles数据格式不正确或为空");
        }
        
        option = {
            title: {
                left: 'center',
                top: 0,
                textStyle: {
                    color: '#fff',
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow',
                    lineStyle: {
                        color: '#dddc6b'
                    }
                },
                formatter: '{b}: {c}个职位',
                backgroundColor: 'rgba(50,50,50,0.7)',
                borderColor: '#ccc',
                borderWidth: 1,
                textStyle: {
                    color: '#fff'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '10%',
                top: '25%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: jobNames,
                axisLabel: {
                    interval: 0,
                    rotate: 30,
                    textStyle: {
                        color: "rgba(255,255,255,.8)",
                        fontSize: 12,
                        fontWeight: 'bold'
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: 'rgba(255,255,255,.3)',
                        width: 2
                    }
                },
                axisTick: {
                    show: false
                }
            },
            yAxis: {
                type: 'value',
                name: '职位数量',
                nameTextStyle: {
                    color: 'rgba(255,255,255,.8)',
                    fontSize: 12,
                    padding: [0, 0, 0, 5]
                },
                axisLabel: {
                    textStyle: {
                        color: "rgba(255,255,255,.8)",
                        fontSize: 12
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: 'rgba(255,255,255,.3)',
                        width: 2
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: 'rgba(255,255,255,.1)',
                        type: 'dashed'
                    }
                }
            },
            series: [
                {
                    name: '职位数量',
                    type: 'bar',
                    barWidth: '50%',
                    data: jobValues,
                    itemStyle: {
                        normal: {
                            // 使用与echarts_4相似的颜色方案
                            color: function(params) {
                                // 基本颜色
                                var baseColor = mainColors[params.dataIndex % mainColors.length];
                                
                                // 创建渐变
                                return new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                                    offset: 0,
                                    color: baseColor // 起始颜色
                                }, {
                                    offset: 1,
                                    color: adjustBrightness(baseColor, 0.7) // 结束颜色，稍微调暗
                                }]);
                            },
                            barBorderRadius: [5, 5, 0, 0],
                            shadowColor: 'rgba(0, 0, 0, 0.3)',
                            shadowBlur: 10,
                            label: {
                                show: true,
                                position: 'top',
                                formatter: '{c}',
                                textStyle: {
                                    color: 'rgba(255,255,255,.9)',
                                    fontSize: 12,
                                    fontWeight: 'bold'
                                }
                            }
                        },
                        emphasis: {
                            barBorderRadius: [8, 8, 0, 0],
                            shadowBlur: 20,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    },
                    // 添加动画效果
                    animationDelay: function (idx) {
                        return idx * 100;
                    },
                    animationDuration: 1000,
                    animationEasing: 'elasticOut'
                }
            ]
        };

        // 使用刚指定的配置项和数据显示图表。
        myChart.setOption(option);
        window.addEventListener("resize", function () {
            myChart.resize();
        });
    }


    function echarts_31() {
        // 基于准备好的dom，初始化echarts实例
        var myChart = echarts.init(document.getElementById('fb1'));
        
        // 检查技能薪资数据是否存在
        if (!skill_salary || !skill_salary.names || !skill_salary.salaries) {
            console.error("技能薪资数据不存在或格式不正确");
            return;
        }
        
        option = {
            title: [{
                text: '热门技能平均薪资对比(K)',
                left: 'center',
                top: 0,
                textStyle: {
                    color: '#fff',
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            }],
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow',
                    lineStyle: {
                        color: '#dddc6b'
                    }
                },
                formatter: '{b}: {c}K',
                backgroundColor: 'rgba(50,50,50,0.7)',
                borderColor: '#ccc',
                borderWidth: 1,
                textStyle: {
                    color: '#fff'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                top: '25%',
                containLabel: true
            },
            xAxis: {
                type: 'value',
                name: '薪资(K)',
                nameTextStyle: {
                    color: 'rgba(255,255,255,.8)',
                    fontSize: 12,
                    padding: [0, 30, 0, 0]
                },
                axisLabel: {
                    formatter: '{value}K',
                    textStyle: {
                        color: "rgba(255,255,255,.8)",
                        fontSize: 12
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: 'rgba(255,255,255,.3)',
                        width: 2
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: 'rgba(255,255,255,.1)',
                        type: 'dashed'
                    }
                }
            },
            yAxis: {
                type: 'category',
                data: skill_salary.names,
                axisLabel: {
                    textStyle: {
                        color: "rgba(255,255,255,.8)",
                        fontSize: 12,
                        fontWeight: 'bold'
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: 'rgba(255,255,255,.3)',
                        width: 2
                    }
                },
                splitLine: {
                    show: false
                },
                axisTick: {
                    show: false
                }
            },
            series: [
                {
                    name: '平均薪资',
                    type: 'bar',
                    data: skill_salary.salaries,
                    barWidth: '60%',
                    itemStyle: {
                        normal: {
                            // 使用与echarts_6相似的颜色方案
                            color: function(params) {
                                // 基本颜色
                                var baseColor = mainColors[params.dataIndex % mainColors.length];
                                
                                // 创建渐变
                                return new echarts.graphic.LinearGradient(1, 0, 0, 0, [{
                                    offset: 0,
                                    color: adjustBrightness(baseColor, 0.7) // 结束颜色，稍微调暗
                                }, {
                                    offset: 1,
                                    color: baseColor // 起始颜色
                                }]);
                            },
                            barBorderRadius: [0, 5, 5, 0],
                            shadowColor: 'rgba(0, 0, 0, 0.3)',
                            shadowBlur: 10,
                            // 显示数值标签
                            label: {
                                show: true,
                                position: 'right',
                                formatter: '{c}K',
                                textStyle: {
                                    color: 'rgba(255,255,255,.9)',
                                    fontSize: 12,
                                    fontWeight: 'bold'
                                }
                            }
                        },
                        emphasis: {
                            barBorderRadius: [0, 8, 8, 0],
                            shadowBlur: 20,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    },
                    // 添加动画效果
                    animationDelay: function (idx) {
                        return idx * 100;
                    },
                    animationDuration: 1000,
                    animationEasing: 'elasticOut'
                }
            ]
        };

        // 使用刚指定的配置项和数据显示图表。
        myChart.setOption(option);
        window.addEventListener("resize", function () {
            myChart.resize();
        });
    }

    function map_1() {
        // 基于准备好的dom，初始化echarts实例
        var myChart = echarts.init(document.getElementById('map_1'));
        
        // 检查中国地图是否已注册
        if (!echarts.getMap('china')) {
            console.error('中国地图未注册');
            return;
        }
        
        // 检查数据是否存在
        if (!geo || !geo.geo_1) {
            console.error("地图数据不存在或格式不正确");
            return;
        }
        
        console.log("地图数据:", geo.geo_1);
        
        // 处理地图数据，确保名称与地图匹配
        var processedData = [];
        var geoCoordMap = {
            '北京': [116.4551, 40.2539],
            '上海': [121.4648, 31.2891],
            '天津': [117.4219, 39.4189],
            '重庆': [107.7539, 30.1904],
            '河北': [114.4995, 38.1006],
            '山西': [112.3352, 37.9413],
            '内蒙古': [111.4124, 40.8367],
            '辽宁': [123.1238, 42.1216],
            '吉林': [125.8154, 44.2584],
            '黑龙江': [127.9688, 45.368],
            '江苏': [118.8062, 31.9208],
            '浙江': [119.5313, 29.8773],
            '安徽': [117.29, 32.0581],
            '福建': [119.4543, 25.9222],
            '江西': [116.0046, 28.6633],
            '山东': [117.1582, 36.8701],
            '河南': [113.4668, 34.6234],
            '湖北': [114.3896, 30.6628],
            '湖南': [113.0823, 28.2568],
            '广东': [113.5107, 23.2196],
            '广西': [108.479, 23.1152],
            '海南': [110.3893, 19.8516],
            '四川': [103.9526, 30.7617],
            '贵州': [106.6992, 26.7682],
            '云南': [102.9199, 25.4663],
            '西藏': [91.1865, 30.1465],
            '陕西': [109.1162, 34.2004],
            '甘肃': [103.5901, 36.3043],
            '青海': [101.4038, 36.8207],
            '宁夏': [106.3586, 38.1775],
            '新疆': [87.9236, 43.5883],
            '香港': [114.1733, 22.3193],
            '澳门': [113.5501, 22.1094],
            '台湾': [121.5200, 25.0307]
        };
        
        // 准备散点数据
        var scatterData = [];
        var effectScatterData = [];
        
        for (var i = 0; i < geo.geo_1.length; i++) {
            var item = geo.geo_1[i];
            // 处理城市名称，去除可能的"市"、"省"、"自治区"等后缀
            var name = item.name.replace(/(市|省|自治区|特别行政区|壮族|维吾尔|回族|藏族)$/, '');
            var value = item.value;
            
            processedData.push({
                name: name,
                value: value
            });
            
            // 获取地理坐标
            var coord = geoCoordMap[name];
            if (coord) {
                // 根据数据大小分配到不同的系列
                if (value >= 100) {
                    scatterData.push({
                        name: name,
                        value: coord.concat(value)
                    });
                } else if (value > 0) {
                    // 小数据使用涟漪效果散点
                    effectScatterData.push({
                        name: name,
                        value: coord.concat(value)
                    });
                }
            }
        }
        
        // 找出最大值和最小值
        var max = 0;
        var min = Number.MAX_VALUE;
        for (var i = 0; i < processedData.length; i++) {
            if (processedData[i].value > max) {
                max = processedData[i].value;
            }
            if (processedData[i].value < min && processedData[i].value > 0) {
                min = processedData[i].value;
            }
        }
        
        // 确保最小值不为0，避免颜色区分不明显
        if (min === max || min === Number.MAX_VALUE) {
            min = 1;
        }
        
        option = {
            backgroundColor: 'transparent',
            title: {
                text: '计算机行业职位地区分布热度',
                subtext: '数据来源：职位推荐系统',
                left: 'center',
                textStyle: {
                    color: '#fff',
                    fontSize: '16',
                }
            },
            tooltip: {
                trigger: 'item',
                formatter: function(params) {
                    if (params.seriesType === 'map') {
                        var value = params.value;
                        if (value === undefined || value === null) {
                            value = 0;
                        }
                        return params.name + ': ' + value + ' 个职位';
                    } else {
                        return params.name + ': ' + params.value[2] + ' 个职位';
                    }
                }
            },
            // 地图系列设置
            geo: {
                map: 'china',
                roam: true,
                zoom: 1,
                label: {
                    emphasis: {
                        show: false
                    }
                },
                itemStyle: {
                    normal: {
                        areaColor: '#001a33', // 更深的背景色，增强对比度
                        borderColor: 'rgba(255, 255, 255, 0.5)' // 更明显的边界线
                    },
                    emphasis: {
                        areaColor: '#003366' // 鼠标悬停时的颜色
                    }
                }
            },
            series: [
                {
                    name: '职位数量',
                    type: 'map',
                    map: 'china',
                    roam: true, // 允许缩放和平移
                    zoom: 1.2, // 默认放大一点
                    label: {
                        show: true,
                        formatter: '{b}',
                        textStyle: {
                            color: '#fff',
                            fontSize: 8
                        }
                    },
                    itemStyle: {
                        normal: {
                            areaColor: '#001a33', // 更深的背景色，增强对比度
                            borderColor: 'rgba(255, 255, 255, 0.5)' // 更明显的边界线
                        },
                        emphasis: {
                            areaColor: '#003366' // 鼠标悬停时的颜色
                        }
                    },
                    data: processedData
                },
                {
                    name: '大数据点',
                    type: 'scatter',
                    coordinateSystem: 'geo',
                    data: scatterData,
                    symbolSize: function (val) {
                        var value = val[2];
                        return Math.min(Math.max(Math.sqrt(value) * 0.8, 8), 20);
                    },
                    label: {
                        normal: {
                            show: false
                        },
                        emphasis: {
                            show: false
                        }
                    },
                    itemStyle: {
                        normal: {
                            color: '#ffeb3b',
                            shadowBlur: 15, // 增强阴影效果
                            shadowColor: '#333'
                        }
                    }
                },
                {
                    name: '小数据点',
                    type: 'effectScatter',
                    coordinateSystem: 'geo',
                    data: effectScatterData,
                    symbolSize: function (val) {
                        return 8;
                    },
                    showEffectOn: 'render',
                    rippleEffect: {
                        brushType: 'stroke',
                        scale: 3,
                        period: 4
                    },
                    hoverAnimation: true,
                    label: {
                        normal: {
                            show: false
                        }
                    },
                    itemStyle: {
                        normal: {
                            color: '#ff5722',
                            shadowBlur: 15, // 增强阴影效果
                            shadowColor: '#333'
                        }
                    },
                    zlevel: 1
                }
            ]
        };

        // 使用刚指定的配置项和数据显示图表。
        myChart.setOption(option);
        window.addEventListener("resize", function () {
            myChart.resize();
        });
    }
})



		
		
		


		









