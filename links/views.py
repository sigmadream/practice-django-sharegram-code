from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .forms import LinkForm
from .models import Link
from .utils import fetch_og_metadata

def link_list(request):
    links = Link.objects.all()
    return render(request, 'links/link_list.html', {'links': links})

def link_detail(request, pk):
    link = get_object_or_404(Link, pk=pk)
    return render(request, 'links/link_detail.html', {'link': link})

@login_required
def link_create(request):
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.user = request.user
            metadata = fetch_og_metadata(link.url)
            link.title = metadata['title']
            link.description = metadata['description']
            link.og_image = metadata['image']
            link.save()
            messages.success(request, '링크가 추가되었습니다.')
            return redirect('links:link_detail', pk=link.pk)
    else:
        form = LinkForm()
    return render(request, 'links/link_create.html', {'form': form})

@login_required
def link_delete(request, pk):
    link = get_object_or_404(Link, pk=pk)
    if link.user != request.user:
        messages.error(request, '삭제 권한이 없습니다.')
        return redirect('links:link_list')
    if request.method == 'POST':
        link.delete()
        messages.success(request, '링크가 삭제되었습니다.')
        return redirect('links:link_list')
    return render(request, 'links/link_confirm_delete.html', {'link': link})
