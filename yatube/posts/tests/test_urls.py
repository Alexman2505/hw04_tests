from http import HTTPStatus

from django.conf import settings
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
        )

    def test_all(self):
        """Тесты для всех. И пусть никто не уйдет обиженный"""
        for url, template, status in self.URLS_ALL_STARS:
            with self.subTest(url=url, template=template, status=status):
                for client in [
                    self.guest_client,
                    self.authorized_client,
                    self.author_client,
                ]:
                    response = client.get(url)
                    if (
                        client == self.guest_client
                        and url
                        == self.URLS_ALL_STARS[settings.POST_CREATE][
                            settings.POST_URL
                        ]
                    ) or (
                        client == self.guest_client
                        and url
                        == self.URLS_ALL_STARS[settings.POST_EDIT][
                            settings.POST_URL
                        ]
                    ):
                        self.assertRedirects(
                            response, '/auth/login/?next=' + url
                        )
                    elif (
                        client == self.authorized_client
                        and url
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
