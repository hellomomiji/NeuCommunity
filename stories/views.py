from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.db.models import Count, Q
from .models import Story, Comment, Tag, Vote
from .forms import StoryForm, CommentForm

# Create your views here.


def search(request):
    query = request.GET.get('q', '')
    if query:
        stories = Story.objects.filter(
            Q(title__icontains=query) |
            Q(text__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    else:
        stories = Story.objects.none()

    context = {
        'stories': stories,
        'query': query,
    }
    return render(request, 'stories/search.html', context)


@login_required
def upvote_story(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    vote, created = Vote.objects.get_or_create(
        user=request.user, story=story, defaults={'vote_type': True})

    if not created:
        messages.error(request, "You have already voted for this story.")
    else:
        messages.success(request, "Upvote added.")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def create_story(request):
    if request.method == 'POST':
        form = StoryForm(request.POST)

        if form.is_valid():
            story = form.save(commit=False)
            story.user = request.user
            story.save()
            # story.tags.set(form.cleaned_data['tags'])
            return redirect('stories:home')
    else:
        form = StoryForm()

    context = {'form': form}
    return render(request, 'stories/create_story.html', context)


# Obselete
def index(request):
    stories = Story.objects.all()
    return render(request, 'stories/index.html', {'stories': stories})


def home(request):
    order_by = request.GET.get('order_by', 'votes')
    category_filter = request.GET.get('category', None)

    if order_by == 'votes':
        order_by = '-num_upvotes'
    elif order_by == 'new':
        order_by = '-created'
    elif order_by == '-created':
        order_by = '-created'
    else:
        order_by = '-num_upvotes'

    if category_filter:
        stories_list = Story.objects.annotate(
            num_upvotes=Count('vote', filter=Q(vote__vote_type=True))
        ).filter(category__name__iexact=category_filter).order_by(order_by)
    else:
        stories_list = Story.objects.annotate(
            num_upvotes=Count('vote', filter=Q(vote__vote_type=True))
        ).order_by(order_by)

    # Show 20 stories per page
    paginator = Paginator(stories_list, 30)

    page = request.GET.get('page')
    stories = paginator.get_page(page)

    context = {
        'stories': stories,
        'order_by': order_by,
        'category_filter': category_filter,
    }
    return render(request, 'stories/home.html', context)


@login_required
def story_detail(request, story_id):
    story = get_object_or_404(Story, pk=story_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.story = story
            comment.user = request.user

            parent_id = request.POST.get('parent_comment')
            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                comment.parent_id = parent_id

            comment.save()
            return redirect('stories:story_detail', story_id=story_id)
    else:
        form = CommentForm()

    root_comments = story.comments.filter(
        parent_comment__isnull=True).annotate(
        num_upvotes=Count('vote', filter=Q(vote__vote_type=True))).order_by('-num_upvotes')
    context = {
        'story': story,
        'form': form,
        'root_comments': root_comments,
    }
    return render(request, 'stories/story_detail.html', context)


@login_required
def add_comment(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.story = story
            comment.user = request.user
            comment.save()
            return redirect('stories:story_detail', story_id=story.id)
    else:
        form = CommentForm()

    context = {
        'story': story,
        'form': form
    }
    return render(request, 'stories/story_detail.html', context)

# Upvote for comment


@login_required
def upvote_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    vote, created = Vote.objects.get_or_create(
        user=request.user, comment=comment, defaults={'vote_type': True})

    if not created:
        messages.error(request, "You have already voted for this comment.")
    else:
        messages.success(request, "Upvote added.")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# Autocomlete searth for tags, Add an endpoint to fetch tags.


# @login_required
# def search_tags(request):
#     query = request.GET.get('query', '').strip()
#     if query:
#         tags = Tag.objects.filter(name__icontains=query).values('name')
#         return JsonResponse(list(tags), safe=False)
#     else:
#         return JsonResponse([], safe=False)
