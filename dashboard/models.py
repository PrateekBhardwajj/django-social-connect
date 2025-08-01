from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    facebook_id = models.CharField(max_length=255, blank=True, null=True)
    facebook_name = models.CharField(max_length=255, blank=True, null=True)
    facebook_access_token = models.TextField(blank=True, null=True)

    facebook_page_id = models.CharField(max_length=255, blank=True, null=True)
    facebook_page_token = models.TextField(blank=True, null=True)
    instagram_business_id = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        return self.user.username




# Signal to auto-create or update profile
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()

# Social Post model
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Owner of the dashboard
    platform = models.CharField(max_length=50)  # e.g. Facebook, Instagram
    post_id = models.CharField(max_length=255)  # ID from API
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.platform} - {self.content[:30]}"

# Likes
class Like(models.Model):
    post = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

# Comments
class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)