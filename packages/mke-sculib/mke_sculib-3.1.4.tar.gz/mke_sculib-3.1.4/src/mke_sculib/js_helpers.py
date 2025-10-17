import json


    # <div id="live-update-graph-az" style="width:600px;height:250px;"></div>
    # <div id="live-update-graph-el" style="width:600px;height:250px;"></div>
    # <div id="live-update-graph-fi" style="width:600px;height:250px;"></div>
    # <div id="tester" style="width:600px;height:250px;"></div>

TEMPLATE_POS_CHART_PAGE = """<head>

    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js" charset="utf-8"></script>
    <div id="live-update-graph-az" <REPLACEME_STYLE>></div>
    <div id="live-update-graph-el" <REPLACEME_STYLE>></div>
    <div id="live-update-graph-fi" <REPLACEME_STYLE>></div>

    <script>
        
function makeChart(chans1, chans2, chans3, url_ws, element_ids) {
    
    const colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52'];


    // alert('Starting getting data from: '.concat(url_ws));
    
    function frmt(c) {
        var n = c;
        n = n.replace('general_management_and_controller', 'gmc');
        n = n.replace('azimuth', 'az');
        n = n.replace('elevation', 'el');
        n = n.replace('feed_indexer', 'fi');
        return n
    }

    
    var channels_per_element = [chans1, chans2, chans3];
    // console.log('channels_pt', channels_per_element);
    
    console.log('url_ws', url_ws);
    var needs_init = 1;

    var socket = new WebSocket(url_ws);
    // Connection opened
    socket.addEventListener("open", (event) => {
        // all channels we need from the source
        var channels = [];
        for (const k of channels_per_element){
            channels.push(...k);
        }
        var s = JSON.stringify(channels);
        console.log("Message to server ", s);
        socket.send(s);
    });

    // Listen for messages
    socket.addEventListener("message", (event) => {
        // console.log("Message from server ", event.data);
        
        let channeldata = JSON.parse(event.data);
        var t = new Date(channeldata['timestamp']);
        
        // console.log(channeldata);

        for (i in channels_per_element) {
            console.log(i);
            var x = [];
            var y = [];
            var names = [];
            for (const k of channels_per_element[i]) {
                x.push([t]);
                y.push([Number(channeldata['fields'][k][0])]);
                names.push([k])
            }

            
            var layout = {
                title: {
                text:element_ids[i],
                font: {
                    family: 'Courier New, monospace',
                    size: 24
                },
                xref: 'paper',
                x: 0.05,
                },
                xaxis: {
                title: {
                    text: 'time',
                    type: 'date',
                    range: [t.setMinutes(t.getMinutes() - 1), t.setMinutes(t.getMinutes() + 1)],
                    font: {
                    family: 'Courier New, monospace',
                    size: 18,
                    color: '#7f7f7f'
                    }
                },
                },
                yaxis: {
                title: {
                    text: 'Axis Position [deg]',
                    font: {
                    family: 'Courier New, monospace',
                    size: 18,
                    color: '#7f7f7f'
                    }
                }
                }
            };


            if (needs_init == 1){
                var traces = []
                for (j in channels_per_element[i]) {
                mode = ''
                traces.push({
                    x: x[j],
                    y: y[j],
                    mode: 'lines',
                    line: {color: colors[j]},
                    name: names[j][0]
                });
                }
                Plotly.newPlot(element_ids[i], traces, layout);
            } else {
                var gd = document.getElementById(element_ids[i])
                var data = gd.data
                
                for (j in channels_per_element[i]) {
                    data[j].x.push(x[j][0]);
                    data[j].y.push(y[j][0]);

                    while (data[j].x.length > 10000){
                        data[j].x.shift();
                    }
                    while (data[j].y.length > 10000){
                        data[j].y.shift();
                    }
                }
                
                Plotly.relayout(element_ids[i], layout);
                // Plotly.extendTraces(element_ids[i], data, [0, 1, 2]);
                Plotly.update(element_ids[i], data, [0, 1, 2]);
            }
        }
        needs_init = 0;

        var channels = [];
        for (const k of channels_per_element){
            channels.push(...k);
        }
    });


    var Httpreq = new XMLHttpRequest(); // a new request
    Httpreq.open("GET",url_http.concat('/devices/statusPaths'),false);
    Httpreq.send(null); 
    var json_obj = JSON.parse(Httpreq.responseText);
    console.log('channels possible', json_obj);
    return [json_obj, json_obj, json_obj]
}


var chans1 = <REPLACEME1>;
var chans2 = <REPLACEME2>;
var chans3 = <REPLACEME3>;

var eids = ['live-update-graph-az', 'live-update-graph-el', 'live-update-graph-fi'];
var url_ws = 'ws://<REPLACEME:IP>:<REPLACEME:PORT>/wsstatus'

makeChart(chans1, chans2, chans3, url_ws, eids);

    </script>
</head>"""

def make_livepos_page(dish_ip, 
                      chans1=['acu.azimuth.p_set', 'acu.azimuth.p_shape', 'acu.azimuth.p_act'],
                      chans2=['acu.elevation.p_set', 'acu.elevation.p_shape', 'acu.elevation.p_act'],
                      chans3=['acu.general_management_and_controller.state', 'acu.azimuth.state', 'acu.elevation.state'],
                      port = '8080', style="width:600px;height:100px;"):
    
    page = TEMPLATE_POS_CHART_PAGE.replace('<REPLACEME:IP>:<REPLACEME:PORT>', f'{dish_ip}:{port}')
    
    page = page.replace('<REPLACEME_STYLE>', json.dumps(style))
    page = page.replace('<REPLACEME1>', json.dumps(chans1))
    page = page.replace('<REPLACEME2>', json.dumps(chans2))
    return page.replace('<REPLACEME3>', json.dumps(chans3))



TEMPLATE_LIVEPLOT_PAGE = """<head>

    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js" charset="utf-8"></script>
    <div id="live-update-graph" <REPLACEME_STYLE>></div>

    <script>
        
function makeChart(channels, url_ws, element_id) {
    
    const colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52'];
    
    function frmt(c) {
        var n = c;
        n = n.replace('general_management_and_controller', 'gmc');
        n = n.replace('azimuth', 'az');
        n = n.replace('elevation', 'el');
        n = n.replace('feed_indexer', 'fi');
        return n
    }


    console.log('url_ws', url_ws);
    var needs_init = 1;

    var socket = new WebSocket(url_ws);
    // Connection opened
    socket.addEventListener("open", (event) => {
        var s = JSON.stringify(channels);
        console.log("Message to server ", s);
        socket.send(s);
    });

    // Listen for messages
    socket.addEventListener("message", (event) => {
        // console.log("Message from server ", event.data);
        
        let channeldata = JSON.parse(event.data);
        var t = new Date(channeldata['timestamp']);
        var x = [];
        var y = [];
        var names = [];
        for (const k of channels) {
            x.push([t]);
            y.push([Number(channeldata['fields'][k][0])]);
            names.push([k])
        }

        
        var layout = {
            xaxis: {
                title: {
                    text: 'time',
                    type: 'date',
                    range: [t.setMinutes(t.getMinutes() - 1), t.setMinutes(t.getMinutes() + 1)],
                    font: {
                    family: 'Courier New, monospace',
                    size: 10,
                    color: '#7f7f7f'
                    }
                },
            },
        };


        if (needs_init == 1){
            var traces = []
            for (j in channels) {
            mode = ''
            traces.push({
                x: x[j],
                y: y[j],
                mode: 'lines',
                line: {color: colors[j]},
                name: names[j][0]
            });
            }
            Plotly.newPlot(element_id, traces, layout);
        } else {
            var gd = document.getElementById(element_id)
            var data = gd.data
            
            for (j in channels) {
                data[j].x.push(x[j][0]);
                data[j].y.push(y[j][0]);

                while (data[j].x.length > 10000){
                    data[j].x.shift();
                }
                while (data[j].y.length > 10000){
                    data[j].y.shift();
                }
            }
            
            Plotly.relayout(element_id, layout);
            // Plotly.extendTraces(element_id, data, [0, 1, 2]);
            Plotly.update(element_id, data, [0, 1, 2]);
        }
        
        needs_init = 0;
    });
}


var chnls = <REPLACEME1>;
var url_ws = 'ws://<REPLACEME:IP>:<REPLACEME:PORT>/wsstatus'

makeChart(chnls, url_ws, 'live-update-graph');

    </script>
</head>"""


def make_liveplot_page(dish_ip, 
                      channels=['acu.azimuth.p_act', 'acu.elevation.p_act', 'acu.azimuth.p_act'],
                      port = '8080', style="width:600px;height:100px;"):
    
    page = TEMPLATE_LIVEPLOT_PAGE.replace('<REPLACEME:IP>:<REPLACEME:PORT>', f'{dish_ip}:{port}')
    page = page.replace('<REPLACEME_STYLE>', json.dumps(style))
    return page.replace('<REPLACEME1>', json.dumps(channels))



live_channels_page = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ShowChannels</title>
</head>
<body>
<div class="container mt-4">    
    <table class="table table-bordered mt-2">
        <!-- <thead>
        <tr>
            <th style="text-align: right; margin-right: 5px;">Key</th>
            <th style="min-width: 250px; text-align: center; margin-left: 5px;">Value</th>
        </tr>
        </thead> -->
        <tbody id="dataTable">
        </tbody>
    </table>
</div>


<script>



function getDataFromEvent(channeldata, channelsToGet) {
    console.log(channeldata);
    return {time: t, channeldata: channeldata}
}

function formatNumberIfNumeric(str, decimalPlaces=4) {
    // Check if the input is a number-like string
    if (/^-?\d+(\.\d+)?$/.test(str)) {
        // Convert to a number and format to the specified decimal places
        return parseFloat(str).toFixed(decimalPlaces);
    }
    else if (((typeof str === 'string' || str instanceof String) && str.toLowerCase() === "true") || str === true) {
        return '<span style="color: green;"">TRUE</span>'; 
    }
    else if ((typeof str === 'string' || str instanceof String) && str.toLowerCase() === "false" || str === false) {
        return '<span style="color: red;">FALSE</span>'; 
    } else { 
        return str;
    }
}


function log(s) {
    document.getElementById('info').innerText= s;
    console.log(s);
}

var url_http = '<REPLACEME:ADDRESS>'
var url_ws = url_http.replace('http://', 'ws://').replace(/\/$/, '').concat('/wsstatus')

var channels = <REPLACEME:CHANNELS>;



const dataTable = document.getElementById('dataTable');
dataTable.innerHTML = '';
var rows = ['info', 'timestamp'].concat(channels);

rows.forEach(chan => {
    const row = document.createElement('tr');
    const keyCell = document.createElement('td');
    const valueCell = document.createElement('td');
    keyCell.textContent = chan;
    keyCell.style.textAlign = 'right';
    keyCell.style.marginRight = '5px';
    valueCell.id = 'row-' + chan;
    valueCell.style.textAlign = 'center';
    valueCell.style.marginLeft = '5px';
    row.appendChild(keyCell);
    row.appendChild(valueCell);
    dataTable.appendChild(row);
});

if (channels.length > 0) {
    var socket = new WebSocket(url_ws);
    
    // Connection opened
    socket.onopen = function () {
        // all channels we need from the source
        var s = JSON.stringify(channels);
        console.log("Message to server ", s);
        socket.send(s);
    };


    socket.onmessage = function (event) {
        const obj = JSON.parse(event.data)
        document.getElementById('row-timestamp').innerText = new Date(obj['timestamp']).toISOString();
        const fields = obj['fields'];
        channels.forEach(key => {
            if (Object.hasOwnProperty.call(fields, key)) {
                document.getElementById('row-' + key).innerHTML = formatNumberIfNumeric(fields[key][0]);
            } else {
                console.error('key is missing', key, fields)
            }
        });
        
    };
    socket.onclose = function () {
        log('WebSocket is closed.');
    };
    socket.onerror = function (error) {
        log('WebSocket error: ' + error);
    };


}

</script>
</body>
</html>

"""


def make_livechannels_page(dish_address, 
                      channels=None):
    
    if channels is None:
        channels = [
        'acu.elevation.p_act',
        'acu.azimuth.p_act',
        'acu.general_management_and_controller.state',
        'acu.general_management_and_controller.p_point_corr_az',
        'acu.general_management_and_controller.p_point_corr_el',
        
        'acu.pointing.pointing_status.point_pointing_model_enabled',
        'acu.pointing.pointing_status.point_amb_temp_corr_enabled',
        'acu.pointing.pointing_status.point_incl_corr_enabled',

        'acu.pointing.incl_signal_x_corrected',
        'acu.pointing.incl_signal_y_corrected',
        'acu.pointing.incl_corr_val_az',
        'acu.pointing.incl_corr_val_el',
        'acu.pointing.pm_corr_val_az',
        'acu.pointing.pm_corr_val_el',
        'acu.pointing.point_corr_az',
        'acu.pointing.point_corr_el',
        'acu.actual_timestamp',
        ]

    page = TEMPLATE_LIVEPLOT_PAGE.replace('<REPLACEME:ADDRESS>', dish_address)
    page = page.replace('<REPLACEME:CHANNELS>', json.dumps(channels))
    return page




if __name__ == '__main__':
    print(make_liveplot_page('10.96.66.10'))