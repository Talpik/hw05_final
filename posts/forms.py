from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            "text": "Новый пост",
            "group": "Группа"
        }
        help_texts = {
            "text": "Введите ваше сообщение.",
            "group": "Выберите сообщество, где будет отображен пост."
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Комментарий'}
        help_texts = {'text': 'Оставьте ваш комментарий'}
