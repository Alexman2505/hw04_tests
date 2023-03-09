from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем тестового пользователя
        cls.user = User.objects.create_user(username='user')
        # Создаем тестового пользователя-автора
        cls.user_author = User.objects.create_user(username='Author')
        # Создаем тестовую группу
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Test_slag",
            description="Тестовое описание",
        )
        # Создаем тестовый пост
        cls.post = Post.objects.create(
            text="Тестовый пост", author=cls.user_author, group=cls.group
        )

        # Создаём неавторизованный клиент
        cls.guest_client = Client()

        # Создаём клиент для авторизации тестовым пользователем
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        # Создаём клиент для авторизации тестовым пользователем-автором
        cls.author_client = Client()
        cls.author_client.force_login(cls.user_author)

        cls.URLS_ALL_STARS = (
            ('/', 'posts/index.html', HTTPStatus.OK),
            (
                f'/group/{cls.group.slug}/',
                'posts/group_list.html',
                HTTPStatus.OK,
            ),
            (
                f'/profile/{cls.post.author.username}/',
                'posts/profile.html',
                HTTPStatus.OK,
            ),
            (
                f'/posts/{cls.post.pk}/',
                'posts/post_detail.html',
                HTTPStatus.OK,
            ),
            ('/unexisting_page/', 'core/404.html', HTTPStatus.NOT_FOUND),
            ('/create/', 'posts/create_post.html', HTTPStatus.OK),
            (
                f'/posts/{cls.post.pk}/edit/',
                'posts/create_post.html',
                HTTPStatus.OK,
            ),
            # (
            #     f'/posts/{cls.post.pk}/comment',
            #     'posts/post_detail.html',
            #     HTTPStatus.OK,
            # ),
        )

    def test_url_for_guest_client(self):
        """Проверяем доступные адреса для клиента."""
        cache.clear()
        for url, template, status in self.URLS_ALL_STARS:
            with self.subTest(url=url, template=template, status=status):
                response = self.guest_client.get(url)
                if (
                    url
                    == self.URLS_ALL_STARS[settings.POST_CREATE][
                        settings.POST_URL
                    ]
                    or url
                    == self.URLS_ALL_STARS[settings.POST_EDIT][
                        settings.POST_URL
                    ]
                    # or url
                    # == self.URLS_ALL_STARS[settings.POST_COMMENT][
                    #     settings.POST_URL
                    # ]
                ):
                    self.assertRedirects(response, '/auth/login/?next=' + url)
                else:
                    self.assertTemplateUsed(response, template)
                    self.assertEqual(response.status_code, status)

    def test_url_for_authorized_client(self):
        """Проверяем доступные адреса для авторизованного пользователя."""
        cache.clear()
        for url, template, status in self.URLS_ALL_STARS:
            with self.subTest(url=url, template=template, status=status):
                response = self.authorized_client.get(url)
                if (
                    url
                    == self.URLS_ALL_STARS[settings.POST_EDIT][
                        settings.POST_URL
                    ]
                ):
                    self.assertRedirects(
                        response,
                        self.URLS_ALL_STARS[settings.POST_DETAIL][
                            settings.POST_URL
                        ],
                    )
                else:
                    self.assertTemplateUsed(response, template)
                    self.assertEqual(response.status_code, status)

    def test_url_for_author_client(self):
        """Проверяем доступные адреса для автора поста."""
        for url, template, status in self.URLS_ALL_STARS:
            with self.subTest(url=url, template=template, status=status):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, status)
