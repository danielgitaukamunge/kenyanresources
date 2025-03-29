from django.db import models
import uuid
from django.conf import settings
from users.models import User

class ResourceRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    parameters = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_fulfilled = models.BooleanField(default=False)

    def __str__(self):
        return f"Request {self.token} - {self.user.username}"

class UserResource(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.display_name} - {self.user.username}"