import os

import jinja2

template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)


def write(response, *a, **kw):
    response.out.write(*a, **kw)

def render_str(template, **params):
    template = jinja_env.get_template(template)
    return template.render(params)

def render(response, template, **kw):
    write(response, render_str(template, **kw))