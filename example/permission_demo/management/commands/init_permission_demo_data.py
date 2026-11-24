from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from permission_demo.models import DemoOrder


ROWS = [
    ('示例订单-全局', 'demo_global', '5000.00', '1200.00'),
    ('示例订单-华东', 'demo_region', '9000.00', '2200.00'),
    ('示例订单-华东一组', 'demo_team', '16000.00', '4000.00'),
]


class Command(BaseCommand):
    help = '初始化 permission_demo 示例订单数据'

    def handle(self, *args, **options):
        User = get_user_model()
        owner, _ = User.objects.get_or_create(
            username='demo_manager_user',
            defaults={'email': 'demo_manager_user@example.com', 'is_staff': True},
        )
        created = 0
        for title, department, amount, cost in ROWS:
            _, is_new = DemoOrder.objects.update_or_create(
                title=title,
                defaults={
                    'owner': owner,
                    'department': department,
                    'amount': amount,
                    'cost': cost,
                    'status': 'pending',
                },
            )
            created += int(is_new)
        self.stdout.write(self.style.SUCCESS('permission_demo 示例数据完成，新建 %s 条' % created))
