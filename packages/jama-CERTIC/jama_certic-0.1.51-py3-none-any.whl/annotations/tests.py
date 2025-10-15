from django.test import TestCase
from resources import models
from rpc import methods as rpc_methods
from resources.management.commands.loadfixtures import load_fixtures
from django.contrib.auth.models import User
from annotations.models import Annotation
from rpc.methods import ServiceException

test_json = {"pouet": "tagada"}


class AnnotationTestCase(TestCase):
    def setUp(self):
        # load file types, create permissions
        load_fixtures()

        self.test_user = User.objects.create(username="basic_user")
        self.basic_user_key = "acme"

        # only django superusers have access to certain rpc methods.
        self.admin_user = User.objects.create(username="admin_user", is_superuser=True)
        rpc_methods.activate_rpc_access(
            self.admin_user, self.test_user.username, self.basic_user_key
        )

        self.test_project = models.Project.objects.create(
            label="projet test", description="projet test"
        )
        self.test_project_root_collection = models.Collection.objects.create(
            title="root", parent_id=None, project=self.test_project
        )
        self.test_metadataset = models.MetadataSet.objects.create(
            title="test metadata set", project=self.test_project
        )

        self.admin_role = models.Role.objects.create(
            label="admin", project=self.test_project
        )
        # give all permissions to admin role
        for perm in models.Permission.objects.all():
            self.admin_role.permissions.add(perm)

        # give admin role to the user on the project
        models.ProjectAccess.objects.get_or_create(
            project=self.test_project, user=self.test_user, role=self.admin_role
        )
        models.ProjectAccess.objects.get_or_create(
            project=self.test_project, user=self.admin_user, role=self.admin_role
        )
        # public user
        self.public_user = User.objects.create(username="public_user")
        self.public_role = models.Role.objects.create(
            label="public", project=self.test_project
        )
        for perm in models.Permission.objects.all():
            self.public_role.permissions.add(perm)
        models.ProjectAccess.objects.get_or_create(
            project=self.test_project, user=self.public_user, role=self.public_role
        )

    def test_add_annotation(self):
        with self.assertRaises(ServiceException):
            rpc_methods.create_annotation(self.test_user, 42, test_json)

        res = models.Resource.objects.create(
            title="test res", ptr_project=self.test_project
        )
        serialized_annotation = rpc_methods.create_annotation(
            self.test_user, res.pk, test_json
        )
        self.assertEqual(serialized_annotation.get("data"), test_json)

    def test_delete_annotation(self):
        with self.assertRaises(ServiceException):
            rpc_methods.delete_annotation(self.test_user, 42)

    def test_list_annotations(self):
        res = models.Resource.objects.create(
            title="test res", ptr_project=self.test_project
        )
        rpc_methods.create_annotation(self.test_user, res.pk, test_json)
        rpc_methods.create_annotation(self.test_user, res.pk, test_json)
        list = rpc_methods.list_annotations(self.test_user, res.pk)
        self.assertEqual(len(list), 2)

    def test_update_annotation(self):
        res = models.Resource.objects.create(
            title="test res", ptr_project=self.test_project
        )
        serialized_annotation = rpc_methods.create_annotation(
            self.test_user, res.pk, test_json
        )
        rpc_methods.update_annotation(
            self.test_user, serialized_annotation.get("id"), {"something": "else"}
        )
        fetched_annotation = Annotation.objects.get(pk=serialized_annotation.get("id"))
        self.assertEqual(fetched_annotation.data, {"something": "else"})

    def test_publish_annotation(self):
        res = models.Resource.objects.create(
            title="test res", ptr_project=self.test_project
        )
        serialized_annotation = rpc_methods.create_annotation(
            self.test_user, res.pk, test_json
        )
        rpc_methods.publish_annotation(self.test_user, serialized_annotation.get("id"))
        fetched_annotation = Annotation.objects.get(pk=serialized_annotation.get("id"))

        self.assertFalse(serialized_annotation.get("public"))
        self.assertTrue(fetched_annotation.public)

    def test_unpublish_annotation(self):
        res = models.Resource.objects.create(
            title="test res", ptr_project=self.test_project
        )
        serialized_annotation = rpc_methods.create_annotation(
            self.test_user, res.pk, test_json, True
        )
        rpc_methods.unpublish_annotation(
            self.test_user, serialized_annotation.get("id")
        )
        fetched_annotation = Annotation.objects.get(pk=serialized_annotation.get("id"))

        self.assertTrue(serialized_annotation.get("public"))
        self.assertFalse(fetched_annotation.public)
