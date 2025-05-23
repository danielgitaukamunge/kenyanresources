from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Post
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = 'blog/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Home'  # This will be used in your template
        return context

def blog_home(request):
    post_list = Post.objects.all().order_by('-date_posted')
    paginator = Paginator(post_list, 2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/blog_home.html', {'page_obj': page_obj})

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    return render(request, 'blog/post_detail.html', {'post': post})

def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})