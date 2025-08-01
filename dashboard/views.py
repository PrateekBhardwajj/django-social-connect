from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import requests
from .models import UserProfile
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout

# ------------------ REGISTER ------------------
@login_required
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'dashboard/register.html', {'form': form})


# ------------------ DASHBOARD ------------------

@login_required
def dashboard(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'dashboard/dashboard.html', {'profile': profile})


# ------------------ FACEBOOK CALLBACK ------------------
def facebook_callback(request):
    code = request.GET.get('code')
    if not code:
        return HttpResponse("No code provided from Facebook.", status=400)

    # Exchange code for access token
    access_token_url = 'https://graph.facebook.com/v20.0/oauth/access_token'
    params = {
        'client_id': '1276278970810903',
        'redirect_uri': 'http://localhost:8000/facebook/callback/',
        'client_secret': '34a0fafc7e2bf9addca21bc914e696d5',
        'code': code,
    }
    response = requests.get(access_token_url, params=params)
    data = response.json()

    if 'access_token' not in data:
        return HttpResponse(f"Error fetching access token: {data}", status=400)

    user_access_token = data['access_token']

    # Get Facebook Pages
    pages_url = "https://graph.facebook.com/v20.0/me/accounts"
    pages_response = requests.get(pages_url, params={"access_token": user_access_token})
    pages_data = pages_response.json()

    if 'data' not in pages_data or not pages_data['data']:
        return HttpResponse("No Facebook pages found.", status=400)

    page = pages_data['data'][0]  # First page
    page_id = page['id']
    page_token = page['access_token']

    # Get Instagram Business Account
    insta_url = f"https://graph.facebook.com/v20.0/{page_id}"
    insta_response = requests.get(insta_url, params={"fields": "instagram_business_account", "access_token": page_token})
    insta_data = insta_response.json()

    instagram_business_id = insta_data.get("instagram_business_account", {}).get("id")

    # Save in DB
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    profile.facebook_access_token = user_access_token
    profile.facebook_page_id = page_id
    profile.facebook_page_token = page_token
    profile.instagram_business_id = instagram_business_id
    profile.save()

    print("Page Linked:", page_id, page_token)
    print("Instagram Business Data:", insta_data)

    return redirect('facebook_posts')


# ------------------ FACEBOOK POSTS ------------------

@login_required
def facebook_posts(request):
    profile = request.user.userprofile

    if not profile.facebook_page_token:
        return render(request, "dashboard/facebook_posts.html", {"posts": []})

    posts_url = f"https://graph.facebook.com/v20.0/{profile.facebook_page_id}/posts"
    params = {
        "fields": "id,message,created_time,permalink_url,"
                  "likes.summary(true),"
                  "comments.limit(5){from,message}",
        "access_token": profile.facebook_page_token,
    }
    response = requests.get(posts_url, params=params)
    posts_data = response.json()

    posts = posts_data.get("data", [])
    return render(request, "dashboard/facebook_posts.html", {"posts": posts})




@login_required
def instagram_posts(request):
    profile = request.user.userprofile

    if not profile.instagram_business_id or not profile.facebook_page_token:
        return HttpResponse("Instagram is not connected.", status=400)

    url = f"https://graph.facebook.com/v20.0/{profile.instagram_business_id}/media"
    params = {
        "fields": "id,caption,media_type,media_url,permalink,timestamp",
        "access_token": profile.facebook_page_token,
    }

    response = requests.get(url, params=params)
    data = response.json()

    posts = data.get("data", [])
    return render(request, "dashboard/instagram_posts.html", {"posts": posts})




@login_required
def facebook_like(request, post_id):
    profile = request.user.userprofile
    if not profile.facebook_page_token:
        messages.error(request, "Facebook not connected.")
        return redirect('facebook_posts')

    url = f"https://graph.facebook.com/v20.0/{post_id}/likes"
    params = {
        'access_token': profile.facebook_page_token
    }
    response = requests.post(url, params=params)
    result = response.json()

    if result.get("success"):
        messages.success(request, "Post liked successfully!")
    else:
        messages.error(request, f"Error: {result}")

    return redirect('facebook_posts')



@login_required
def facebook_comment(request, post_id):
    profile = request.user.userprofile
    if request.method == "POST":
        comment_text = request.POST.get("comment")
        if not comment_text:
            messages.error(request, "Comment cannot be empty.")
            return redirect('facebook_posts')

        if not profile.facebook_page_token:
            messages.error(request, "Facebook not connected.")
            return redirect('facebook_posts')

        url = f"https://graph.facebook.com/v20.0/{post_id}/comments"
        params = {
            'message': comment_text,
            'access_token': profile.facebook_page_token
        }
        response = requests.post(url, params=params)
        result = response.json()

        if "id" in result:
            messages.success(request, "Comment posted successfully!")
        else:
            messages.error(request, f"Error: {result}")

    return redirect('facebook_posts')

from django.http import JsonResponse

@login_required
def facebook_like_ajax(request, post_id):
    profile = request.user.userprofile
    if not profile.facebook_page_token:
        return JsonResponse({"success": False, "error": "Facebook not connected."})

    url = f"https://graph.facebook.com/v20.0/{post_id}/likes"
    params = {"access_token": profile.facebook_page_token}
    response = requests.post(url, params=params)
    result = response.json()

    if result.get("success"):
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": result})


@login_required
def facebook_comment_ajax(request, post_id):
    profile = request.user.userprofile
    if request.method == "POST":
        comment_text = request.POST.get("comment")
        if not comment_text:
            return JsonResponse({"success": False, "error": "Comment cannot be empty."})

        if not profile.facebook_page_token:
            return JsonResponse({"success": False, "error": "Facebook not connected."})

        url = f"https://graph.facebook.com/v20.0/{post_id}/comments"
        params = {
            "message": comment_text,
            "access_token": profile.facebook_page_token
        }
        response = requests.post(url, params=params)
        result = response.json()

        if "id" in result:
            return JsonResponse({"success": True, "comment": comment_text, "user": request.user.username})
        return JsonResponse({"success": False, "error": result})

    return JsonResponse({"success": False, "error": "Invalid request method"})


@login_required
def instagram_comment_ajax(request, post_id):
    profile = request.user.userprofile

    if request.method == "POST":
        comment_text = request.POST.get("comment")
        if not comment_text:
            return JsonResponse({"success": False, "error": "Comment cannot be empty."})

        if not profile.instagram_business_id or not profile.facebook_page_token:
            return JsonResponse({"success": False, "error": "Instagram is not connected."})

        url = f"https://graph.facebook.com/v20.0/{post_id}/comments"
        params = {
            "message": comment_text,
            "access_token": profile.facebook_page_token
        }
        response = requests.post(url, params=params)
        result = response.json()

        if "id" in result:
            return JsonResponse({"success": True, "comment": comment_text, "user": request.user.username})
        return JsonResponse({"success": False, "error": result})

    return JsonResponse({"success": False, "error": "Invalid request method"})

def custom_logout(request):
    if request.method == "POST" or request.method == "GET":  # allow GET too
        logout(request)
        return redirect('login')