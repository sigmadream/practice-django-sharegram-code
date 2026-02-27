import random
import uuid
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from PIL import Image
from .forms import PostForm, CommentForm
from users.models import User
from .models import Post, Comment, Like, Follow


def generate_random_image():
    """랜덤 컬러의 400x400 이미지를 생성합니다."""
    color = (random.randint(50, 220), random.randint(
        50, 220), random.randint(50, 220))
    img = Image.new('RGB', (400, 400), color)
    for i in range(0, 400, 40):
        lighter = tuple(min(c + 30, 255) for c in color)
        for x in range(i, min(i + 20, 400)):
            for y in range(400):
                img.putpixel((x, y), lighter)
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=85)
    buf.seek(0)
    filename = f'random_{random.randint(10000, 99999)}.jpg'
    return filename, ContentFile(buf.read())


def home(request):
    """비로그인: Welcome 페이지, 로그인: 홈 피드"""
    if not request.user.is_authenticated:
        return render(request, 'posts/welcome.html')

    posts = Post.objects.all()
    paginator = Paginator(posts, 5)
    page_obj = paginator.get_page(1)
    # recent_links = Link.objects.all()[:3]
    # context = {'posts': page_obj, 'recent_links': recent_links}
    context = {'posts': page_obj}
    return render(request, 'posts/home.html', context)


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    Post.objects.filter(pk=pk).update(views=post.views + 1)
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            messages.success(request, '댓글이 작성되었습니다.')
            return redirect('posts:post_detail', pk=pk)
    else:
        comment_form = CommentForm()
    is_liked = False
    if request.user.is_authenticated:
        is_liked = Like.objects.filter(user=request.user, post=post).exists()
    is_following = False
    if request.user.is_authenticated and request.user != post.user:
        is_following = Follow.objects.filter(follower=request.user, following=post.user).exists()
    prev_post = Post.objects.filter(
        created_at__gt=post.created_at).order_by('created_at').first()
    next_post = Post.objects.filter(
        created_at__lt=post.created_at).order_by('-created_at').first()
    context = {
        'post': post,
        'comment_form': comment_form,
        'is_liked': is_liked,
        'like_count': post.likes.count(),
        'is_following': is_following,
        'prev_post': prev_post,
        'next_post': next_post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        # 중복 제출 방지: nonce 검증
        submitted_nonce = request.POST.get('form_nonce', '')
        session_nonce = request.session.pop('post_create_nonce', None)
        if not submitted_nonce or submitted_nonce != session_nonce:
            messages.warning(request, '이미 처리된 요청입니다.')
            return redirect('posts:home')

        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            if not post.image and request.POST.get('use_random_image'):
                filename, content = generate_random_image()
                post.image.save(filename, content, save=False)
            post.save()
            messages.success(request, '게시물이 작성되었습니다.')
            return redirect('posts:home')
    else:
        form = PostForm()

    nonce = str(uuid.uuid4())
    request.session['post_create_nonce'] = nonce
    return render(request, 'posts/post_form.html', {'form': form, 'title': '새 게시물', 'form_nonce': nonce})


@login_required
def post_update(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.user != request.user:
        messages.error(request, '수정 권한이 없습니다.')
        return redirect('posts:home')
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, '게시물이 수정되었습니다.')
            return redirect('posts:post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'posts/post_form.html', {'form': form, 'title': '게시물 수정'})


@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.user != request.user:
        messages.error(request, '삭제 권한이 없습니다.')
        return redirect('posts:home')
    if request.method == 'POST':
        post.delete()
        messages.success(request, '게시물이 삭제되었습니다.')
        return redirect('posts:home')
    return render(request, 'posts/post_confirm_delete.html', {'post': post})

@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.user != request.user:
        messages.error(request, '삭제 권한이 없습니다.')
        return redirect('posts:post_detail', pk=comment.post.pk)
    if request.method == 'POST':
        post_pk = comment.post.pk
        comment.delete()
        messages.success(request, '댓글이 삭제되었습니다.')
        return redirect('posts:post_detail', pk=post_pk)
    return render(request, 'posts/comment_confirm_delete.html', {'comment': comment})


def load_more_posts(request):
    page_number = request.GET.get('page', 1)
    feed_type = request.GET.get('feed', 'home')
    posts = Post.objects.all()
    paginator = Paginator(posts, 5)

    # get_page()는 범위 초과 시 마지막 페이지를 반환하여 중복 표시 발생
    # paginator.page()를 사용하여 범위 초과 시 빈 응답 반환
    try:
        page_obj = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        return JsonResponse({'html': '', 'has_next': False})

    html = render_to_string('posts/includes/post_card.html',
                            {'posts': page_obj}, request=request)
    return JsonResponse({'html': html, 'has_next': page_obj.has_next()})

@login_required
@require_POST
def like_toggle(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    like_count = post.likes.count()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'like_count': like_count})
    return redirect('posts:post_detail', pk=pk)


@login_required
def follow_toggle(request, username):
    target_user = get_object_or_404(User, username=username)
    if request.user == target_user:
        messages.warning(request, '자기 자신을 팔로우할 수 없습니다.')
        return redirect('users:profile', username=username)
    follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)
    if not created:
        follow.delete()
        messages.info(request, f'{target_user.username}님을 언팔로우했습니다.')
    else:
        messages.success(request, f'{target_user.username}님을 팔로우합니다.')
    return redirect('users:profile', username=username)

@login_required
def following_feed(request):
    following_users = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    posts = Post.objects.filter(Q(user_id__in=following_users) | Q(user=request.user))
    paginator = Paginator(posts, 5)
    page_obj = paginator.get_page(1)
    liked_post_ids = set(Like.objects.filter(user=request.user, post__in=page_obj.object_list).values_list('post_id', flat=True))
    for post in page_obj:
        post.is_liked = post.pk in liked_post_ids
    context = {'posts': page_obj}
    return render(request, 'posts/following_feed.html', context)
