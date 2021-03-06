from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from .models import Post, Group, Comment, Follow


DUMMY_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}

User = get_user_model()


class UserNotAuthorizedTests(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_not_auth_user_cant_create_post(self):
        """
        Неавторизованный посетитель не может опубликовать пост
        (его редиректит на страницу входа)
        """
        response = self.client.get(reverse('new_post'), follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')
    
    def test_check_redirect_not_auth_user(self):
        self.client = Client()
        response = self.client.get(reverse('new_post'), follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/') 
        self.post = self.client.post(reverse('new_post'), {'text' : ''})
        post_count = Post.objects.all().count()
        self.assertEqual(post_count, 0)

    def test_check_404(self):
        response = self.client.get('/test_error_page_404/')
        self.assertEqual(response.status_code, 404)


class UserIsAuthorizedTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.new_user = User.objects.create_user(
            username="terminatorT2000",
            email="terminatort2000@mail.com",
            password="123456"
        )
        self.second_user = User.objects.create_user(
            username="tron",
            email="tron@mail.com",
            password="123456"
        )
        self.group = Group.objects.create(
            title="TombRider",
            slug="tombrider",
            description="A new group of fans Lara Kroft"
        )
        self.text_for_post = "Kukaracha v nebe parahod, kukaracha dym uje idet"
        self.post_img = Post.objects.create(
            text=self.text_for_post, 
            group=self.group,
            author=self.new_user
        )

        self.post_second = Post.objects.create(
            text=self.text_for_post,
            author=self.second_user,
            group=self.group
        )
        self.client.force_login(self.new_user)

    def check_text_post(self, url, text, author, group):
        """
        Проверка всех атрибутов поста
        """
        response = self.client.get(url)
        paginator = response.context.get('paginator')

        if paginator is not None:
            post = response.context['page'][0]
        else:
            post = response.context['post']
        
        self.assertEqual(post.text, text)
        self.assertEqual(post.author, author)
        self.assertEqual(post.group, group)
    
    def test_profile_new_user(self):
        """
        После регистрации пользователя создается его персональная страница
        """
        response = self.client.get(reverse(
            'profile',
            kwargs={'username': self.new_user}
            )
        )
        self.assertEqual(response.status_code, 200)
    
    @override_settings(CACHES=DUMMY_CACHES)
    def test_create_new_post(self):
        """
        Авторизованный пользователь может опубликовать пост (new)
        """
        self.client.post(
            reverse('new_post'),
            {'text': self.text_for_post, 'group': self.group.id},
            follow=True,
        )
        response = self.client.get(reverse('index'))
        self.assertContains(response, self.text_for_post)
    
    @override_settings(CACHES=DUMMY_CACHES)
    def test_new_post_published(self):
        """
        После публикации поста новая запись появляется на главной странице 
        сайта (index), на персональной странице пользователя (profile),
        и на отдельной странице поста (post)
        """
        post = Post.objects.create(
            text=self.text_for_post, 
            group=self.group,
            author=self.new_user
        )
        list_urls = [
            reverse('index'),
            reverse(
                'profile',
                kwargs={'username': self.new_user.username}
            ),
            reverse('post', args=(self.new_user.username, post.pk)) 
        ]

        for url in list_urls:
            self.check_text_post(
                url,
                self.text_for_post,
                self.new_user,
                self.group
            )

    @override_settings(CACHES=DUMMY_CACHES) 
    def test_post_can_be_edit_and_view(self):
        """
        Авторизованный пользователь может отредактировать свой пост и его
        содержимое изменится на всех связанных страницах
        """
        text_for_edit_post = "Durum-dum-dum tu-tu-ru-ru-rum"
        self.post_for_edit = Post.objects.create(
            text="My test post #1", 
            group=self.group, 
            author=self.new_user
        )
        self.group_for_edit_post = Group.objects.create(
            title="Barcelona",
            slug="barcelona",
            description="ONE LIFE - ONE LOVE"
            )

        self.client.post(
            reverse(
                'post_edit',
                args=[self.new_user.username, self.post_for_edit.id]
            ),
            {
                'text': text_for_edit_post, 
                'group': self.group_for_edit_post.id
            },
            is_edit=True,
            follow=True
        )

        list_urls = [
            reverse('index'),
            reverse(
                'profile',
                kwargs={'username': self.new_user.username}
            ),
            reverse(
                'post', 
                kwargs={
                    'username': self.new_user.username,
                    'post_id': self.post_for_edit.id
                }
            ),
            reverse('group_posts', args=[self.group_for_edit_post.slug])
        ]
        
        for url in list_urls:
            self.check_text_post(
                url, 
                text_for_edit_post, 
                self.new_user, 
                self.group_for_edit_post
            )
    
    @override_settings(CACHES=DUMMY_CACHES)
    def test_teg_img_and_post_with_img(self):
        """
        1. Проверяет страницу конкретной записи с картинкой: тег <img>
        2. Проверяет, что на главной странице, на странице профайла и на 
        странице группы пост с картинкой отображается корректно, с тегом <img>
        """
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        post = Post.objects.create(
            author=self.new_user,
            text=self.text_for_post,
            group=self.group,
            image=uploaded
        )

        response_list = [
            reverse('index'),
            reverse('profile', args=(self.new_user,)),
            reverse('post', args=(self.new_user, post.id,)),
            reverse('group_posts', args=(self.group.slug,))
        ]

        for page in response_list:
            response = self.client.get(page)
            self.assertContains(response, '<img')
    
    def test_security_non_img(self):
        """
        Проверяет, что срабатывает защита от загрузки файлов
        не-графических форматов
        """
        test_text = 'Проверка поста с неграфическим файлом'
        url = reverse('post_edit', kwargs={
            'username': self.new_user, 'post_id': self.post_img.id
            }
        )
        file = SimpleUploadedFile(content=b'test', name='test_file.txt')
        response = self.client.post(
            url,
            {'text': test_text, 'author': self.new_user, 'image': file},
            follow=True
        )
            
        self.assertFormError(
                response,
                'form',  
                'image',
                'Загрузите правильное изображение. Файл, который вы загрузили,'
                ' поврежден или не является изображением.',
                msg_prefix='Проверьте, что не может загружаться отличный от'
                ' изображения файл' 
        )
    
    def test_index_page_cached(self):
        """
        Тесты, которые проверяют работу кэша
        """
        test_text = "Test post for check cache"
        post = Post.objects.create(
            text=test_text,
            author=self.new_user,
            group=self.group
        )
        response_1 = self.client.get(reverse('index'))
        self.assertContains(response_1, post.text)
        
        post.delete()
        response_2 = self.client.get(reverse('index'))
        self.assertEqual(response_1.content, response_2.content)
        
        cache.clear()
        response_3 = self.client.get(reverse('index'))
        self.assertNotEqual(response_1.content, response_3.content)

    def test_follow(self):
        """
        Авторизованный пользователь может подписываться на других пользователей
        """
        self.client.get(reverse( 
            "profile_follow", 
            args=[self.second_user.username] 
            ) 
        )
        follower = Follow.objects.get(user=self.new_user)
        following = Follow.objects.get(author=self.second_user)
        self.assertEqual(follower.pk, following.pk)
    
    def test_unfollow(self):
        """
        Авторизованный пользователь может удалять других юзеров из подписок.
        """
        self.client.get(reverse( 
            "profile_follow", 
            args=[self.second_user.username] 
            ) 
        )
        subscription = Follow.objects.filter(
            user=self.new_user,
            author=self.second_user
        ).count()
        self.assertEqual(subscription, 1)

        self.client.get(reverse(
            "profile_unfollow",
            args=[self.second_user.username]
            )
        )
        subscription = Follow.objects.filter(
            user=self.new_user,
            author=self.second_user
        ).count()
        self.assertEqual(subscription, 0)

    @override_settings(CACHE=DUMMY_CACHES)
    def test_follow_index_subscribe(self):
        """
        Новая запись пользователя появляется в ленте тех, кто на него подписан. 
        """
        self.client.get(reverse( 
            "profile_follow", 
            args=[self.second_user.username] 
            ) 
        )
        response = self.client.get(reverse('follow_index'))
        self.assertContains(response, self.post_second.text, status_code=200)
    
    @override_settings(CACHE=DUMMY_CACHES)
    def test_folllow_index_unsubscribe(self):
        """
        Новая запись пользователя не появляется в ленте тех, 
        кто не подписан на него.
        """
        self.client.get(reverse( 
            "profile_follow", 
            args=[self.second_user.username] 
            ) 
        )
        self.client.logout()
        self.client.force_login(self.second_user)
        response = self.client.get(reverse('follow_index'))
        self.assertNotContains(
            response,
            self.post_second.text,
            status_code=200
        )
    
    def test_comment_post(self):
        """
        Только авторизированный пользователь может комментировать посты.
        """
        self.client.post(
            reverse(
                'add_comment',
                kwargs={
                    'username': self.second_user.username,
                    'post_id': self.post_second.id
                }
            ),
            {
                'text': 'First test comment',
                'post': self.post_second.id,
                'author': self.new_user.id,  
            }
        )
        comment = Comment.objects.first()
        response = self.client.get(
            reverse(
                'post', 
                args=[self.second_user.username, self.post_second.id]
            )
        )
        self.assertContains(response, comment.text)
        self.assertContains(response, comment.author.username)
        self.assertContains(response, comment.post.id)
    
    def test_no_auth_comment_post(self):
        """
        Неавторизованный пользователь не может оставлять комменты
        """
        self.no_auth_user = Client()
        response = self.no_auth_user.post(
            reverse(
                'add_comment', 
                kwargs={
                    'username': self.second_user, 
                    'post_id': 1}), 
            {'text': 'текст коментария'}
        )
        self.assertEqual(Comment.objects.count(), 0)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/{self.second_user}/1/comment'
        )
