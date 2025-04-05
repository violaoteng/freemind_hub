from django.shortcuts import render, get_object_or_404
from .models import Resource

# Create your views here.
def resource_content(request):
    resources = Resource.objects.all()
    return render(request, 'resources/resource_content.html', {'resources':resources})

# View to show details of a single resource
def resource_detail(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    return render(request, 'resources/resource_detail.html', {'resource': resource})

# View to filter resources by category or type
def resource_filter(request, category):
    resources = Resource.objects.filter(categories=category)
    return render(request, 'resources/resource_list.html', {'resources': resources})

from django.db.models import Q

def resource_search(request):
    query = request.GET.get('q')
    if query:
        resources = Resource.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(categories__icontains=query)
        )
    else:
        resources = Resource.objects.all()
    return render(request, 'resources/resource_list.html', {'resources': resources})

