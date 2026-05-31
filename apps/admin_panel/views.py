from django.shortcuts import render


def admin_placeholder(request):
    return render(request, 'admin_panel/placeholder.html', {'seccion': 'Panel Admin'})


def superadmin_placeholder(request):
    return render(request, 'admin_panel/placeholder.html', {'seccion': 'Panel Superadmin'})
