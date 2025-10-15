from django.test import TestCase
from rpc import methods
from resources import models
from django.contrib.auth.models import User
from resources.management.commands.loadfixtures import load_fixtures
from rpc.methods import ServiceException
from pathlib import Path
import os


class ServiceTestCase(TestCase):
    def setUp(self):
        # load file types, create permissions
        load_fixtures()

        self.test_user = User.objects.create(username="basic_user")
        self.basic_user_key = "acme"

        # only django superusers have access to certain rpc methods.
        self.admin_user = User.objects.create(username="admin_user", is_superuser=True)
        methods.activate_rpc_access(
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

    def test_ping(self):
        self.assertEqual(
            methods.ping(self.test_user), "pong {}".format(self.test_user.username)
        )

    def test_metadatasets(self):
        metadatasets = methods.metadatasets(self.test_user, self.test_project.pk)
        self.assertEqual(1, len(metadatasets))

    def test_permissions(self):
        for perm in models.Permission.objects.all():
            self.assertTrue(
                methods.has_permission(self.test_user, self.test_project.pk, perm.label)
            )

    def test_add_collection(self):
        methods.add_collection(
            self.test_user,
            "test_collection",
            parent_id=self.test_project_root_collection.pk,
        )
        collections = methods.collections(
            self.test_user, parent_id=self.test_project_root_collection.pk
        )
        self.assertEqual(len(collections), 1)

    def test_add_tag(self):
        methods.set_tag(self.test_user, "tag bidon", self.test_project.pk)
        tags = methods.tags(self.test_user, self.test_project.pk)
        self.assertEqual(len(tags), 1)

    def test_add_collection_from_path(self):
        ancestors_labels = ["toto", "tata"]
        collections = methods.add_collection_from_path(
            self.test_user, "/toto/tata/tutu", self.test_project.pk
        )
        idx = 0
        for ancestor in collections[-1]["ancestors"]:
            self.assertEqual(ancestor["title"], ancestors_labels[idx])
            idx = idx + 1
        self.assertEqual(models.Collection.objects.filter(title="root").count(), 1)

    def test_require_superuser(self):
        with self.assertRaises(ServiceException):
            methods.delete_role(self.test_user, 1)

    def test_resources_bad_order_by(self):
        collection = methods.add_collection(
            self.test_user,
            "test_collection",
            parent_id=self.test_project_root_collection.pk,
        )
        with self.assertRaises(ServiceException):
            methods.resources(self.test_user, collection["id"], order_by="pouet")

    def test_collections_bad_order_by(self):
        with self.assertRaises(ServiceException):
            methods.collections(
                self.test_user,
                parent_id=self.test_project_root_collection.pk,
                order_by="pouet",
            )

    def test_recycle_bin(self):
        col = methods.add_collection(
            self.test_user, "delete me", self.test_project.root_collection.pk
        )
        methods.delete_collection(self.test_user, col["id"])
        self.assertEqual(
            len(methods.recycle_bin(self.test_user, self.test_project.pk)), 1
        )

    def test_search(self):
        terms = [
            {"property": "title", "term": "contains", "value": "cherbourg"},
        ]
        methods.advanced_search(
            self.public_user,
            terms,
            self.test_project.pk,
            include_metas=True,
            collection_id=321,
            limit_from=0,
            limit_to=2000,
        )
        methods.simple_search(self.public_user, "pouet", self.test_project.pk)

    def test_descendants_resources_count(self):
        col = models.Collection.objects.create(
            title="desc col",
            project=self.test_project,
            parent=self.test_project.root_collection,
        )
        res = models.Resource.objects.create(
            title="test res", ptr_project=self.test_project
        )
        models.CollectionMembership.objects.create(collection=col, resource=res)
        self.assertEqual(col.descendants_resources_count(), 0)
        self.assertEqual(col.descendant_resources_count(), 1)

    def test_metas_count(self):
        col = models.Collection.objects.create(
            title="desc col",
            project=self.test_project,
            parent=self.test_project.root_collection,
        )
        res = models.Resource.objects.create(
            title="test res", ptr_project=self.test_project
        )
        models.CollectionMembership.objects.create(collection=col, resource=res)
        meta_set = models.MetadataSet.objects.create(
            project=self.test_project, title="test metadataset"
        )
        metadata_id = methods.add_metadata(
            self.admin_user, "metadata test", meta_set.id
        )
        methods.add_meta_to_resource(
            self.admin_user, res.pk, metadata_id, "test meta value A"
        )
        methods.add_meta_to_resource(
            self.admin_user, res.pk, metadata_id, "test meta value B"
        )
        methods.add_meta_to_resource(
            self.admin_user, res.pk, metadata_id, "test meta value C"
        )
        methods.add_meta_to_resource(
            self.admin_user, res.pk, metadata_id, "test meta value C"
        )
        result = methods.meta_count(self.admin_user, metadata_id, col.pk)
        self.assertEqual(result["test meta value C"], 1)

    def test_project_properties(self):
        test_property = methods.set_project_property(
            self.admin_user,
            self.test_project.pk,
            "test_prop",
            {"some": "complex", "value": [1, 2, 3]},
        )
        self.assertEqual(test_property["value"]["some"], "complex")
        methods.delete_project_property(
            self.admin_user, self.test_project.pk, "test_prop"
        )
        all_props = methods.project_properties(self.admin_user, self.test_project.pk)
        self.assertEqual(len(all_props), 0)

    def test_ordering(self):
        GOOD_ORDERING = ["0001", "0002", "0002a", "0002b", "0002c", "0003"]
        methods.add_collection(
            self.test_user,
            "0003",
            parent_id=self.test_project_root_collection.pk,
        )
        methods.add_collection(
            self.test_user,
            "0001",
            parent_id=self.test_project_root_collection.pk,
        )
        methods.add_collection(
            self.test_user,
            "0002",
            parent_id=self.test_project_root_collection.pk,
        )
        methods.add_collection(
            self.test_user,
            "0002c",
            parent_id=self.test_project_root_collection.pk,
        )
        methods.add_collection(
            self.test_user,
            "0002b",
            parent_id=self.test_project_root_collection.pk,
        )
        methods.add_collection(
            self.test_user,
            "0002a",
            parent_id=self.test_project_root_collection.pk,
        )
        titles = []
        for item in methods.collections(
            self.test_user, self.test_project_root_collection.pk, order_by="title"
        ):
            titles.append(item["title"])
        self.assertEqual(titles, GOOD_ORDERING)

        r = models.Resource.objects.create(title="0003", ptr_project=self.test_project)
        methods.add_resource_to_collection(
            self.test_user, r.pk, self.test_project_root_collection.pk
        )
        r = models.Resource.objects.create(title="0001", ptr_project=self.test_project)
        methods.add_resource_to_collection(
            self.test_user, r.pk, self.test_project_root_collection.pk
        )
        r = models.Resource.objects.create(title="0002b", ptr_project=self.test_project)
        methods.add_resource_to_collection(
            self.test_user, r.pk, self.test_project_root_collection.pk
        )
        r = models.Resource.objects.create(title="0002c", ptr_project=self.test_project)
        methods.add_resource_to_collection(
            self.test_user, r.pk, self.test_project_root_collection.pk
        )
        r = models.Resource.objects.create(title="0002a", ptr_project=self.test_project)
        methods.add_resource_to_collection(
            self.test_user, r.pk, self.test_project_root_collection.pk
        )
        r = models.Resource.objects.create(title="0002", ptr_project=self.test_project)
        methods.add_resource_to_collection(
            self.test_user, r.pk, self.test_project_root_collection.pk
        )

        titles = []
        for item in methods.resources(
            self.test_user, self.test_project_root_collection.pk, order_by="title"
        ):
            titles.append(item["title"])
        self.assertEqual(titles, GOOD_ORDERING)

    def test_remove_selection(self):
        col = methods.add_collection(
            self.test_user, "some_test", parent_id=self.test_project_root_collection.pk
        )
        r = models.Resource.objects.create(title="0002", ptr_project=self.test_project)
        methods.add_resource_to_collection(self.test_user, r.pk, col.get("id"))

        res = methods.remove_selection(
            self.test_user,
            col.get("id"),
            {"include": {"resources_ids": [r.pk], "collections_ids": []}},
        )

        self.assertTrue(res)

    def test_user_tasks(self):
        models.UserTask.objects.create(
            owner=self.test_user, description="test description 1"
        )
        models.UserTask.objects.create(
            owner=self.test_user, description="test description 2"
        )
        self.assertEqual(models.UserTask.objects.count(), 2)

    def test_replace_file(self):
        from resources.helpers import handle_local_file

        self.assertTrue(
            models.Resource.objects.filter(deleted_at__isnull=True).count() == 0
        )
        id1 = handle_local_file(
            Path(os.path.dirname(__file__), "test_assets", "cat_1.png"),
            self.test_project,
        )
        id2 = handle_local_file(
            Path(os.path.dirname(__file__), "test_assets", "cat_2.png"),
            self.test_project,
        )
        self.assertTrue(
            models.Resource.objects.filter(deleted_at__isnull=True).count() == 2
        )
        methods.replace_file(self.test_user, id1, id2)
        self.assertTrue(
            models.Resource.objects.filter(deleted_at__isnull=True).count() == 1
        )
