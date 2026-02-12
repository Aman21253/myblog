# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class BlogsCategories(models.Model):
    bc_category_id = models.AutoField(primary_key=True)
    bc_category_name = models.CharField(max_length=150, blank=True, null=True)
    bc_slug = models.CharField(unique=True, max_length=200)
    bc_description = models.CharField(max_length=255, blank=True, null=True)
    bc_category_status = models.CharField(max_length=8, blank=True, null=True)
    bc_parent_id = models.IntegerField(blank=True, null=True)
    bc_created_at = models.DateTimeField()
    bc_updated_at = models.DateTimeField()
    bc_sort_order = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'blogs_categories'


class BlogsComments(models.Model):
    bc_comment_id = models.AutoField(primary_key=True)
    bc_blog = models.ForeignKey('BlogsDetails', models.DO_NOTHING, blank=True, null=True)
    bc_user = models.ForeignKey('BlogsUsers', models.DO_NOTHING, blank=True, null=True)
    bc_comment = models.TextField(blank=True, null=True)
    bc_created_at = models.DateTimeField()
    bc_status = models.CharField(max_length=8)
    bc_parent = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    bc_is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'blogs_comments'


class BlogsDetails(models.Model):
    bd_blog_id = models.AutoField(primary_key=True)
    bd_blog_title = models.CharField(max_length=255, blank=True, null=True)
    bd_slug = models.CharField(unique=True, max_length=255)
    bd_blog_content = models.TextField(blank=True, null=True)
    bd_excerpt = models.CharField(max_length=300, blank=True, null=True)
    bd_featured_image = models.CharField(max_length=500, blank=True, null=True)
    bd_date_added = models.DateField(blank=True, null=True)
    bd_updated_at = models.DateTimeField(blank=True, null=True)
    bd_published_at = models.DateTimeField(blank=True, null=True)
    bd_user_id = models.IntegerField(blank=True, null=True)
    bd_modified_by = models.IntegerField(blank=True, null=True)
    bd_blog_status = models.CharField(max_length=9, blank=True, null=True)
    bd_category_id = models.IntegerField(blank=True, null=True)
    bd_is_deleted = models.IntegerField()
    bd_views = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'blogs_details'


class BlogsUsers(models.Model):
    bu_user_id = models.AutoField(primary_key=True)
    bu_first_name = models.CharField(max_length=100, blank=True, null=True)
    bu_last_name = models.CharField(max_length=100, blank=True, null=True)
    bu_status = models.CharField(max_length=8, blank=True, null=True)
    bu_email = models.CharField(unique=True, max_length=150)
    bu_password_hash = models.CharField(max_length=255)
    bu_role = models.CharField(max_length=6)
    bu_username = models.CharField(max_length=100, unique=True, null=True, blank=True)
    bu_bio = models.TextField(null=True, blank=True)
    bu_profile_pic = models.ImageField(upload_to="profiles/", null=True, blank=True)
    bu_created_at = models.DateTimeField(auto_now_add=True)
    bu_updated_at = models.DateTimeField(auto_now_add=True)
    bu_last_login = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'blogs_users'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'

class BlogsLikes(models.Model):
    bl_like_id = models.AutoField(primary_key=True)
    bl_blog = models.ForeignKey(
        "BlogsDetails",
        on_delete=models.CASCADE,
        db_column="bl_blog_id",
        related_name="likes"
    )
    bl_user = models.ForeignKey(
        "BlogsUsers",
        on_delete=models.CASCADE,
        db_column="bl_user_id",
        related_name="likes"
    )
    bl_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "blogs_likes"
        managed = True 
        unique_together = ("bl_blog", "bl_user")

    def __str__(self):
        return f"{self.bl_user_id} -> {self.bl_blog_id}"