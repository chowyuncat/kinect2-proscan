import itertools
import _winreg

def enumerate_serial_ports():
    """ Uses the Win32 registry to return a iterator of serial 
        (COM) ports existing on this computer.


    """
    path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
    try:
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, path)
    except WindowsError:
        raise IterationError

    for i in itertools.count():
        try:
            val = _winreg.EnumValue(key, i)
            # yield (str(val[1]), str(val[0]))
            yield str(val[1])
        except EnvironmentError:
            break