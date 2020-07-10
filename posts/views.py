from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render, reverse

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


def index(request):
    """ 
    The function view latest 10 posts in this blog. 

    Parameters: 
        request (HttpRequest object):  Contains metadata about the request 
    
    Returns: 
        Combines a given template with a given context dictionary  
        (latest 11 posts)and returns an HttpResponse object with that 
        rendered text.
    """
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request, 
        "index.html", 
        {"page": page, "paginator": paginator}
    )


def group_posts(request, slug):
    """ 
    The function view 10 posts of requested group

    Parameters: 
        request (HttpRequest object):  Contains metadata about the request
        slug (slug of group): Argument of get_object_or_404()
    
    Returns: 
        Combines a given template with a given context dictionary  
        (latest 10 posts of requested group) and returns an HttpResponse
        object with that rendered text.
    """
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request, 
        "group.html", 
        {"page": page, "paginator": paginator, "group": group}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():   
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index') 
    return render(request, 'new.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = False
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    ).exists()

    return render(
        request,
        'profile.html', 
        {
            'page': page, 
            'paginator': paginator, 
            'author': author,
            'following': following
        }
    )


@login_required
def follow_index(request):
    post_list = Post.objects.select_related('author').filter(
        author__following__user=request.user
    )
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 
        "follow.html", 
        {"page": page, "paginator": paginator}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    subscription = Follow.objects.filter(user=request.user, author=author)
    if request.user != author and not subscription.exists():
        Follow.objects.create(
            user=request.user,
            author=author
        )
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username=username)
 
 
def post_view(request, username, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author'),
        id=post_id, 
        author__username=username
    )
    form = CommentForm()
    comments = Comment.objects.filter(post=post_id)
    return render(
        request,
        'post.html', 
        {
            'author': post.author, 
            'post': post, 
            'comments': comments, 
            'form': form
        }
    )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(
        Post,
        id=post_id, 
        author__username=username
    )
    form = CommentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():   
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        form.save()
    return redirect(
        reverse(
            'post', 
            kwargs={'username': username, 'post_id': post_id}
        )
    )


@login_required
def post_edit(request, username, post_id):
    """
    Post edit function
    """
    post = get_object_or_404(
        Post.objects.select_related('author'),
        id=post_id, 
        author__username=username
    )
    if request.user != post.author:
        return redirect(
            reverse(
                'post', 
                kwargs={'username': username, 'post_id': post_id}
            )
        )
        
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(
        request,
        'new.html', 
        {'form': form, 'post': post, 'is_edit': True} 
    )


def page_not_found(request, exception):
    """
    Function for render 404
    Переменная exception содержит отладочную информацию
    """
    return render(
        request, 
        "misc/404.html", 
        {"path": request.path}, 
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
