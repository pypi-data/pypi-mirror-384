import dateutil.parser, datetime, time, re


from astropy.time import Time

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BLACK = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

colors_dc = {
    'header': colors.HEADER,
    'blue': colors.OKBLUE,
    'green': colors.OKGREEN,
    'warn': colors.WARNING,
    'red': colors.FAIL,
    'black': colors.BLACK,
    'bold': colors.BOLD,
    'underline': colors.UNDERLINE
}

colors_dc_all = {**colors_dc, **{v:v for v in colors_dc.values()}}
    
def print_color(msg, color='red'):
    if isinstance(color, str):
        color = colors_dc_all.get(color, colors.BLACK)
    print(f"{color}{msg}{colors.BLACK}")


def get_utcnow():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=datetime.timezone.utc)

def make_zulustr(dtobj, remove_ms = True):
    utc = dtobj.replace(tzinfo=datetime.timezone.utc)
    if remove_ms:
        utc = utc.replace(microsecond=0)
    return utc.isoformat().replace('+00:00','') + 'Z'

def mk_dtz(dtobj=None, remove_ms = True):
    if dtobj is None:
        dtobj = get_utcnow()
    return make_zulustr(dtobj, remove_ms).replace('T',' ').replace('Z',' ')

def match_zulutime(s):
    if s is None: return None

    s = s.strip()
    if '.' in s and re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{1,6}Z', s) is not None:
        return s
    elif 'T' in s and re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z', s) is not None:
        return s
    elif re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}Z', s) is not None:
        return s
    else:
        return None

def anytime2datetime(t):
    if isinstance(t, Time):
        t = parse_zulutime(t.isot)
    
    if isinstance(t, str):
        t = parse_zulutime(t)
    
    if isinstance(t, (int, float)):
        if t >= 1e12: # nanosec
            t = t / 1000000000
        t = datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc)
        
    
    assert isinstance(t, datetime.datetime) and t.tzinfo == datetime.timezone.utc, f'expected datetime with utc timezone but got {type(t)=} with {t.tzinfo=}'
    return t

def parse_zulutime(s):
    try:
        if re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}Z', s) is not None:
            s = s[:-1] + 'T00:00:00Z'
        return dateutil.parser.isoparse(s).replace(tzinfo=datetime.timezone.utc)
    except Exception:
        return None
    
def parse_timedelta(time_str, strptime_format='%H:%M:%S'):
    """Parses a time string in the format 'HH:MM:SS' into a timedelta object using strptime.

    Args:
        time_str: The time string to parse.
        strptime_format: the format string to use.

    Returns:
        A timedelta object representing the time duration.
    """

    time_obj = datetime.datetime.strptime(time_str, strptime_format)
    return datetime.timedelta(hours=time_obj.hour, minutes=time_obj.minute, seconds=time_obj.second)


def is_notebook() -> bool:
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter



def get_ntp_time_with_socket(ntp_server_address):
    """Retrieves the current time from an NTP server using socket programming.

    Args:
        ntp_server_address: The IP address of the NTP server.

    Returns:
        A tuple containing the current time as a Unix timestamp and a human-readable string.
    """
    
    import socket
    import struct
    import time

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.sendto(b'\x1b' + 47 * b'\0', (ntp_server_address, 123))
    message, address = client.recvfrom(1024)
    
    ntp_ts = struct.unpack('!II', message[40:48])
    # convert ntp to unix (https://tickelton.gitlab.io/articles/ntp-timestamps/)
    t_unix = (ntp_ts[0] - 2208988800) + float(ntp_ts[1]) / 2**32
    
    dt_utc = datetime.datetime.fromtimestamp(t_unix, datetime.timezone.utc)

    # Format the datetime object in ISO 8601 format
    human_time_iso = make_zulustr(dt_utc, remove_ms=False)

    return human_time_iso
