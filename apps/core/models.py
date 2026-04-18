from django.db import models

# Create your models here.
class BaseModel(models.Model): 
    id = models.UUIDField(primary_key=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta: 
        abstract = True 