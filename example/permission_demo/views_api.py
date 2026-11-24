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

    try:
        page = max(1, int(request.GET.get('page') or 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.GET.get('page_size') or 10)
    except (TypeError, ValueError):
        page_size = 10
    page_size = min(max(page_size, 1), 100)

    total = queryset.count()
    start = (page - 1) * page_size
    queryset = queryset[start:start + page_size]

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

    return JsonResponse({
        'code': 200,
        'data': rows,
        'fields': visible_fields,
        'count': total,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size,
    })
