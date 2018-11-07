from colorama import init, Fore
init()


def __colored(s, color, bold = False):
    if bold:
        return '\033[1m' + color + s + Fore.RESET + '\033[0m'
    else:
        return color + s + Fore.RESET


def blue(s, bold = False):
    return __colored(s, Fore.BLUE, bold)


def green(s, bold = False):
    return __colored(s, Fore.GREEN, bold)


def yellow(s, bold = False):
    return __colored(s, Fore.YELLOW, bold)


def red(s, bold = False):
    return __colored(s, Fore.RED, bold)


def prompt(message, default = None):
    if default:
        ans = input('%s [%s]: ' % (message, default))
        return default if not ans else ans
    else:
        ans = input('%s: ' % message)
        return None if not ans else ans


def format_datetime(date_time):
    return '{0:%Y-%m-%d %H:%M:%S %Z}'.format(date_time) if date_time is not None else '-'


def shorten(s, slen, elen):
    if len(s) <= (slen + elen):
        return s
    else:
        if slen < 1:
            return '..%s' % s[len(s) - elen + 2:len(s)]
        elif elen < 1:
            return '%s..' % s[0:slen - 2]
        else:
            return '%s..%s' % (s[0:slen - 1], s[len(s) - elen + 1:len(s)])


