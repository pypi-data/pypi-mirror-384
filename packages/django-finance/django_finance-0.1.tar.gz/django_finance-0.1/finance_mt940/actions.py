from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from .forms import UploadMt940FileForm
from .mt940 import process_mt940_file
from .mt940 import InvalidMT940FileError


def upload_mt940_file(modeladmin, request, queryset):
    # We only work with one single order account.
    if len(queryset) > 1:
        msg = 'You cannot upload your mt940 file for more than one order account.'
        modeladmin.message_user(request, msg, messages.ERROR)
        return HttpResponseRedirect(reverse('admin:finance_orderaccount_changelist'))

    # Check if we are coming from the form or not.
    if 'upload_mt940_file' in request.POST:
        upload_form = UploadMt940FileForm(request.POST, request.FILES)
    else:
        upload_form = UploadMt940FileForm()

    # Process the form.
    if upload_form.is_valid():
        try:
            created, found = process_mt940_file(queryset.first(), request.FILES['mt940_file'])
        except InvalidMT940FileError as exc:
            modeladmin.message_user(request, str(exc), messages.ERROR)
            return render(request, 'finance_mt940/upload_mt940_file.html', context)
        else:
            if created:
                msg = f'Successfully created {len(created)} bankstatements.'
                modeladmin.message_user(request, msg, messages.INFO)
            if found:
                msg = f'{len(found)} bankstatements already exists.'
                modeladmin.message_user(request, msg, messages.INFO)
            return HttpResponseRedirect(reverse('admin:finance_orderaccount_changelist'))

    # Or render it.
    else:
        # context = modeladmin.admin_site.each_context(request)
        context = dict(upload_form=upload_form, objects=queryset)
        return render(request, 'finance_mt940/upload_mt940_file.html', context)
