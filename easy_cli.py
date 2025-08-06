from shutil import get_terminal_size as _get_terminal_size
import os
import sys
from typing import Literal

#MARK: colors
supports_colors = (hasattr(sys.stdout, 'isatty') and sys.stdout.isatty())
_styles = Literal["None","RESET","BOLD","DIM","UNDERLINED","BLINK","INVERT","HIDDEN"]
_colors = Literal["None","BLACK","RED","GREEN","YELLOW","BLUE","MAGENTA","CYAN","WHITE","BRIGHT_BLACK","BRIGHT_RED","BRIGHT_GREEN","BRIGHT_YELLOW","BRIGHT_BLUE","BRIGHT_MAGENTA","BRIGHT_CYAN","BRIGHT_WHITE"]
def change_terminal_color(foreground:_colors="None", background:_colors="None", style:_styles="None"):
    final: list[str] = []
    cols: list[str] = ["BLACK","RED","GREEN","YELLOW","BLUE","MAGENTA","CYAN","WHITE"]
    cols2: list[str] = ["BRIGHT_BLACK","BRIGHT_RED","BRIGHT_GREEN","BRIGHT_YELLOW","BRIGHT_BLUE","BRIGHT_MAGENTA","BRIGHT_CYAN","BRIGHT_WHITE"]
    styles: list[str] = ["RESET","BOLD","DIM","None","UNDERLINED","BLINK","INVERT","HIDDEN"]
    if (foreground != "None"):
        if foreground in cols:
            final.append(str(cols.index(foreground)+30))
        if foreground in cols2:
            final.append(str(cols2.index(foreground)+90))
    if (background != "None"):
        if background in cols:
            final.append(str(cols.index(background)+40))
        if background in cols2:
            final.append(str(cols2.index(background)+100))
    if (style != "None"):
        if style in styles:
            final.append(str(styles.index(style)))
    if final:
        return f"\033[{';'.join(final)}m"
    return ""

#MARK: keys

# same
text_keys = set(map(lambda x:x.encode(), "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,;:-+*/|\\<>?!%=()[]{}@&#'\"^~_$"))
enter = b'\r'
escape = b'\x1b'
ctrl = {
'A': b'\x01','B': b'\x02','C': b'\x03','D': b'\x04',
'E': b'\x05','F': b'\x06','G': b'\x07','H': b'\x08',
'I': b'\t',  'J': b'\n',  'K': b'\x0b','L': b'\x0c',
'M': b'\r',  'N': b'\x0e','O': b'\x0f','P': b'\x10',
'Q': b'\x11','R': b'\x12','S': b'\x13','T': b'\x14',
'U': b'\x15','V': b'\x16','W': b'\x17','X': b'\x18',
'Y': b'\x19','Z': b'\x1a'
}

# different platforms
if sys.platform == 'win32':
    up_arrow, down_arrow, right_arrow, left_arrow = b'\xe0H',b'\xe0P',b'\xe0M',b'\xe0K'
    backspace = b'\x08'
    delete = b'\xe0S'
    page_up, page_down = b'\xe0I',b'\xe0Q'
    insert = b'\xe0R'
    end = b'\xe0O'
    home = b'\xe0G'
    num_middle = b'\x1b[E' # Linux only, won't work
    F_keys = {
    'F1':b'\x00;','F2':b'\x00<','F3':b'\x00=','F4':b'\x00>',
    'F5':b'\x00?','F6':b'\x00@','F7':b'\x00A','F8':b'\x00B',
    'F9':b'\x00C','F10':b'\x00D','F11':b'\xe0\x85','F12':b'\xe0\x86',
    'F13':b'\x00\x87','F14':b'\x00\x88','F15':b'\x00\x89','F16':b'\x00\x8A',
    'F17':b'\x00\x8B','F18':b'\x00\x8C','F19':b'\x00\x8D','F20':b'\x00\x8E',
    'F21':b'\x00\x8F','F22':b'\x00\x90','F23':b'\x00\x91','F24':b'\x00\x92'
    }
else:
    up_arrow, down_arrow, right_arrow, left_arrow = b'\x1b[A',b'\x1b[B',b'\x1b[C',b'\x1b[D'
    backspace = b'\x7f'
    delete = b'\x1b[3~'
    page_up, page_down = b'\x1b[5~', b'\x1b[6~'
    insert = b'\x1b[2~'
    end = b'\x1b[F'
    home = b'\x1b[H'
    num_middle = b'\x1b[E' # Linux only
    F_keys = {
    'F1':b'\x1bOP','F2':b'\x1bOQ','F3':b'\x1bOR','F4':b'\x1bOS',
    'F5':b'\x1b[15~','F6':b'\x1b[17~','F7':b'\x1b[18~','F8':b'\x1b[19~',
    'F9':b'\x1b[20~','F10':b'\x1b[21~','F11':b'\x1b[23~','F12':b'\x1b[24~',
    'F13':b'\x1b[25~','F14':b'\x1b[26~','F15':b'\x1b[28~','F16':b'\x1b[29~',
    'F17':b'\x1b[31~','F18':b'\x1b[32~','F19':b'\x1b[33~','F20':b'\x1b[34~',
    'F21':b'\x1b[35~','F22':b'\x1b[36~','F23':b'\x1b[37~','F24':b'\x1b[38~'
    }

reverse_ctrl = {item:key for key,item in ctrl.items()}
reverse_F_keys = {item:key for key,item in F_keys.items()}

#MARK: functions

def get_terminal_size() -> tuple[int,int]:
    size = _get_terminal_size()
    return size.columns, size.lines

def move_cursor(y:int=1, x:int=1) -> None:
    sys.stdout.write("\033[%d;%dH" % (y, x))
    sys.stdout.flush()

if sys.platform == 'win32':
    import msvcrt
    def get_key() -> bytes:
        first_byte = msvcrt.getch()
        # Handle special keys (e.g., arrow keys) and normal keys
        if first_byte in b'\xe0\x00':  # Escape character | Special key prefix
            return first_byte + msvcrt.getch()
        else:
            # Read further bytes if they are part of a multibyte sequence
            if first_byte >= b'\x80':  # If the first byte indicates a multibyte UTF-8 sequence
                while msvcrt.kbhit():  # While there are more bytes to read
                    first_byte += msvcrt.getch()
            return first_byte
    def clear_screen() -> None:
        os.system('cls')
else:
    import tty
    import termios
    def get_key() -> bytes:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ord(ch) >= 0xc0:  # Start of a UTF-8 multi-byte sequence
                num_bytes = 1
                if ord(ch) & 0xe0 == 0xc0:
                    num_bytes = 2
                elif ord(ch) & 0xf0 == 0xe0:
                    num_bytes = 3
                elif ord(ch) & 0xf8 == 0xf0:
                    num_bytes = 4
                for _ in range(num_bytes - 1):
                    ch += sys.stdin.read(1)
            elif ch == '\x1b':  # Escape character for special keys
                ch += sys.stdin.read(2)
                if ch[2] in "0123456789":
                    while not ch.endswith("~"):  # Read the full sequence for special keys
                        ch += sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch.encode('utf-8')
    def clear_screen() -> None:
        os.system('clear')
