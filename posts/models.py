from django.db import models
from django.contrib.auth import get_user_model
from django.template.defaultfilters import truncatechars

User = get_user_model()


class Group(models.Model):
    title = models.CharField("Название", max_length=200)
    slug = models.SlugField("Автоссылка", unique=True)
    description = models.TextField("Описание", null=True, blank=True)
    
    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField("Текст")
    pub_date = models.DateTimeField(
        "Дата публикации",
        auto_now_add=True,
        db_index=True
    )
    author = models.ForeignKey(
        User, 
        verbose_name="Автор",
        on_delete=models.CASCADE, 
        related_name="posts"
    )
    group = models.ForeignKey(
        Group,
        verbose_name="Сообщества",
        blank=True, 
        null=True, on_delete=models.SET_NULL, 
        related_name="posts"
    )
    # поле для картинки
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return f"Text:{truncatechars(self.text, 20)}"


class Comment(models.Model):
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE, 
        related_name="comments"
    )
    text = models.TextField(verbose_name='Комментарий')
    created = models.DateTimeField(
        'date created', 
        auto_now_add=True
    )

    class Meta:
        ordering = ('-created',)
    
    def __str__(self):
        return f"Text:{truncatechars(self.text, 10)}"


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following"
    )
