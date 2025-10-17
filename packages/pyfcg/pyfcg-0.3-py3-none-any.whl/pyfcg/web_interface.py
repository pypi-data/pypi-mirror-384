import pyfcg as fcg
import json

def add_element_to_web_interface (html):
    """Adds an HTML element to the Babel web interface."""
    fcg.routes.add_element(html)

def render_image_in_web_interface(list):
    canvas_id = fcg.routes.gensym("c")
    add_element_to_web_interface('<canvas class="matrix-image" id="' + canvas_id + '"></canvas>')
    add_element_to_web_interface('<script>drawArrayAsImage(' + json.dumps(list) + ',"' + canvas_id + '")</script>')
