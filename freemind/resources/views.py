from django.shortcuts import render, get_object_or_404
from .models import Resource
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

def resource_content(request):
    resource_list = Resource.objects.all().order_by('-created_at')
    paginator = Paginator(resource_list, 2)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
        
    return render(request, 'resources/resource_content.html', {
        'page_obj': page_obj,  # Changed from 'resources' to 'page_obj'
        'is_paginated': page_obj.has_other_pages()  # Helpful for template
    })

def resource_search(request):
    query = request.GET.get('q', '').strip()
    resource_list = Resource.objects.all()
    
    if query:
        resource_list = resource_list.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(categories__icontains=query)
        )
    
    resource_list = resource_list.order_by('-created_at')
    paginator = Paginator(resource_list, 6)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
        
    return render(request, 'resources/resource_content.html', {
        'page_obj': page_obj,
        'query': query,
        'is_paginated': page_obj.has_other_pages()
    })

def resource_detail(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    return render(request, 'resources/resource_details.html', {
        'resource': resource
    })

def resource_filter(request, category):
    resource_list = Resource.objects.filter(
        categories__icontains=category
    ).order_by('-created_at')
    
    paginator = Paginator(resource_list, 6)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
        
    return render(request, 'resources/resource_content.html', {
        'page_obj': page_obj,
        'category': category,
        'is_paginated': page_obj.has_other_pages()
    })