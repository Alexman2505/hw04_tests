import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_count = Post.objects.count()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.form_data = {
            'group': PostCreateFormTests.group.id,
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(PostCreateFormTests.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_guest_client(self):
        """Проверка создания поста гостем"""
        response = self.guest_client.post(
            reverse('posts:post_create'), data=self.form_data
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertFalse(
            Post.objects.filter(
                author=self.user,
                group=self.form_data['group'],
                text=self.form_data['text'],
                image='posts/small.gif'
            ).exists()
        )
        self.assertEqual(Post.objects.count(), self.post_count)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_post_authorized_client(self):
        """Проверка создания поста
        авторизованным пользователем.
        """
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=self.form_data
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ),
        )
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                group=self.form_data['group'],
                text=self.form_data['text'],
                image='posts/small.gif'
            ).exists()
        )
        self.assertEqual(Post.objects.count(), self.post_count+1)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostEditFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
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
            'group': PostEditFormTests.new_group.id,
            'image': new_uploaded,
        }
        cls.authorized_client = Client()
        cls.authorized_client.force_login(PostEditFormTests.user)

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
                kwargs={'post_id': PostEditFormTests.post.id},
            ),
            data=self.form_data,
            follow=True,
        )
        PostEditFormTests.post.refresh_from_db()
        data_for_equal = (
            (Post.objects.count(), posts_count),
            (response.status_code, HTTPStatus.OK),
            (PostEditFormTests.post.text, self.form_data['text']),
            (PostEditFormTests.post.group.id, self.form_data['group']),
            (
                str(PostEditFormTests.post.image).split('/')[1],
                str(self.form_data['image']),
            ),
        )
        for value, expected in data_for_equal:
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostEditFormTests.post.id},
            ),
        )
