import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.post_count = Post.objects.count()
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_authorized_client(self):
        """Проверка создания поста
        авторизованным пользователем.
        """
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': PostCreateFormTests.group.id,
            'text': 'Формы текст',
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ),
        )
        self.assertEqual(Post.objects.count(), self.post_count+1)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # post = Post.objects.latest('id')
        # self.assertEqual(post.text,form_data['text'])
        # self.assertEqual(post.group.id,form_data['group'])
        # self.assertEqual(post.image.name,f"posts/{form_data['image'].name}")
        self.assertTrue(
            Post.objects.filter(
                group=form_data['group'],
                text=form_data['text'],
                image=f"posts/{form_data['image'].name}",
            ).exists()
        )

    def test_create_post_guest_client(self):
        """Проверка создания поста гостем"""
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': self.group.id,
            'text': 'Формы текст',
            'image': uploaded
        }
        response = self.guest_client.post(
            reverse('posts:post_create'), data=form_data
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertFalse(
            Post.objects.filter(
                group=form_data['group'],
                text=form_data['text'],
                image=f"posts/{form_data['image'].name}",
            ).exists()
        )
        self.assertEqual(Post.objects.count(), self.post_count)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_add_comment_authorized_client(self):
        """После проверки формы комментарий
        авторизованного добавляется в пост
        """
        form_data = {
            'text': 'Комментарий авторизованного',
        }
        comment_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data, follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
                             'post_id': self.post.id}))
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text']
            ).exists())
        self.assertEqual(Comment.objects.count(), comment_count+1)

    def test_add_comment_guest_client(self):
        """После проверки формы комментарий
        гостя НЕ добавляется в пост
        """
        form_data = {
            'text': 'Комментарий гостя',
        }
        comment_count = Comment.objects.count()
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data, follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/posts/'
                                        f'{self.post.id}/comment/')
        self.assertFalse(
            Comment.objects.filter(
                text=form_data['text']
            ).exists())
        self.assertEqual(Comment.objects.count(), comment_count)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostEditFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.new_group = Group.objects.create(
            title='Новая тестовая группа новая',
            slug='new-slug',
            description='Тестовое описание новой группы',
        )
        small_gif = (
            b'\x50\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        new_small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )
        new_uploaded = SimpleUploadedFile(
            name='small_new.gif',
            content=new_small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовое содержание поста',
            group=cls.group,
            image=uploaded,
        )
        cls.form_data = {
            'text': 'Отредактированный пост',
            'group': cls.new_group.id,
            'image': new_uploaded,
        }
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_edit_post_authorized(self):
        '''Тестируем редактирования поста авторизованным пользователем'''
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id},
            ),
            data=self.form_data,
            follow=True,
        )
        self.post.refresh_from_db()
        data_for_equal = (
            (Post.objects.count(), posts_count),
            (response.status_code, HTTPStatus.OK),
            (self.post.text, self.form_data['text']),
            (self.post.group.id, self.form_data['group']),
            (self.post.image.name,f"posts/{self.form_data['image'].name}"),
        )
        for value, expected in data_for_equal:
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id},
            ),
        )
