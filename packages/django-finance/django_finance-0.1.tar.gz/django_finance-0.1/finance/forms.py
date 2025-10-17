from searchkit.forms import SearchkitModelForm as OriginalSearchkitModelForm
from searchkit.forms import SearchForm as OriginalSearchForm


class SearchkitModelForm(OriginalSearchkitModelForm):
    """
    Use a hidden searchkit_model field.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = self.fields['searchkit_model'].queryset.filter(model='bankstatement')
        self.fields['searchkit_model'].queryset = queryset
        self.fields['searchkit_model'].empty_label = None


class SearchForm(OriginalSearchForm):
    """
    A SearchForm working only on BankStatement.
    """
    searchkit_model_form_class = SearchkitModelForm
