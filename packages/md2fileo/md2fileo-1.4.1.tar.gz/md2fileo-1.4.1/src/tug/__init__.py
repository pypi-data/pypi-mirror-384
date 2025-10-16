from loguru import logger
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import tempfile
import tomllib
from typing import Any, Optional
from importlib import resources

from PyQt6.QtCore import QSettings, QVariant
from PyQt6.QtGui import QIcon, QPixmap

from .. import qss

FONT_SIZE = {
    '8pt': ('8pt', '9pt', '8pt'),
    '9pt': ('9pt', '10pt', '9pt'),
    '10pt': ('10pt', '11pt', '9pt'),
    '11pt': ('11pt', '12pt', '10pt'),
    '12pt': ('12pt', '14pt', '11pt'),
    '14pt': ('14pt', '16pt', '12pt'),
}

if sys.platform.startswith("win"):
    def reveal_file(path: str):
        subprocess.Popen(['explorer.exe', '/select,', str(Path(path))])

elif sys.platform.startswith("linux"):
    def reveal_file(path: str):
        cmd = f'''dbus-send --session --dest=org.freedesktop.FileManager1 --type=method_call \
/org/freedesktop/FileManager1 org.freedesktop.FileManager1.ShowItems \
array:string:file:////{str(Path(path)).replace(' ', '%20')} string:'''
        subprocess.Popen(cmd.split(' '))

else:
    def reveal_file(path: str):
        raise NotImplementedError(f"doesn't support {sys.platform} system")


APP_NAME = "fileo"
MAKER = 'miha'

entry_point: str = None
cfg_path = Path()
qss_params = {}
dyn_qss = defaultdict(list)
m_icons = defaultdict(list)
themes = {}

temp_dir = tempfile.TemporaryDirectory()

def new_window(db_name: str):
    logger.info(f'{db_name=}, frozen: {getattr(sys, "frozen", False)}')
    if getattr(sys, "frozen", False):
        logger.info(f'frozen: {db_name=}, {entry_point}')
        subprocess.Popen([entry_point, db_name, 'False', ])
    else:
        logger.info(f'not frozen: {db_name=}, {entry_point}')
        subprocess.Popen(
            [sys.executable, entry_point, db_name, 'False', ],  # sys.executable - python interpreter
        )

def get_app_setting(key: str, default: Optional[Any]=None) -> QVariant:
    """
    used to restore settings on application level
    """
    settings = QSettings(MAKER, APP_NAME)
    try:
        to_set = settings.value(key, default)
    except (TypeError, SystemError):
        to_set = default
    return to_set

def set_logger(first_instance: bool):
    logger.remove()
    use_logging = get_app_setting('USE_LOGGING', False)
    if not use_logging:
        return

    fmt = "{time:%y-%b-%d %H:%M:%S} | {module}.{function}({line}): {message}"

    log_path = Path(get_app_setting("DEFAULT_LOG_PATH")) / ('fileo.log' if first_instance else 'second.log')
    logger.add(str(log_path), format=fmt, rotation="1 days", retention=3)
    # logger.add(sys.stderr, format='"{file.path}({line})", {function} - {message}')
    logger.info(f"START =================> {log_path.as_posix()}")
    logger.info(f'{entry_point=}')

def create_dir(dir: Path):
    dir.mkdir(parents=True, exist_ok=True)

def save_to_file(filename: str, msg: str):
    """ save translated qss """
    pp = Path('~/fileo/report').expanduser()
    path = get_app_setting('DEFAULT_REPORT_PATH', str(pp))
    path = Path(path) / filename
    path.write_text(
        '\n'.join((f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f'File: {filename}',
            "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-", msg)))

def save_app_setting(**kwargs):
    """
    used to save settings on application level
    """
    if not kwargs:
        return
    settings = QSettings(MAKER, APP_NAME)

    for key, value in kwargs.items():
        settings.setValue(key, QVariant(value))

def prepare_styles(theme_key: str, to_save: bool) -> str:
    files = {'qss': "default.qss", 'ico': "icons.toml", 'param': "default.param"}
    dyn_qss.clear()
    qss_params.clear()
    theme_path = resources.files(qss)

    def get_theme_list():
        global themes
        theme_toml_file = theme_path / "themes.toml"
        if theme_toml_file.exists():
            with open(theme_toml_file, "rb") as f:
                themes = tomllib.load(f)
                # logger.info(f'{themes=}')

    get_theme_list()
    logger.info(f'{theme_key=}')
    theme = themes.get(theme_key if theme_key in themes else next(iter(themes)), {})

    def translate_qss(styles: str) -> str:
        keys = list(qss_params.keys())
        keys.sort(reverse=True)
        for key in keys:
            styles = styles.replace(key, qss_params[key])
        return styles

    def read_file(name: str) -> str:
        res_file = theme_path / name
        if res_file.exists():
            with open(res_file, "r") as ft:
                return ft.read()
        return resources.read_text(qss, name)

    def read_params():
        param = theme.get('param', '')
        parse_params(param)
        parse_params('common.param')

        extra = theme.get('extra', '')
        if extra:
            parse_params(extra)

        ico_app = f'{qss_params["$ico_app"]}.{"ico" if sys.platform.startswith("win") else "png"}'
        with resources.path(qss, ico_app) as _path:
            qss_params['$ico_app'] = str(_path)

    def parse_params(param: str):
        def check_for_double_key():
            seen = set()
            for name, _ in params:
                if name in seen:
                    raise Exception(f'Duplicate key "{name}" in qss parameters')
                seen.add(name)

        params = read_file(param)
        params = [it.split('~') for it in params.splitlines() if it.startswith("$") and ('~' in it)]
        check_for_double_key()
        params.sort(key=lambda x: x[0], reverse=True)
        qss_params.update(params)
        param_substitution()

    def param_substitution():
        def val_subst(val: str) -> str:
            nonlocal loop_check
            if val.startswith("$"):
                if val in loop_check:
                    raise Exception(f'Loop in parameter {val} substitution')
                loop_check.add(val)
                return val_subst(qss_params[val])
            return val

        for key, val in qss_params.items():
            loop_check = set(key)
            qss_params[key] = val_subst(val)

    def extract_dyn_qss() -> int:
        it = tr_styles.find("/* END")
        aa: str = tr_styles
        it2 = aa.find('##', it)
        lines = tr_styles[it2:].splitlines()
        dyn_qss_add_lines(lines)
        return it

    def dyn_qss_add_lines(lines: list[str]):
        for line in lines:
            if line.startswith('##'):
                key, val = line[2:].split('~')
                dyn_qss[key].append(val)

    styles = read_file(theme.get('qss', files['qss']))
    icons_txt = read_file(theme.get('ico', files['ico']))
    read_params()
    qss_params['$FoldTitles'] = get_app_setting('FoldTitles', qss_params['$FoldTitles'])
    font_size_key = get_app_setting('FONT_SIZE', '10pt')
    qss_params['$normalSize'], qss_params['$bigSize'], qss_params['$menuSize'] = FONT_SIZE[font_size_key]

    tr_icons = translate_qss(icons_txt)
    icons_res = tomllib.loads(tr_icons)

    svgs = collect_all_icons(icons_res)

    tr_styles = translate_qss(styles)
    start_dyn = extract_dyn_qss()

    if to_save:
        ttls = (" style parameters ", " style sheets ", " icons.toml ", " SVGs ")
        logs = (
            '\n'.join([f'{key}: {val}' for key, val in qss_params.items()]),
            tr_styles, tr_icons,
            '\n'.join([f'{key}:{val}' for key, val in svgs.items()])
        )
        b="-=-=-=-=-=-=-=-=-=-"
        save_to_file(f'theme {theme_key}.log',
            '\n'.join([''.join((b,x,b,'\n',y)) for x,y in zip(ttls, logs)])
        )

    return tr_styles[:start_dyn]

def get_dyn_qss(key: str, idx: int=0) -> str|list:
    qss = dyn_qss[key]
    if not qss:
        raise Exception(f'Not defined "{key}" qss')
    return dyn_qss[key][idx] if idx >= 0 else dyn_qss[key]

def collect_all_icons(icons_res: dict) -> dict:
    m_icons.clear()
    keys = {
        'folder': ('one_folder',),
        'hidden': ('one_folder_hide',),
        'mult_folder': ('mult_folder',),
        'mult_hidden': ('mult_folder_hide',),
        'prev_folder': ('arrow_back',),
        'next_folder': ('arrow_forward',),
        'history': ('history',),
        'search': ('search',),
        'match_case': ('match_case',),
        'match_word': ('match_word',),
        'regex': ('regex',),
        'ok': ('ok',),
        'busy': ('busy_off', 'busy_on',),
        'show_hide': ('show_hide_off', 'show_hide_on',),
        'btnFilterSetup': ('filter_setup', 'filter_setup_active',),
        'btnDir': ('folders', 'folders_active',),
        'btnSetup': ('menu', ),
        'btnFilter': ('filter', 'filter_active',),
        'btnToggleBar': ('angle_left', 'angle_right',),
        'more': ('more',),
        'refresh': ('refresh',),
        'collapse_all': ('collapse_all',),
        'collapse_notes': ('collapse_notes',),
        'plus': ('plus',),
        'cancel2': ('cancel2',),
        'up': ('angle_up',),
        'down': ('angle_down',),
        'right': ('angle_right_2',),
        'down3': ('angle_down_3',),
        'right3': ('angle_right_3',),
        'toEdit': ('pencil',),
        'folder_open': ('folder_open',),
        'minimize': ('minimize',),
        'maximize': ('maximize', 'restore',),
        'close': ('close',),
        'ico_app': ('app_ico',),
        'svg_files': (
            'check_box_off', 'check_box_on',
            'radio_btn', 'radio_btn_active',
            'vline3', 'angle_down3', 'angle_right3',
            'angle_down2',
        ),
    }
    return set_icons(keys, icons_res)

def get_icon(key: str, index: int = 0) -> QIcon:
    return m_icons[key][index]

def set_icons(keys: dict, icons_res: dict) -> dict:
    """
    add items into dict m_icons:
    keys - dict of list of svgs
    created item contains list of icons
    """
    mode = {
        'normal':  QIcon.Mode.Normal,
        'disabled':  QIcon.Mode.Disabled,
        'active':  QIcon.Mode.Active,
        'selected':  QIcon.Mode.Selected,
    }
    svgs = {}

    def get_pixmaps(svg_key: str) -> list|None:
        def get_svg() -> str:
            ico_subst = svg_stamp.get('ico_subst', '')
            if ico_subst:
                svg_root = icons_res[ico_subst]
                return svg_root.get('ico', ''), svg_stamp.get('colors', '')
            return svg_stamp.get('ico', ''), svg_stamp.get('colors', '')

        def get_colors():
            def get_color() -> tuple:
                """
                returns (mode, color)
                default mode is normal
                """
                tmp = clr.split('|')
                return tmp if len(tmp) == 2 else ('normal', tmp[0])

            colors = defaultdict(list)

            for clr in color_set:
                mm, color = get_color()
                colors[mm].append(
                    '' if color == '`' else color if color
                    else colors['normal'][len(colors[mm])]
                )
            return colors

        def create_pixs():
            nonlocal svg
            def create_pix(mode: str, svg: str):
                pic = QPixmap()
                pic.loadFromData(bytearray(svg, 'utf-8'),)
                pics.append((mode, pic))
                svgs[f'{svg_key}_{mode}'] = svg

            colors = get_colors()
            pics = []
            if not colors:  # [app_ico] only
                create_pix('normal', svg)
                return pics

            for mode_, color in colors.items():
                tmp = svg
                for i in range(svg.count('|')):
                    j = i % len(color)
                    tmp = tmp.replace('|', color[j], 1)

                if file_name:
                    create_image_file(mode_, tmp)
                    continue

                create_pix(mode_, tmp)

            return pics

        def create_image_file(icon_mode: str, svg: str):
            # logger.info(f'{file_name=}, {icon_mode=}')
            if icon_mode == 'normal':
                file_ = Path(temp_dir.name) / f'{file_name}.svg'
            else:
                file_ = Path(temp_dir.name) / f'{file_name}_{icon_mode}.svg'
            qss_params[f'${file_.stem}'] = file_.as_posix()

            file_.write_text(svg)

        svg_stamp: dict = icons_res.get(svg_key, "")
        if not svg_stamp:
            return []

        svg, color_set = get_svg()
        file_name = svg_stamp.get('save_in_file', '')
        return create_pixs()

    def create_icon():
        pixs = get_pixmaps(svg_key)

        ico = QIcon()
        for mm, px in pixs:
            # logger.info(f'{key=}, {mm=}')
            ico.addPixmap(px, mode=mode[mm])

        # logger.info(f'{key=}, {[p[0] for p in pixs]}')
        m_icons[key].append(ico)

    for key, svg_keys in keys.items():
        # logger.info(f'{key=}, {svg_keys=}')
        for svg_key in svg_keys:
            create_icon()

    return svgs
