# Source : https://github.com/Textualize/rich/blob/master/rich/console.py (line 625)
# License: MIT
# Complexity: 32
# Tier   : tier4

def __init__(
    self,
    *,
    color_system: Optional[
        Literal["auto", "standard", "256", "truecolor", "windows"]
    ] = "auto",
    force_terminal: Optional[bool] = None,
    force_jupyter: Optional[bool] = None,
    force_interactive: Optional[bool] = None,
    soft_wrap: bool = False,
    theme: Optional[Theme] = None,
    stderr: bool = False,
    file: Optional[IO[str]] = None,
    quiet: bool = False,
    width: Optional[int] = None,
    height: Optional[int] = None,
    style: Optional[StyleType] = None,
    no_color: Optional[bool] = None,
    tab_size: int = 8,
    record: bool = False,
    markup: bool = True,
    emoji: bool = True,
    emoji_variant: Optional[EmojiVariant] = None,
    highlight: bool = True,
    log_time: bool = True,
    log_path: bool = True,
    log_time_format: Union[str, FormatTimeCallable] = "[%X]",
    highlighter: Optional["HighlighterType"] = ReprHighlighter(),
    legacy_windows: Optional[bool] = None,
    safe_box: bool = True,
    get_datetime: Optional[Callable[[], datetime]] = None,
    get_time: Optional[Callable[[], float]] = None,
    _environ: Optional[Mapping[str, str]] = None,
):
    # Copy of os.environ allows us to replace it for testing
    if _environ is not None:
        self._environ = _environ

    self.is_jupyter = _is_jupyter() if force_jupyter is None else force_jupyter
    if self.is_jupyter:
        if width is None:
            jupyter_columns = self._environ.get("JUPYTER_COLUMNS")
            if jupyter_columns is not None and jupyter_columns.isdigit():
                width = int(jupyter_columns)
            else:
                width = JUPYTER_DEFAULT_COLUMNS
        if height is None:
            jupyter_lines = self._environ.get("JUPYTER_LINES")
            if jupyter_lines is not None and jupyter_lines.isdigit():
                height = int(jupyter_lines)
            else:
                height = JUPYTER_DEFAULT_LINES

    self.tab_size = tab_size
    self.record = record
    self._markup = markup
    self._emoji = emoji
    self._emoji_variant: Optional[EmojiVariant] = emoji_variant
    self._highlight = highlight
    self.legacy_windows: bool = (
        (detect_legacy_windows() and not self.is_jupyter)
        if legacy_windows is None
        else legacy_windows
    )

    if width is None:
        columns = self._environ.get("COLUMNS")
        if columns is not None and columns.isdigit():
            width = int(columns) - self.legacy_windows
    if height is None:
        lines = self._environ.get("LINES")
        if lines is not None and lines.isdigit():
            height = int(lines)

    self.soft_wrap = soft_wrap
    self._width = width
    self._height = height

    self._color_system: Optional[ColorSystem]

    self._force_terminal = None
    if force_terminal is not None:
        self._force_terminal = force_terminal

    self._file = file
    self.quiet = quiet
    self.stderr = stderr

    if color_system is None:
        self._color_system = None
    elif color_system == "auto":
        self._color_system = self._detect_color_system()
    else:
        self._color_system = COLOR_SYSTEMS[color_system]

    self._lock = threading.RLock()
    self._log_render = LogRender(
        show_time=log_time,
        show_path=log_path,
        time_format=log_time_format,
    )
    self.highlighter: HighlighterType = highlighter or _null_highlighter
    self.safe_box = safe_box
    self.get_datetime = get_datetime or datetime.now
    self.get_time = get_time or monotonic
    self.style = style
    self.no_color = (
        no_color
        if no_color is not None
        else self._environ.get("NO_COLOR", "") != ""
    )
    if force_interactive is None:
        tty_interactive = self._environ.get("TTY_INTERACTIVE", None)
        if tty_interactive is not None:
            if tty_interactive == "0":
                force_interactive = False
            elif tty_interactive == "1":
                force_interactive = True

    self.is_interactive = (
        (self.is_terminal and not self.is_dumb_terminal)
        if force_interactive is None
        else force_interactive
    )

    self._record_buffer_lock = threading.RLock()
    self._thread_locals = ConsoleThreadLocals(
        theme_stack=ThemeStack(themes.DEFAULT if theme is None else theme)
    )
    self._record_buffer: List[Segment] = []
    self._render_hooks: List[RenderHook] = []
    self._live_stack: List[Live] = []
    self._is_alt_screen = False