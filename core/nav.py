def nav(
    url_name='',
    name='',
    icon='',
    color=''
):
    data = {
        'path': url_name,
        'name': name,
        'icon': icon,
    }
    if color:
        data['color'] = color
    return data