from django.contrib import admin
from customer_service.models import User, Menu, Role, RoleBindMenu

# Register your models here.

admin.site.register(User)
admin.site.register(Menu)
admin.site.register(Role)
admin.site.register(RoleBindMenu)
