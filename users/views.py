# users/views.py (전체 파일)

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ProfileUpdateForm, UserRegisterForm, UserUpdateForm
# from links.models import Link
from posts.models import Follow, Like, Post


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'{username}님, 회원가입이 완료되었습니다! 로그인해주세요.')
            return redirect('users:login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    user_posts = Post.objects.filter(user=profile_user)
    # user_links = Link.objects.filter(user=profile_user)[:5]

    # if request.user.is_authenticated:
    #     liked_ids = set(Like.objects.filter(user=request.user, post__in=user_posts).values_list('post_id', flat=True))
    #     for post in user_posts:
    #         post.is_liked = post.pk in liked_ids
    # else:
    #     for post in user_posts:
    #         post.is_liked = False

    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()

    followers_count = profile_user.followers.count()
    following_count = profile_user.following.count()

    context = {
        'profile_user': profile_user,
        'posts': user_posts,
        # 'user_links': user_links,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
    }
    return render(request, 'users/profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, '프로필이 업데이트되었습니다.')
            return redirect('users:profile', username=request.user.username)
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    context = {'u_form': u_form, 'p_form': p_form}
    return render(request, 'users/edit_profile.html', context)