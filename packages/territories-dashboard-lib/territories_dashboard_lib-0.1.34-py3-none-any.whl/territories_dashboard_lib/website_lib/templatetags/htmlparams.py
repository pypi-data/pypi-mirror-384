from django import template

register = template.Library()

"""
This tag is used to give some html as argument to an {% include %} tag.

For instance:

{% htmlparams %}
    {% htmlparam content %}
        <span>click me</span>
    {% endhtmlparam %}
    {% include "website/components/button.html"%}
{% endhtmlparams %}

you have to wrap {% include %} within {% htmlparams %} then you can add {% htmlparam VARIABLE_NAME %} with some html within and use the variable within the component.

Included button:

<button>
    {{ content }}
</button>

"""


class HtmlParamNode(template.Node):
    def __init__(self, var_name, nodelist):
        self.var_name = var_name
        self.nodelist = nodelist

    def render(self, context):
        # do not render anything but stores the output in the context
        output = self.nodelist.render(context)
        context[self.var_name] = output
        return ""


class HtmlParamsNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = template.NodeList()
        self.paramnodelist = template.NodeList()
        for node in nodelist:
            if isinstance(node, HtmlParamNode):
                self.paramnodelist.append(node)
            else:
                self.nodelist.append(node)

    def render(self, context):
        with context.push():
            ## Render the htmlparam nodes to update the context
            self.paramnodelist.render(context)
            output = self.nodelist.render(context)
        return output


@register.tag(name="htmlparam")
def do_htmlparam(parser, token):
    try:
        tag_name, var_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        )
    nodelist = parser.parse(("endhtmlparam",))
    parser.delete_first_token()
    return HtmlParamNode(var_name, nodelist)


@register.tag(name="htmlparams")
def do_htmlparams(parser, token):
    nodelist = parser.parse(("endhtmlparams",))
    parser.delete_first_token()
    return HtmlParamsNode(nodelist)
