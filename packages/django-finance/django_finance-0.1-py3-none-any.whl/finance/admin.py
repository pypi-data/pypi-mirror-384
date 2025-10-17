from django.contrib import admin
from searchkit.filters import SearchkitFilter
from finance_mt940.actions import upload_mt940_file
from searchkit.models import Search
from searchkit.admin import SearchkitSearchAdmin as OriginalSearchkitSearchAdmin
from .forms import SearchForm
from .models import OrderAccount
from .models import BankStatement


@admin.register(OrderAccount)
class OrderAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'iban', 'bic']
    list_filter = ['name', 'iban', 'bic']
    actions = [upload_mt940_file]


@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):
    list_select_related = True
    date_hierarchy = 'entry_date'
    list_display = [
        'amount',
        'currency',
        'order_account',
        'applicant_name',
        'applicant_iban',
        'posting_text',
        'entry_date',
        ]
    list_filter = [
        SearchkitFilter,
        'entry_date',
        'posting_text',
        'applicant_name',
        ]

    def has_change_permission(self, request, obj=None):
        return False


# Unregister the original Search admin.
admin.site.unregister(Search)

# Register a new Search admin using our customized SearchForm.
@admin.register(Search)
class SearchkitSearchAdmin(OriginalSearchkitSearchAdmin):
    form = SearchForm
