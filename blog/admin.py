from django.contrib import admin
from .models import Post

# admin.site.register(Post) #hushed out this line

from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'date_posted', 'image_preview')  # Add 'image_preview' to display the image
    list_filter = ('date_posted', 'author')
    search_fields = ('title', 'content')
    readonly_fields = ('image_preview',)  # Make the image preview read-only
    prepopulated_fields = {'slug': ('title',)}

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-width: 100px; max-height: 100px;" />'
        return "No Image"
    image_preview.allow_tags = True  # Allow HTML in the preview
    image_preview.short_description = 'Image Preview'  # Set column header name
