


import copy
import datetime

import numpy as np
import pandas as pd


from mke_sculib.helpers import make_zulustr, match_zulutime, get_utcnow, parse_zulutime, colors, colors_dc, print_color



class colors_hex:
    blue = '#6495ED'
    red = '#D2042D'
    mangenta = '#FF00FF'
    orange = '#FF5F1F'
    green = '#228B22'
    gray = '#D3D3D3'

def test_command_auth(x):
    try:
        num = int(x)
        if num == 0:
            return True, colors_hex.green, 'FREE'
        elif num == 1:
            return True, colors_hex.blue, 'LMC'
        elif num == 2:
            return False, colors_hex.orange, 'ENG_UI'
        elif num == 3:
            return True, colors_hex.green, 'WEBUI'
        elif num == 4:
            return False, colors_hex.red, 'HHP'
        else:
            return False, None, 'UNKNOWN'
        
    except Exception as err:
        return False, colors_hex.red, 'ERROR: ' + str(err)


chanmap = {
    'acu.safety_controller.safety_status_bs.safety_system_error': dict(color=colors_hex.red, expected=False, needed=True),
    'acu.safety_controller.safety_status_bs.lockout_azimuth': dict(color=colors_hex.red, expected=False, needed=True),
    'acu.safety_controller.safety_status_bs.lockout_elevation': dict(color=colors_hex.red, expected=False, needed=True),
    'acu.safety_controller.safety_status_bs.lockout_feedindexer': dict(color=colors_hex.red, expected=False, needed=True),

    'acu.safety_controller.safety_status_bs.interlock_hatch': dict(color=colors_hex.red, expected=False, needed=True),
    'acu.safety_controller.safety_status_bs.e_stop_hhd_junction_box': dict(color=colors_hex.red, expected=False, needed=True),
    'acu.feed_indexer.axis_bit_status.abs_emergency_stop': dict(color=colors_hex.red, expected=False, needed=True),
    'acu.elevation.axis_bit_status.abs_emergency_stop': dict(color=colors_hex.red, expected=False, needed=True),
    'acu.azimuth.axis_bit_status.abs_emergency_stop': dict(color=colors_hex.red, expected=False, needed=True),


    'acu.azimuth.error_status.err_error_active': dict(color=colors_hex.orange, expected=False, needed=False),
    'acu.elevation.error_status.err_error_active': dict(color=colors_hex.orange, expected=False, needed=False),
    'acu.feed_indexer.error_status.err_error_active': dict(color=colors_hex.orange, expected=False, needed=False),
    'acu.command_arbiter.act_authority': dict(color=colors_hex.orange, expected=test_command_auth, needed=False),

    'acu.general_management_and_controller.warning_status.door_ped_open_warning': dict(color=colors_hex.orange, expected=False, needed=False),
    'acu.general_management_and_controller.warning_status.door_psc_open_warning': dict(color=colors_hex.orange, expected=False, needed=False),
    'acu.general_management_and_controller.warning_status.door_sc_open_warning': dict(color=colors_hex.orange, expected=False, needed=False),
    'acu.general_management_and_controller.warning_status.door_d_open_warning': dict(color=colors_hex.orange, expected=False, needed=False),
    'acu.general_management_and_controller.warning_status.hatch_el_open_warning': dict(color=colors_hex.orange, expected=False, needed=False),
}


def shorten_channel_name(chan_name):
    s = chan_name
    s = s.replace('.elevation.', '.el.').replace('.azimuth.', '.az.').replace('.feed_indexer.', '.fi.')
    s = s.replace('.warning_status.', '.warn.').replace('.error_status.', '.err.')
    s = s.replace('.general_management_and_controller.', '.gmc.').replace('acu.', '')
    return s

class ChannelState():
    @staticmethod
    def from_chanmap(chanvals, chanmap):
        return [ChannelState.from_chanmapi(k, chanvals[k], chanmap[k]) for k in chanmap if k in chanvals]
    
    @staticmethod
    def from_chanmapi(channel_name, channel_state, dc):
        expected_state = dc['expected']
        
        can_ignore = dc['needed'] == False
        color = None
        if hasattr(expected_state, '__call__'):
            is_ok, color, result = expected_state(channel_state)
            p = 'PASS' if is_ok else 'FAIL'
            hint = f'test({channel_state=}) => {result=} ==> {p}!'
            channel_state = result # + f' ({channel_state})'
            expected_state = str(expected_state)
        else:
            is_ok = channel_state == expected_state

            if is_ok:
                hint = f'{channel_state=} == {expected_state=} ==> PASS!'
            else:
                hint = f'{channel_state=} != {expected_state=} ==> FAIL!'
        
        if color is None:
            if can_ignore and not is_ok:
                color = colors_hex.blue
            elif is_ok:
                color = colors_hex.green
            else:
                color = dc.get('color', colors_hex.mangenta) # mangenta
            
        return ChannelState(channel_name, channel_state, color, hint, expected_state, is_ok, can_ignore)
    
    def get_html_table_header(stl='border:1px black solid; border-collapse: collapse;text-align: center; padding:5px;'):
        return f'''<tr>
    <th style="{stl}">Channel Name</th>
    <th style="{stl}">Sate</th>
    <th style="{stl}">Result</th>
</tr>'''


    def connection_error(channel_name):       
        expected_state = channel_state = is_ok = can_ignore = 'UNKNOWN'

        hint = f'CONNECTION ERROR!'
        color = colors_hex.mangenta
            
        return ChannelState(channel_name, channel_state, color, hint, expected_state, is_ok, can_ignore)
    

        
    def __init__(self, channel_name, channel_state, color, hint, expected_state, is_ok, can_ignore) -> None:
        self.channel_name = channel_name
        self.channel_state = channel_state
        self.expected_state = expected_state
        self.color = color
        self.hint = hint
        self.is_ok = is_ok
        self.can_ignore = can_ignore
        
    def __str__(self):
        return f'{self.channel_name}="{self.channel_state}" vs.expected="{self.expected_state}" ==> {self.is_ok} {"can_ignore" if self.can_ignore and not self.is_ok else ""}'
    
    def __repr__(self):
        return str(self)
    
    def to_html(self, with_chan_name=False):
        if self.is_ok:
            s = 'PASS!'
            exp = ''
        elif self.can_ignore and not self.is_ok:
            s = f'IGNORED!' 
            exp = f'(expected: "<code>{self.expected_state}</code>")'
        else:
            s = f'FAIL!'
            exp = f'(expected: "<code>{self.expected_state}</code>")' 
            
        if with_chan_name:
            return f'<span><code>{ self.channel_name }</code> = "<code>{self.channel_state}</code>"  \u21D2 <span style="color:{self.color};"><b>{s}</b></span> {exp} </span>'
        else:
            suffix = f'(expected "{self.expected_state}" vs. actual "{self.channel_state}")'
            return f'<span>{s}{suffix}</span>' #  style="color:{self.color}; background-color:white;"
    
    def to_html_row(self, stl='border:1px black solid; border-collapse: collapse;text-align: center; padding:5px;'):
        if self.is_ok:
            s = 'PASS!'
            exp = ''
        elif self.can_ignore and not self.is_ok:
            s = f'IGNORED!' 
            exp = f'(expected: "<code>{self.expected_state}</code>")'
        else:
            s = f'FAIL!'
            exp = f'(expected: "<code>{self.expected_state}</code>")' 
            
        return f'''<tr>
    <td style="{stl}"><code>{ self.channel_name }</code></td>
    <td style="{stl}"><code>{ self.channel_state }</code></td>
    <td style="{stl}"><span style="color:{self.color};"><b>{s}</b> {exp}</span></td>
</tr>'''

    def to_row(self):
        if self.is_ok:
            s = 'PASS!'
            exp = ''
        elif self.can_ignore and not self.is_ok:
            s = f'IGNORED!' 
            exp = f' (expected: "<code>{self.expected_state}</code>")'
        else:
            s = f'FAIL!'
            exp = f' (expected: "<code>{self.expected_state}</code>")' 
            
        return {'Channel Name': self.channel_name, 'State': self.channel_state, 'Result': f'{s}{exp}'}
    
    def to_dict(self):
        if self.is_ok:
            s = 'PASS!'
        elif self.can_ignore and not self.is_ok:
            s = f'IGNORED!' 
        else:
            s = f'FAIL!'
        return {'name': self.channel_name, 'state': self.channel_state, 'color': self.color, 'expected': self.expected_state, 'result': s}

    def to_str(self, prefix='', sep=''):
        if self.is_ok:
            s = 'PASS!'
        elif self.can_ignore and not self.is_ok:
            s = f'IGNORED!' 
        else:
            s = f'FAIL!'
        suffix = f'(expected "{self.expected_state}" vs. actual "{self.channel_state}")'
        return f'{prefix}{sep}{self.channel_name} --> {s}{suffix}'

    def to_kv(self, prefix='', sep=''):
        return self.to_k(prefix, sep), self.to_v()

    def to_v(self):
        if self.is_ok:
            s = 'PASS!'
        elif self.can_ignore and not self.is_ok:
            s = f'IGNORED!' 
        else:
            s = f'FAIL!'
        suffix = f'(expected "{self.expected_state}" vs. actual "{self.channel_state}")'
        return f'{s}{suffix}'


    def to_k(self, prefix='', sep=''):
        return f'{prefix}{sep}{self.channel_name}'
    


def _dish_state_to_text(dish_api_obj, antenna_id, chaninfo, is_ok, short, nohead):
    
    from tabulate import tabulate

    if not antenna_id:
        antenna_id = dish_api_obj.address
        

    dish_type = dish_api_obj.dish_type
    tres = 'PASS!' if is_ok else 'FAIL!'
    
    
    s = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    s = s.replace('T', ' ').split('.')[0] + 'Z'
        
    chans = ['acu.azimuth.p_act',
        'acu.elevation.p_act',
        'acu.pointing.pointing_status.point_pointing_model_enabled',
        'acu.pointing.pointing_status.point_amb_temp_corr_enabled',
        'acu.pointing.pointing_status.point_incl_corr_enabled'
    ]

    az, el, spem_on, at_corr_on, incl_on = dish_api_obj.getc(chans, as_dict=False)
    azel_str = f'{az: 5.1f}°/{el: 4.1f}°'

    err_chans = ''
    if short == 3:
        azel_str = f'{az: .1f}°/{el: .1f}°'

        errs = dish_api_obj.get_errors(warnings=False)
        if errs and len(errs) < 5:
            err_chans = [f'"{k.split(".")[-1]}"' for k in errs.keys()]
            err_chans = ", ".join(err_chans)
            err_chans = f'| ERRORS: {err_chans}'
        elif errs:
            err_chans = f'| ERRORS: n={len(errs)}'

        tmplt = {
            'state': dish_api_obj.get_state(),
            'AZ/EL': azel_str,
            'time (UTC)': dish_api_obj.t_internal.iso,
            'ALL CLEAR?': tres
        }
        
        return str(dish_api_obj) + ' | ' + ' | '.join([f'{k}: {v}' for k, v in tmplt.items()]) + err_chans
    
    if short == 2:

        errs = dish_api_obj.get_errors(warnings=False)
        if errs:
            err_chans = [f'"{k}"' for k in errs.keys()]
            err_chans = ", ".join(err_chans)
            err_chans = f'\nERRORS: {err_chans}'

        tmplt = {
            'state': dish_api_obj.get_state(),
            'AZ/EL': azel_str,
            'time (UTC)': dish_api_obj.t_internal.iso,
            'ALL CLEAR?': f'{tres}  (@: {s})'
        }

        return str(dish_api_obj) + '\n' + '\n'.join(tabulate(tmplt.items(), tablefmt="github").split('\n')[1:]) + err_chans
    
    rows = [{'Dish-Type': dish_type, 
             'address': dish_api_obj.address, 
             'current state': dish_api_obj.get_state(), 
             'Az/EL [deg]': azel_str, 
             'current (UTC) timestamp': dish_api_obj.t_internal.iso}]
    
    txt = pd.DataFrame(rows).to_markdown(index=False, tablefmt="grid")  


    if short == 1:
        chaninfo = [c for c in chaninfo if not c.is_ok]
        
    rows = [s.to_row() for s in chaninfo]
    tmp = pd.DataFrame(rows)
    li = tabulate(tmp.values.tolist(), tmp.columns, tablefmt='github')
    
    
    head = '' 
    if not nohead: 
        head = f'<<=== DISH: "{antenna_id}" ===>>'
        head = head.rjust(max(100-len(head), 0) // 2)
    
    err_chans = ''

    if not short:
        errs = dish_api_obj.get_errors(warnings=True)
        if errs:
            err_chans = [f'- {k}' for k in errs.keys()]
            err_chans = "\n".join(err_chans)         
            err_chans = f'\nERRORS AND WARNINGS:\n{err_chans}'

    
    
    if not short:
        temps = dish_api_obj.get_temperatures(shorten_names=True)
        cells = {}
        cells['SPEM'] = 'ON' if spem_on else 'OFF'
        cells['ATCORR'] = 'ON' if at_corr_on else 'OFF'
        cells['INCL'] = 'ON' if incl_on else 'OFF'
        cells.update({k:f'{v:.1f}°' for k, v in temps.items()})
        cells.pop('temp_air_inlet_psc')
        mat = pd.DataFrame([cells]).T.reset_index().values        
        # mat = mat.reshape(6, mat.shape[0] // 3)
        status = tabulate(mat.tolist(), tablefmt='github')
        status = status.split('\n')[1:]
        status = '\n'.join([''.join(status[i:i+3]) for i in range(0, len(status), 3)])
    else:
        status = ''

    line = '_'*100

  

    tmplt = f'''{head}
{line}
STATUS: 
{txt}

{status}
{line}
TESTRESULT: {tres}  (@: {s})
{li}
{line}
{err_chans}
{line}'''
    return tmplt


def _dish_state_to_html(dish_api_obj, antenna_id, chaninfo, is_ok, short, nohead):
    
    dish_type = dish_api_obj.dish_type
    
    if not antenna_id:
        antenna_id = dish_api_obj.address
        

    if short:
        chaninfo = [c for c in chaninfo if not c.is_ok]
        
    # li = '\n\n'.join([f'<li>{s.to_html(with_chan_name=True)}</li>' for s in chaninfo])
    if is_ok:
        tres = '<span style="color:green;"> <b>PASS!</b> </span>'
    else:
        tres = '<span style="color:red;"> <b>FAIL!</b> </span>'

    stl = 'border:1px black solid; border-collapse: collapse;text-align: center; padding:5px;'

    
    rows = [ChannelState.get_html_table_header(stl)] 
    rows += [s.to_html_row() for s in chaninfo]
    
    channel_state_rows = '\n\n'.join(rows)

    head = '' if nohead else f'<h2>DISH: "{antenna_id}"</h2> '
    
    err_chans = ''

    if not short:
        errs = dish_api_obj.get_errors(warnings=True)
        if errs:
            err_chans = [f'<li style="color: {"#B8860B" if "warn" in k else "red"};">{k}</li>' for k in errs.keys()]
            err_chans = "\n".join(err_chans)         
            err_chans = f'<hr><h4>ERRORS AND WARNINGS:</h4>\n\n<ul>\n{err_chans}\n</ul>'           

    s = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    s = s.replace('T', ' ').split('.')[0] + 'Z'
    



    chans = ['acu.azimuth.p_act',
        'acu.elevation.p_act',
        'acu.pointing.pointing_status.point_pointing_model_enabled',
        'acu.pointing.pointing_status.point_amb_temp_corr_enabled',
        'acu.pointing.pointing_status.point_incl_corr_enabled'
    ]

    az, el, spem_on, at_corr_on, incl_on = dish_api_obj.getc(chans, as_dict=False)
    azel_str = f'{az: 5.1f}°/{el: 4.1f}°'

    onoff = lambda x: 'ON' if x else 'OFF'

    def format_temps(k, temp, min_err=-5, min_warn=0, max_warn=35, max_err=45):
        if 'motor' in k:
            min_err -= 10
            min_warn -= 10
            max_err += 20
            max_warn += 20

        t = float(temp)
        if t < min_err:
            color = '#7a31f7'
        elif t < min_warn:
            color = '#3184f7' 
        elif t > max_err:
            color = 'red'
        elif t > max_warn:
            color = "#B8860B"
        else:
            color = 'green'
            
        return f'<th style="{stl}">{k}</th><td style="{stl} color: {color};">{temp:.1f}°</td>'
     
    temps = dish_api_obj.get_temperatures(shorten_names=True)

    cells = {k:format_temps(k, v) for k, v in temps.items()}

    cells['SPEM'] = f'<th style="{stl}">SPEM state</th><td style="{stl}">{onoff(spem_on)}</td>'
    cells['ATCORR'] = f'<th style="{stl}">ATCORR state</th><td style="{stl}">{onoff(at_corr_on)}</td>'
    cells['INCL'] = f'<th style="{stl}">INCL state</th><td style="{stl}">{onoff(incl_on)}</td>'

    table_layout = [['SPEM', 'ATCORR', 'INCL'],
                    ['temp_tower_amb_W', 'temp_tower_amb_S', 'temp_tower_amb_E'],
                    ['temp_emisc', 'temp_drive_cab', 'temp_air_outlet_psc'],
                    ['temp_az_motor_1', 'temp_el_motor_1', 'temp_fi_motor_1'],
                    ['temp_az_motor_2', 'temp_el_motor_2', 'temp_fi_motor_2']]

    joiner = "\n      "
    rows = '\n'.join([f'<tr>{joiner.join([cells[c] for c in row])}</tr>' for row in table_layout])
        

    tmplt = f'''{head}
<table style="{stl}">
    <tr>
        <th style="{stl}">Dish-Type</th>
        <th style="{stl}">address</th>
        <th style="{stl}">ACU Version</th>
        <th style="{stl}">Current state</th>
        <th style="{stl}">AZ/EL [deg]</th>
        <th style="{stl}">Current Band</th>
        <th style="{stl}">current (UTC) timestamp</th>
    </tr>
    <tr>
        <td style="{stl}"><code>{dish_type}</code></td>
        <td style="{stl}"><a href="{dish_api_obj.address}">{dish_api_obj.address}</a></td>
        <td style="{stl}"><code>{dish_api_obj.version_acu}</code></td>
        <td style="{stl}"><code>{dish_api_obj.get_state()}</code></td>
        <td style="{stl}"><code>{azel_str}</code></td>
        <td style="{stl}"><code>{dish_api_obj.get_band_in_focus(as_name=True)}</code></td>
        <td style="{stl}"><code>{dish_api_obj.t_internal.iso}</td>
    <tr>
</table>
<hr>
<table style="{stl}">
{rows}
</table>
<hr>
<h4>
    TESTRESULT: {tres}  
</h4>
<code>@: {s} </code>

<table style="{stl}">
    {channel_state_rows}
</table

{err_chans}
'''

    return tmplt


def get_dish_state_sub(dish_api_obj, antenna_id):

    if not antenna_id:
        antenna_id = dish_api_obj.address
        
    assert dish_api_obj.ping(timeout=5), f'ERROR: Ping for dish with {dish_api_obj.address=} FAILED!'
    dish_type = dish_api_obj.determine_dish_type()


    if dish_type != 'mke':
        chanmap_local = copy.deepcopy(chanmap)
        chanmap_local.pop('acu.safety_controller.safety_status_bs.interlock_hatch') # no hatch on skampi
        
        # different names on skampi
        skampi_mapper = {
            '.door_ped_open_warning': '.door_switch_warning_ped',
            '.door_psc_open_warning': '.door_switch_warning_psc',
            '.door_sc_open_warning': '.door_switch_warning_sc',
            '.door_d_open_warning': '.door_switch_warning_d',
            '.hatch_el_open_warning': '.hatch_el_warning',
            '.e_stop_hhd_junction_box': '.e_stop_hhd_lockout_box',
        }
        def replace_fwd(key):
            s = key
            for from_, to_ in skampi_mapper.items():
                s = s.replace(from_, to_)
            return s
        
        chanmap_local = {replace_fwd(k):v for k, v in chanmap_local.items()} 
        chans_act = dish_api_obj.getc(list(chanmap_local.keys()), as_dict=True)
    else:
        chanmap_local = copy.deepcopy(chanmap)
        chans_act = dish_api_obj.getc(as_dict=True)

    assert isinstance(chans_act, dict)
    chaninfo = ChannelState.from_chanmap(chans_act, chanmap_local)
    is_ok = all([c.is_ok or c.can_ignore for c in chaninfo])
    return chaninfo, is_ok

def show_dish_state_html(dish_api_obj, antenna_id=None, nohead=False, short=False, return_is_ok=False):

    chaninfo, is_ok = get_dish_state_sub(dish_api_obj, antenna_id)
    html = _dish_state_to_html(dish_api_obj, antenna_id, chaninfo, is_ok, short, nohead)

    return (html, is_ok) if return_is_ok else html

def show_dish_state_text(dish_api_obj, antenna_id=None, nohead=False, short=False, return_is_ok=False):

    chaninfo, is_ok = get_dish_state_sub(dish_api_obj, antenna_id)
    text = _dish_state_to_text(dish_api_obj, antenna_id, chaninfo, is_ok, short, nohead)

    return (text, is_ok) if return_is_ok else text