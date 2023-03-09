from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.cache import cache_page

from .models import Group, Post, User
from .forms import CommentForm, PostForm
from .utils import make_page


# Создание поста под авторизацией
@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
    form = PostForm()
    return render(
        request,
        'posts/create_post.html',
        {
            'form': form,
        },
    )


# Редактирование поста под авторизацией
@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
    return render(
        request,
        'posts/create_post.html',
        {'form': form, 'is_edit': True},
    )


# Главная страница
@cache_page(40, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related('group', 'author')
    return render(
        request, 'posts/index.html',
        {'page_obj': make_page(request, posts)}
    )


# Страница групп
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    return render(
        request,
        'posts/group_list.html',
        {'group': group, 'page_obj': make_page(request, posts)},
    )


# Профайл пользователя
def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.select_related('group', 'author').filter(
        author__username=username
    )
    return render(
        request,
        'posts/profile.html',
        {
            'author': author,
            'page_obj': make_page(request, posts),
        },
    )


#Отдельная запись
def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'), id=post_id
        )
    comments = post.comments.all().select_related('author')
    form = CommentForm()
    author = request.user.id
    return render(
        request,
        'posts/post_detail.html',
        {'post': post,
         'author': author,
         'form': form,
         'comments': comments,
        })

#Добавление комментариев
@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, id=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)
