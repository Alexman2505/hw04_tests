from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import models


User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(
        help_text="Текст нового поста", verbose_name="Текст поста"
    )
    pub_date = models.DateTimeField(auto_now_add=True, db_index=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='posts'
    )
    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        help_text="Группа, к которой будет относиться пост",
        verbose_name="Группа",
    )
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to='posts/',
        blank=True,
        null=True)

    class Meta:
        ordering = ['-pub_date']

    def __str__(self) -> str:
        return self.text[: settings.SLICE_LETTERS]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField()
    created = models.DateTimeField(
        auto_now_add=True
    )
    class Meta:
        ordering = ['-created']

    def __str__(self) -> str:
        return self.text
