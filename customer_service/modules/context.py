from django.core.urlresolvers import reverse, NoReverseMatch

from django.db import connection

from collections import namedtuple


def namedtuplefetchall(cursor):
    """Return all rows from a cursor as a namedtuple"""
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


panel_themes = [
    "panel-primary", "panel-green", "panel-yellow", "panel-red"
]


class Context:

    @staticmethod
    def get_url(view_name):
        try:
            url = reverse(view_name)
        except NoReverseMatch:
            url = view_name

        return url

    @staticmethod
    def menus(user):
        select_sql = """
            SELECT
                menu.id,
                menu.label,
                menu.name AS view_name,
                menu.icon
            FROM menu
                INNER JOIN role_bind_menu ON role_bind_menu.menu_id = menu.id
                INNER JOIN customer_service_user ON customer_service_user.role_id = role_bind_menu.role_id
            WHERE customer_service_user.id = %s AND menu.parent = %s
            ORDER BY menu.order_index, menu.id ASC
        """

        _index = 0
        theme_length = len(panel_themes)
        with connection.cursor() as cursor:
            cursor.execute(select_sql, (user.id, 0))
            qry_set = namedtuplefetchall(cursor)
            menus = [
                {
                    "id": _menu.id,
                    "label": _menu.label,
                    "href": Context.get_url(_menu.view_name),
                    "icon": _menu.icon,
                    "number": index,
                    "theme": panel_themes[index % theme_length]
                } for index, _menu in enumerate(qry_set, start=_index)
            ]

        with connection.cursor() as cursor:
            for menu in menus:
                cursor.execute(select_sql, (user.id, menu['id']))
                qry_set = namedtuplefetchall(cursor)
                secondmenus = [
                    {
                        "id": sm.id,
                        "label": sm.label,
                        "href": Context.get_url(sm.view_name),
                        "icon": sm.icon,
                        "number": ind,
                        "theme": panel_themes[ind % theme_length]
                    } for ind, sm in enumerate(qry_set, start=_index)
                ]
                menu.update(submenu=secondmenus)

                for submenu in secondmenus:
                    cursor.execute(select_sql, (user.id, submenu['id'],))
                    qry_set = namedtuplefetchall(cursor)

                    thirdmenus = [
                        {
                            "id": sm.id,
                            "label": sm.label,
                            "href": Context.get_url(sm.view_name),
                            "icon": sm.icon,
                            "number": ind,
                            "theme": panel_themes[ind % theme_length]
                        } for ind, sm in enumerate(qry_set, start=_index)
                    ]

                    submenu.update(submenu=thirdmenus)

        return menus
