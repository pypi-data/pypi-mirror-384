from django import template
from django.db.models import Sum
from finance.models import BankStatement

register = template.Library()

@register.inclusion_tag('finance/bank_statement_sum.html', takes_context=True)
def bank_statement_sum(context):
    changelist = context.get('cl')
    queryset = changelist.queryset if changelist else BankStatement.objects.none()
    sum = queryset.aggregate(sum=Sum('amount'))['sum'] or 0
    return {
        'sum': f'{sum:.2f}',
        'count': queryset.count(),
    }
