# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/config/__init__.py (line 1485)
# License: MIT
# Complexity: 14
# Tier   : tier3

def parse(self, args: list[str], addopts: bool = True) -> None:
    # Parse given cmdline arguments into this config object.
    assert self.args == [], (
        "can only parse cmdline args at most once per Config object"
    )

    self.hook.pytest_addhooks.call_historic(
        kwargs=dict(pluginmanager=self.pluginmanager)
    )

    if addopts:
        env_addopts = os.environ.get("PYTEST_ADDOPTS", "")
        if len(env_addopts):
            args[:] = (
                self._validate_args(shlex.split(env_addopts), "via PYTEST_ADDOPTS")
                + args
            )

    ns = self._parser.parse_known_args(args, namespace=copy.copy(self.option))
    rootpath, inipath, inicfg, ignored_config_files = determine_setup(
        inifile=ns.inifilename,
        override_ini=ns.override_ini,
        args=ns.file_or_dir,
        rootdir_cmd_arg=ns.rootdir or None,
        invocation_dir=self.invocation_params.dir,
    )
    self._rootpath = rootpath
    self._inipath = inipath
    self._ignored_config_files = ignored_config_files
    self._inicfg = inicfg
    self._parser.extra_info["rootdir"] = str(self.rootpath)
    self._parser.extra_info["inifile"] = str(self.inipath)

    self._parser.addini("addopts", "Extra command line options", "args")
    self._parser.addini("minversion", "Minimally required pytest version")
    self._parser.addini(
        "pythonpath", type="paths", help="Add paths to sys.path", default=[]
    )
    self._parser.addini(
        "required_plugins",
        "Plugins that must be present for pytest to run",
        type="args",
        default=[],
    )

    if addopts:
        args[:] = (
            self._validate_args(self.getini("addopts"), "via addopts config") + args
        )

    self.known_args_namespace = self._parser.parse_known_args(
        args, namespace=copy.copy(self.option)
    )
    self._checkversion()
    self._consider_importhook()
    self._configure_python_path()
    self.pluginmanager.consider_preparse(args, exclude_only=False)
    if (
        not os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD")
        and not self.known_args_namespace.disable_plugin_autoload
    ):
        # Autoloading from distribution package entry point has
        # not been disabled.
        self.pluginmanager.load_setuptools_entrypoints("pytest11")
    # Otherwise only plugins explicitly specified in PYTEST_PLUGINS
    # are going to be loaded.
    self.pluginmanager.consider_env()

    self._parser.parse_known_args(args, namespace=self.known_args_namespace)

    self._validate_plugins()
    self._warn_about_skipped_plugins()

    if self.known_args_namespace.confcutdir is None:
        if self.inipath is not None:
            confcutdir = str(self.inipath.parent)
        else:
            confcutdir = str(self.rootpath)
        self.known_args_namespace.confcutdir = confcutdir
    try:
        self.hook.pytest_load_initial_conftests(
            early_config=self, args=args, parser=self._parser
        )
    except ConftestImportFailure as e:
        if self.known_args_namespace.help or self.known_args_namespace.version:
            # we don't want to prevent --help/--version to work
            # so just let it pass and print a warning at the end
            self.issue_config_time_warning(
                PytestConfigWarning(f"could not load initial conftests: {e.path}"),
                stacklevel=2,
            )
        else:
            raise

    try:
        self._parser.parse(args, namespace=self.option)
    except PrintHelp:
        return

    self.args, self.args_source = self._decide_args(
        args=getattr(self.option, FILE_OR_DIR),
        pyargs=self.option.pyargs,
        testpaths=self.getini("testpaths"),
        invocation_dir=self.invocation_params.dir,
        rootpath=self.rootpath,
        warn=True,
    )