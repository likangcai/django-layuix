from django.http import JsonResponse

from django_layuix.rbac.abac import filter_fields, filter_queryset
from django_layuix.rbac.permissions import api_permission_required, resolve_api_user

from .models import DemoOrder

VIEW_FIELDS = ['id', 'title', 'owner_name', 'department', 'amount', 'cost', 'status']


@api_permission_required('demo:order:view')
def order_list(request):
    user = resolve_api_user(request)
    resource = 'permission_demo.DemoOrder'

    scoped_queryset = DemoOrder.objects.for_user(user).select_related('owner')
    queryset = filter_queryset(scoped_queryset, user, 'view', resource)
    visible_fields = filter_fields(user, 'view', resource, VIEW_FIELDS)

    rows = []
    for order in queryset:
        values = {
            'id': order.id,
            'title': order.title,
            'owner_name': order.owner.username if order.owner else '',
            'department': order.department,
            'amount': str(order.amount),
            'cost': str(order.cost),
            'status': order.status,
        }
        rows.append({key: values[key] for key in visible_fields})

    return JsonResponse({'code': 200, 'data': rows, 'fields': visible_fields, 'count': len(rows)})
