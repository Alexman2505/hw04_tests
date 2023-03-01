from django import forms
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings

from posts.models import Group, Post, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем тестового пользователя-автора
        cls.user_author = User.objects.create_user(username='Author')
        # Создаем тестовую группу
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Test_slag",
            description="Тестовое описание",
        )
        # Создаем тестовый пост с группой
        cls.post = Post.objects.create(
            text="Тестовый пост", author=cls.user_author, group=cls.group
        )
        # Создаем тестовый пост, но без группы
        cls.post_1 = Post.objects.create(
            text='Пост без группы',
            author=cls.user_author,
            # group=cls.group
        )
        # Создаем еще один тестовый пост с группой
        cls.post_2 = Post.objects.create(
            text='Еще один пост', author=cls.user_author, group=cls.group
        )
        cls.templates_guest = (
            (
                reverse('posts:index'),
                'posts/index.html',
                Post.objects.select_related('group', 'author'),
            ),
            (
                reverse(
                    'posts:group_list',
                    kwargs={'slug': PostPagesTests.group.slug},
                ),
                'posts/group_list.html',
                Post.objects.filter(group=PostPagesTests.group),
            ),
            (
                reverse(
                    'posts:profile',
                    kwargs={'username': PostPagesTests.user_author},
                ),
                'posts/profile.html',
                Post.objects.filter(author=PostPagesTests.post.author),
            ),
            (
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post.pk},
                ),
                'posts/post_detail.html',
                Post.objects.filter(pk=PostPagesTests.post.pk),
            ),
        )
        cls.templates_author = (
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': PostPagesTests.post.pk},
                ),
                'posts/create_post.html',
            ),
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        # Создаём неавторизованный клиент
        cls.guest_client = Client()
        # Создаём клиент для авторизации тестовым пользователем-автором
        cls.author_client = Client()
        cls.author_client.force_login(PostPagesTests.user_author)

    def test_views_guest_client(self):
        """Тестируем адреса для гостя"""
        for name, template, filt in self.templates_guest:
            with self.subTest(name=name, template=template, filt=filt):
                response = self.guest_client.get(name)
                self.assertQuerysetEqual(
                    response.context['page_obj']
                    if 'page_obj' in response.context
                    else [response.context['post']],
                    filt,
                    transform=lambda x: x,
                )

    def test_views_author_client(self):
        """Тестируем адреса для автора"""
        for name, template in self.templates_author:
            for value, expected in self.form_fields.items():
                with self.subTest(name=name, template=template):
                    response = self.author_client.get(name)
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)
                if name in 'edit':
                    self.assertEqual(
                        response.context.get('form').initial.get('text'),
                        PostPagesTests.post.text,
                    )
                    self.assertEqual(
                        response.context.get('form').initial.get('group'),
                        PostPagesTests.post.group.pk,
                    )
                    is_edit_context = response.context.get('is_edit')
                    self.assertTrue(is_edit_context)

    def test_create_post_page_show_correct_context(self):
        """Тестируем шаблон создания поста"""
        response = self.author_client.get(reverse('posts:post_create'))
        # Словарь ожидаемых типов полей формы:# указываем,
        # объектами какого класса должны быть поля формы
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        list_objs = list()
        for i in range(
            settings.NUMBER_OF_POSTS + settings.NUMBER_OF_POSTS_PAGE_TWO
        ):
            list_objs.append(
                Post.objects.create(
                    author=cls.user_author,
                    text=f'Тест пост #{i+1}',
                    group=cls.group,
                )
            )
        cls.pages = (
            (
                reverse('posts:index'),
                (settings.NUMBER_OF_POSTS, settings.NUMBER_OF_POSTS_PAGE_TWO),
            ),
            (
                reverse(
                    'posts:group_list',
                    kwargs={'slug': PaginatorViewsTest.group.slug},
                ),
                (settings.NUMBER_OF_POSTS, settings.NUMBER_OF_POSTS_PAGE_TWO),
            ),
            (
                reverse(
                    'posts:profile',
                    kwargs={'username': PaginatorViewsTest.user_author},
                ),
                (settings.NUMBER_OF_POSTS, settings.NUMBER_OF_POSTS_PAGE_TWO),
            ),
        )

    def test_pagination(self):
        '''Тестируем паджинатор'''
        for url, page_count in self.pages:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), page_count[0]
                )
                if page_count[1]:
                    response = self.client.get(url + '?page=2')
                    self.assertEqual(
                        len(response.context['page_obj']), page_count[1]
                    )
