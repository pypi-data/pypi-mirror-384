'''
    out - Simple logging with a few fun features.
    © 2018-25, Mike Miller - Released under the LGPL, version 3+.
'''
from console.constants import TermLevel
from console.detection import init, is_a_tty, is_fbterm, os_name
from console.style import ForegroundPalette, BackgroundPalette, EffectsPalette


def _find_palettes(stream):
    ''' Need to configure palettes manually, since we are checking stderr. '''
    # doing this manually because we're using std-error, may be other reasons
    is_tty = is_a_tty(stream)

    try:  # avoid install issue with new pip:2024 :-/
        import env
    except ModuleNotFoundError as err:
        print(str(err))

    # detection is performed if not explicitly disabled
    if is_tty and (
        env.PY_CONSOLE_AUTODETECT.value is None or
        env.PY_CONSOLE_AUTODETECT.truthy
    ):
        level = init(_stream=stream)
        fg = ForegroundPalette(level=level)
        bg = BackgroundPalette(level=level)
        fx = EffectsPalette(level=level)

    else:
        from console.constants import TermLevel
        from console.disabled import empty_bin as _empty_bin

        # Define pass-thru palette objects for streams and dumb terminals:
        level = TermLevel.DUMB
        fg = bg = fx = _empty_bin

    return fg, bg, fx, level, is_tty


TermLevel, is_fbterm, os_name  # quiet pyflakes
