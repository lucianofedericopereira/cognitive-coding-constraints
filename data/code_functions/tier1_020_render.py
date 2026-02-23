# Source : https://github.com/tornadoweb/tornado/blob/master/tornado/web.py (line 3466)
# License: Apache-2.0
# Complexity: 1
# Tier   : tier1

def render(self) -> str:
    return self.handler.xsrf_form_html()