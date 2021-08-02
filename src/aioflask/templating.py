from flask.templating import *
from flask.templating import _app_ctx_stack, before_render_template, \
    template_rendered


async def _render(template, context, app):
    """Renders the template and fires the signal"""

    before_render_template.send(app, template=template, context=context)
    rv = await template.render_async(context)
    template_rendered.send(app, template=template, context=context)
    return rv


async def render_template(template_name_or_list, **context):
    """Renders a template from the template folder with the given
    context.
    :param template_name_or_list: the name of the template to be
                                  rendered, or an iterable with template names
                                  the first one existing will be rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    ctx = _app_ctx_stack.top
    ctx.app.update_template_context(context)
    return await _render(
        ctx.app.jinja_env.get_or_select_template(template_name_or_list),
        context,
        ctx.app,
    )


async def render_template_string(source, **context):
    """Renders a template from the given template source string
    with the given context. Template variables will be autoescaped.
    :param source: the source code of the template to be
                   rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    ctx = _app_ctx_stack.top
    ctx.app.update_template_context(context)
    return await _render(ctx.app.jinja_env.from_string(source), context,
                         ctx.app)
