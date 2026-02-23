# Source : https://github.com/tornadoweb/tornado/blob/master/tornado/web.py (line 1087)
# License: Apache-2.0
# Complexity: 1
# Tier   : tier1

def render_embed_js(self, js_embed: Iterable[bytes]) -> bytes:
    """Default method used to render the final embedded js for the
    rendered webpage.

    Override this method in a sub-classed controller to change the output.
    """
    return (
        b'<script type="text/javascript">\n//<![CDATA[\n'
        + b"\n".join(js_embed)
        + b"\n//]]>\n</script>"
    )