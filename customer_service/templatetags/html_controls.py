import sys

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


def control_decorator(control_type):
    def wrapped_generate(generate_func):
        def wrapper(field_info):
            if field_info.get('type') != control_type:
                return ''
            wrapped_html = '<div class="form-group {group_css}">\n'
            if field_info.get('label') and field_info.get('type') != 'group_button':
                wrapped_html += '    <label class="col-form-label">{label}</label>\n'
            wrapped_html += generate_func(field_info)
            if field_info.get('help_text'):
                wrapped_html += '    <small id="{help_id}" class="form-text text-muted">{help_text}</small>\n'
            wrapped_html += '</div>'

            wrapped_html = wrapped_html.format(help_id=field_info.get('help_id', ''),
                                               help_text=field_info.get('help_text', ''),
                                               label=field_info.get('label', ''),
                                               group_css=field_info.get('group_css', '')
                                               )
            return mark_safe(wrapped_html)
        return wrapper

    return wrapped_generate


@register.simple_tag(name='group')
def generate_field_group(field_info):
    if field_info.get('type') != 'group':
        return ''
    _group_html = '<div class="row {group_css}" {attrs}>\n'.format(
        group_css=field_info.get('group_css', ''),
        attrs=" ".join(['%s="%s"' % attr for attr in field_info.get('attrs', {}).items()])
    )

    field_group = field_info.get('group', [])
    for field_info in field_group:
        field_type = field_info.get('type')
        generate_html_func = getattr(sys.modules[__name__], '_%s_html' % field_type)

        _control_html = generate_html_func(field_info)
        _group_html += '%s\n' % _control_html
    _group_html += '</div>'

    return mark_safe(_group_html)


@control_decorator('radio')
def _radio_html(field_info):
    _html = ""

    for radio in field_info.get('radio_group', []):
        radio_html = ""
        if field_info.get('inline'):
            radio_html += '<div class="form-check form-check-inline {extra_class}" style="{extra_style}">\n'
        else:
            radio_html += '<div class="form-check {extra_class}" style="{extra_style}">\n'
        radio_html += '    <label class="form-check-label">\n'
        radio_html += '        <input class="form-check-input" type="radio" name="{name}" id="{id}"' \
                      ' value="{value}"> {label}\n'
        radio_html += '    </label>\n'
        radio_html += '</div>\n'

        radio_html = radio_html.format(name=radio.get('name', ''),
                                       id=radio.get('id', ''),
                                       value=radio.get('value', ''),
                                       label=radio.get('label', ''),
                                       extra_class=radio.get('extra_class', ''),
                                       extra_style=radio.get('extra_style', '')
                                       )
        _html += '%s\n' % radio_html

    return _html


@register.simple_tag(name='radio')
def generate_radio(field_info):
    return _radio_html(field_info)


@control_decorator('checkbox')
def _checkbox_html(field_info):
    _html = ""
    for checkbox in field_info.get('checkbox_group', []):
        checkbox_html = ""
        if field_info.get('inline', False):
            checkbox_html += '<div class="form-check form-check-inline {extra_class}" style="{extra_style}">\n'
        else:
            checkbox_html += '<div class="form-check {extra_class}" style="{extra_style}">\n'
        checkbox_html += '    <label class="form-check-label">\n'
        checkbox_html += '        <input class="form-check-input" value="{value}" type="checkbox" name="{name}"' \
                         ' id="{id}" {checked}> {label}\n'
        checkbox_html += '    </label>\n'
        checkbox_html += '</div>\n'

        checkbox_html = checkbox_html.format(name=checkbox.get('name', ''),
                                             id=checkbox.get('id', ''),
                                             checked="checked" if checkbox.get('checked') else '',
                                             label=checkbox.get('label', ''),
                                             value=checkbox.get('value', 1),
                                             extra_class=checkbox.get('extra_class', ''),
                                             extra_style=checkbox.get('extra_style', '')
                                             )
        _html += '%s\n' % checkbox_html

    return _html


@register.simple_tag(name='checkbox')
def generate_checkbox(field_info):
    return _checkbox_html(field_info)


@control_decorator('file')
def _file_html(field_info):
    _html = """
        <label class="custom-file">
            <input type="file" id="{id}" name="{name}" class="custom-file-input" {disabled}/>
            <span class="custom-file-control"></span>
        </label>
        """.format(id=field_info.get('id', ''), name=field_info.get('name', ''),
                   disabled=field_info.get('disabled', ''))

    return _html


@register.simple_tag(name='file_upload')
def generate_file_upload(field_info):
    return _file_html(field_info)


@control_decorator('multi_select')
def _multi_select_html(field_info):
    _html = '<select multiple class="form-control{extra_class}" {extra_style} id="{id}" name="{name}" {disabled}>\n'.format(
        id=field_info.get('id', ''), name=field_info.get('name', ''),
        extra_class=" %s" % field_info.get('extra_css') if field_info.get('extra_css') else '',
        extra_style='style={%s}' % field_info.get('extra_style') if field_info.get('extra_style') else '',
        disabled=field_info.get('disabled', '')
    )
    for option in field_info.get('options'):
        _html += '    <option value="{value}" {selected}>{label}</option>\n'.format(
            value=option.get('value', ''),
            selected='selected="selected"' if option.get('selected') else '',
            label=option.get('label', '')
        )
    _html += '</select>\n'

    return _html


@register.simple_tag(name='multi_select')
def generate_multi_select(field_info):
    return _multi_select_html(field_info)


@control_decorator('select')
def _select_html(field_info):
    _html = '<select class="form-control{extra_class}" {extra_style} id="{id}" name="{name}" {disabled}>\n'.format(
        id=field_info.get('id', ''), name=field_info.get('name', ''),
        extra_class=" %s" % field_info.get('extra_css') if field_info.get('extra_css') else '',
        extra_style='style={%s}' % field_info.get('extra_style') if field_info.get('extra_style') else '',
        disabled=field_info.get('disabled', '')
    )
    _html += '    <option></option>\n'
    for option in field_info.get('options'):
        _html += '    <option value="{value}" {selected}>{label}</option>\n'.format(
            value=option.get('value', ''),
            selected='selected="selected"' if option.get('selected') else '',
            label=option.get('label', '')
        )
    _html += '</select>\n'

    return _html


@register.simple_tag(name='select')
def generate_select(field_info):
    return _select_html(field_info)


@control_decorator('password')
def _password_html(field_info):
    _html = '<input type="password" class="form-control" name="{name}" id="{id}" placeholder="Password" />\n'.format(
        name=field_info.get('name', ''), id=field_info.get('id', '')
    )

    return _html


@register.simple_tag(name='password')
def generate_password(field_info):
    return _password_html(field_info)


@control_decorator('text')
def _text_html(field_info):
    _html = '<input type="text" class="form-control" id="{id}" placeholder="{placeholder}" name="{name}"' \
            ' aria-describedby="{help_id}" value="{value}" {disabled}>'.format(
        id=field_info.get('id', ''), placeholder=field_info.get('placeholder', ''),
        name=field_info.get('name', ''), help_id=field_info.get('help_id', ''), value=field_info.get('value', ''),
        disabled=field_info.get('disabled', '')
    )

    return _html


@register.simple_tag(name='text')
def generate_text(field_info):
    return _text_html(field_info)


def _button_html(field_info):
    if field_info.get('type') != "button":
        return ''
    _html = '<button type="{button_type}" {click} {attrs} class="btn{extra_class}">{label}</button>'.format(
        button_type=field_info.get('button_type', 'submit'),
        click="onclick=%s" % field_info.get('click') if field_info.get('click') else '',
        extra_class=" %s" % field_info.get('extra_class', 'btn-primary'),
        label=field_info.get('label', 'Submit'),
        attrs=" ".join(['%s="%s"' % attr for attr in field_info.get('attrs', {}).items()])
    )

    return mark_safe(_html)


@control_decorator('icon_button')
def _icon_button_html(field_info):
    _html = '<button type="button" {click} class="btn {extra_class} btn-circle" ' \
            'data-toggle="tooltip" data-placement="{tooltip_position}" title={tooltip}>' \
            '<i class="fa {icon}">' \
            '</i></button>'.format(click="onclick=%s" % field_info.get('click') if field_info.get('click') else '',
                                   extra_class=field_info.get('extra_class', ''),
                                   icon=field_info.get('icon', ''),
                                   tooltip=field_info.get('tooltip'),
                                   tooltip_position=field_info.get('tooltip_position', 'bottom'))
    return _html


@control_decorator('group_button')
def _group_button_html(field_info):
    field_info['type'] = 'button'
    return _button_html(field_info)


@register.simple_tag(name="group_button")
def generate_group_button(field_info):
    return _group_button_html(field_info)


@register.simple_tag(name='button')
def generate_button(field_info):
    return _button_html(field_info)


def _submit_html(field_info):
    if field_info.get('type') != 'submit':
        return ''

    _html = '<button type="submit" class="btn btn-primary btn-sm btn-block">{label}</button>'.format(
        label=field_info.get('label', '提&nbsp;&nbsp;&nbsp;&nbsp;交')
    )

    return mark_safe(_html)


@register.simple_tag(name='submit')
def generate_submit(field_info):
    return _submit_html(field_info)


@control_decorator('textarea')
def _textarea_html(field_info):
    _html = '<textarea class="form-control" id="{id}" name="{name}" {disabled} rows="{row}"></textarea>\n'.format(
        id=field_info.get('id', ''),
        name=field_info.get('name', ''),
        disabled=field_info.get('disabled', ''),
        row=field_info.get('row', 3)
    )

    return _html


@register.simple_tag(name='textarea')
def generate_textarea(field_info):
    return _textarea_html(field_info)


if __name__ == "__main__":
    field = {
        'type': 'radio',
        'id': "star",
        'label': 'like star:',
        'help_text': 'choose as many as you like',
        'help_id': 'like_start',
        'inline': True,
        'radio_group': [
            {
                'id': 'chk1',
                'label': 'sun li',
                'value': 1,
                'name': 'name'
            },
            {
                'id': 'chk2',
                'label': 'wang jing',
                'value': 2,
                'name': 'name'
            }
        ]
    }

    chk_html = generate_radio(field)
    print(chk_html)