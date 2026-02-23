# Source : https://github.com/pytest-dev/pytest/blob/main/src/_pytest/python.py (line 563)
# License: MIT
# Complexity: 1
# Tier   : tier1

def collect(self) -> Iterable[nodes.Item | nodes.Collector]:
    self._register_setup_module_fixture()
    self._register_setup_function_fixture()
    self.session._fixturemanager.parsefactories(self)
    return super().collect()