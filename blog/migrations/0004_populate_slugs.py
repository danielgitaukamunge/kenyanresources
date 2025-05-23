# Generated by Django 5.1.7 on 2025-03-28 09:19
from django.db import migrations
from django.utils.text import slugify

def generate_unique_slug(title, existing_slugs):
    """Helper function to create a unique slug from title."""
    base_slug = slugify(title)
    unique_slug = base_slug
    num = 1
    while unique_slug in existing_slugs:
        unique_slug = f"{base_slug}-{num}"
        num += 1
    return unique_slug

def populate_slugs(apps, schema_editor):
    """Migration function to fill in slugs for existing posts."""
    Post = apps.get_model('blog', 'Post')
    existing_slugs = set(Post.objects.values_list('slug', flat=True))
    
    for post in Post.objects.all():
        if not post.slug:
            post.slug = generate_unique_slug(post.title, existing_slugs)
            post.save()
            existing_slugs.add(post.slug)  # Update set to avoid duplicates

class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0003_post_slug'),  # Replace with your last migration
    ]

    operations = [
        migrations.RunPython(populate_slugs),
    ]



