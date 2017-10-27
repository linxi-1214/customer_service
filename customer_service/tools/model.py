def updated_fields(origin_obj, form_data, key_list, key_map={}):
    update_fields = []
    for key in key_list:
        key_map[key] = key

    for field_name, form_name in key_map.items():
        field_value = getattr(origin_obj, field_name)
        form_value = form_data.get(form_name)

        if field_value != form_value:
            update_fields.append(field_name)

    return update_fields


def set_operator(obj, user):
    setattr(obj, 'operator', user)


def get_operator(obj):
    return getattr(obj, 'operator')
