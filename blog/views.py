from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.db.models import Q
from django.db import IntegrityError
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from .models import BlogsUsers, BlogsCategories, BlogsDetails, BlogsComments


# ----------- USER MANAGEMENT HELPERS -----------
USER_ROLES = ["admin", "writer", "viewer"]
USER_STATUSES = ["Active", "Inactive"]


def _render_users_page(request, *, mode=None, edit_user=None):
    """Render the single users page (y_users.html) with optional create/edit form context."""
    q = (request.GET.get("q") or "").strip()

    users_qs = BlogsUsers.objects.all().order_by("-bu_user_id")
    if q:
        users_qs = users_qs.filter(
            Q(bu_first_name__icontains=q)
            | Q(bu_last_name__icontains=q)
            | Q(bu_email__icontains=q)
            | Q(bu_role__icontains=q)
        )

    return render(
        request,
        "blog/y_users.html",
        {
            "users": users_qs,
            "q": q,
            "mode": mode,  # None | 'create' | 'edit'
            "u": edit_user,
            "roles": USER_ROLES,
            "statuses": USER_STATUSES,
        },
    )


# ----------- SECURITY HELPERS -----------
def login_required_y(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get("user_id"):
            messages.error(request, "Please login first.")
            return redirect("y_login")
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            role = request.session.get("user_role")
            if role not in roles:
                messages.error(request, "Access denied.")
                return redirect("y_home")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

#---------------SLug---------------------
def make_slug(title: str) -> str:
    # spaces hatao + small letters
    slug = (title or "").strip().lower()
    slug = "".join(ch if ch.isalnum() else "-" for ch in slug)
    #  "-" me convert karta hai(double dash remove)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "post"

# It make unique in slug
def unique_slug(base: str) -> str:
    slug = base
    i = 2
    while BlogsDetails.objects.filter(bd_slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug

def _make_cat_slug(name: str) -> str:
    slug = (name or "").strip().lower()
    slug = "".join(ch if ch.isalnum() else "-" for ch in slug)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "category"


def _unique_cat_slug(base: str) -> str:
    slug = base
    i = 2
    while BlogsCategories.objects.filter(bc_slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug


def _render_categories_page(request, *, mode=None, edit_category=None):
    q = (request.GET.get("q") or "").strip()

    cats = BlogsCategories.objects.all().order_by("bc_sort_order", "bc_category_name")
    if q:
        cats = cats.filter(
            Q(bc_category_name__icontains=q) |
            Q(bc_slug__icontains=q) |
            Q(bc_description__icontains=q)
        )

    parent_choices = BlogsCategories.objects.all().order_by("bc_category_name")

    return render(request, "blog/y_categories.html", {
        "categories": cats,
        "parent_choices": parent_choices,
        "q": q,
        "mode": mode,
        "c": edit_category,
        "statuses": ["Active", "Inactive"],
    })

# ---------------- AUTH ----------------
def y_login(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        try:
            user = BlogsUsers.objects.get(bu_email=email)
        except BlogsUsers.DoesNotExist:
            messages.error(request, "Invalid email or password")
            return redirect("y_login")

        if user.bu_status != "Active":
            messages.error(request, "Account inactive. Contact admin.")
            return redirect("y_login")

        if not check_password(password, user.bu_password_hash):
            messages.error(request, "Invalid email or password")
            return redirect("y_login")

        # SESSION SET
        request.session["user_id"] = user.bu_user_id
        request.session["user_role"] = user.bu_role
        request.session["user_email"] = user.bu_email

        # update last login
        try:
            user.bu_last_login = timezone.now()
            user.save(update_fields=["bu_last_login"])
        except:
            pass

        # login should go to HOME
        return redirect("y_home")

    return render(request, "blog/y_login.html")


def y_register(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not name:
            messages.error(request, "Name is required.")
            return redirect("y_register")

        if password != confirm_password:
            messages.error(request, "Password and Confirm Password do not match.")
            return redirect("y_register")

        if BlogsUsers.objects.filter(bu_email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("y_register")

        # split name
        parts = name.split()
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        # force role to viewer
        role = "viewer"

        user = BlogsUsers.objects.create(
            bu_first_name=first_name,
            bu_last_name=last_name,
            bu_email=email,
            bu_password_hash=make_password(password),
            bu_role=role,
            bu_status="Active",
            bu_created_at=timezone.now(),  # important if DB requires NOT NULL
            bu_updated_at=timezone.now(),  # important if DB requires NOT NULL
        )

        # auto-login after register
        request.session["user_id"] = user.bu_user_id
        request.session["user_role"] = user.bu_role
        request.session["user_email"] = user.bu_email

        messages.success(request, "Registration successful.")
        return redirect("y_home")

    return render(request, "blog/y_register.html")


def y_logout(request):
    request.session.flush()
    return redirect("y_login")


# ---------------- PAGES ----------------
@login_required_y
def y_home(request):
    q = (request.GET.get("q") or "").strip()
    cat = (request.GET.get("cat") or "").strip()

    role = request.session.get("user_role", "viewer")

    categories = BlogsCategories.objects.filter(
        bc_category_status="Active"
    ).order_by("bc_sort_order", "bc_category_name")

    blogs = BlogsDetails.objects.filter(
        bd_blog_status="Published",
        bd_is_deleted=0
    )

    if cat:
        blogs = blogs.filter(bd_category_id=cat)

    if q:
        blogs = blogs.filter(
            Q(bd_blog_title__icontains=q) |
            Q(bd_excerpt__icontains=q) |
            Q(bd_blog_content__icontains=q) |
            Q(bd_slug__icontains=q)
        )

    blogs = blogs.order_by("-bd_published_at", "-bd_updated_at")

    return render(request, "blog/y_home.html", {
        "blogs": blogs[:50],
        "categories": categories,
        "q": q,
        "cat": cat,
        "role": role,
    })

#----------Blog detail--------------
@login_required_y
def y_blog_detail(request, slug):
    role = request.session.get("user_role", "viewer")
    user_id = request.session.get("user_id")

    blog = get_object_or_404(BlogsDetails, bd_slug=slug, bd_is_deleted=0)

    all_comments = (
        BlogsComments.objects
        .filter(bc_blog=blog, bc_is_deleted=0, bc_status="Approved")
        .select_related("bc_user", "bc_parent")
        .order_by("-bc_created_at")
    )

    children_map = {}
    roots = []

    for c in all_comments:
        parent_id = c.bc_parent_id
        if parent_id:
            children_map.setdefault(parent_id, []).append(c)
        else:
            roots.append(c)

    for c in all_comments:
        c.children = children_map.get(c.bc_comment_id, [])

    if request.method == "POST":
        if role != "viewer":
            messages.error(request, "Only viewer can add comment.")
            return redirect("y_blog_detail", slug=slug)

        comment_text = (request.POST.get("comment") or "").strip()
        parent_id = request.POST.get("parent_id")

        if not comment_text:
            messages.error(request, "Comment cannot be empty.")
            return redirect("y_blog_detail", slug=slug)

        parent_obj = None
        if parent_id:
            try:
                parent_obj = BlogsComments.objects.get(
                    bc_comment_id=int(parent_id),
                    bc_blog=blog,
                    bc_is_deleted=0
                )
            except:
                parent_obj = None

        BlogsComments.objects.create(
            bc_blog=blog,
            bc_user_id=user_id,
            bc_comment=comment_text,
            bc_status="Approved",
            bc_created_at=timezone.now(),
            bc_is_deleted=0,
            bc_parent=parent_obj
        )

        messages.success(request, "Reply added." if parent_obj else "Comment added.")
        return redirect("y_blog_detail", slug=slug)

    return render(request, "blog/y_detail.html", {
        "blog": blog,
        "comments_roots": roots,
        "role": role,
    })

#-------------------Create--------------------------
@login_required_y
@role_required("admin", "writer")
def y_blog_create(request):
    categories = BlogsCategories.objects.filter(
        bc_category_status="Active"
    ).order_by("bc_sort_order", "bc_category_name")

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        excerpt = (request.POST.get("excerpt") or "").strip()
        content = (request.POST.get("content") or "").strip()
        category_id = request.POST.get("category_id")
        status = (request.POST.get("status") or "Draft").strip()  # Draft/Published

        if not title or not content:
            messages.error(request, "Title and Content are required.")
            return redirect("y_blog_create")

        base = make_slug(title)
        slug = unique_slug(base)

        now = timezone.now()
        BlogsDetails.objects.create(
            bd_blog_title=title,
            bd_slug=slug,
            bd_blog_content=content,
            bd_excerpt=excerpt,
            bd_category_id=int(category_id) if category_id else None,
            bd_blog_status=status,
            bd_is_deleted=0,
            bd_views=0,
            bd_updated_at=now,
            bd_published_at=now if status == "Published" else None,
            bd_date_added=now.date(),
            bd_user_id=request.session.get("user_id"),
        )

        messages.success(request, "Blog created.")
        return redirect("y_blog_detail", slug=slug)

    return render(request, "blog/y_create.html", {"categories": categories})

#-------------------------Edit---------------------------------
@login_required_y
@role_required("admin", "writer")
def y_blog_edit(request, blog_id):
    role = request.session.get("user_role")
    user_id = request.session.get("user_id")

    blog = get_object_or_404(BlogsDetails, bd_blog_id=blog_id, bd_is_deleted=0)

    if role == "writer" and blog.bd_user_id != user_id:
        messages.error(request, "You can edit only your own blogs.")
        return redirect("y_blog_detail", slug=blog.bd_slug)

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        excerpt = (request.POST.get("excerpt") or "").strip()
        content = (request.POST.get("content") or "").strip()
        category_id = request.POST.get("category_id")

        if not title or not content:
            messages.error(request, "Title and Content are required.")
            return redirect("y_blog_edit", blog_id=blog_id)

        blog.bd_blog_title = title
        blog.bd_excerpt = excerpt
        blog.bd_blog_content = content
        blog.bd_category_id = int(category_id) if category_id else blog.bd_category_id
        blog.bd_updated_at = timezone.now()
        blog.save()

        messages.success(request, "Blog updated.")
        return redirect("y_blog_detail", slug=blog.bd_slug)

    return render(request, "blog/y_edit.html", {
        "blog": blog,
        "categories": categories
    })

#-------------------------Delete---------------------------
@login_required_y
@role_required("admin", "writer")
def y_blog_delete(request, blog_id):
    role = request.session.get("user_role")
    user_id = request.session.get("user_id")

    blog = get_object_or_404(BlogsDetails, bd_blog_id=blog_id, bd_is_deleted=0)

    if role == "writer" and blog.bd_user_id != user_id:
        messages.error(request, "You can delete only your own blogs.")
        return redirect("y_blog_detail", slug=blog.bd_slug)
    
    if request.method == "POST":
        blog.bd_is_deleted = 1
        blog.bd_updated_at = timezone.now()
        blog.save(update_fields=["bd_is_deleted", "bd_updated_at"])
        messages.success(request, "Blog deleted.")
        return redirect("y_home")

    return redirect("y_blog_detail", slug=blog.bd_slug)

#---------------Dashboard-----------------
@login_required_y
def y_dashboard(request):
    role = request.session.get("user_role", "viewer")
    user_id = request.session.get("user_id")

    drafts = BlogsDetails.objects.filter(
        bd_is_deleted=0,
        bd_blog_status="Draft",
    )

    if role == "writer":
        drafts = drafts.filter(bd_user_id=user_id)

    q = (request.GET.get("q") or "").strip()
    if q:
        drafts = drafts.filter(
            Q(bd_blog_title__icontains=q) |
            Q(bd_slug__icontains=q) |
            Q(bd_excerpt__icontains=q) |
            Q(bd_blog_content__icontains=q)
        )

    drafts = drafts.order_by("-bd_updated_at", "-bd_blog_id")

    return render(request, "blog/y_dashboard.html", {
        "drafts": drafts,
        "q": q,
        "role": role,
        "email": request.session.get("user_email"),
    })

#---------------User list-------------------
@login_required_y
@role_required("admin")
def y_users(request):
    # Optional single-page form mode: ?mode=create or ?mode=edit&user_id=123
    mode = (request.GET.get("mode") or "").strip().lower() or None
    edit_user = None

    if mode == "edit":
        try:
            edit_user_id = int(request.GET.get("user_id") or 0)
        except ValueError:
            edit_user_id = 0
        if edit_user_id:
            edit_user = get_object_or_404(BlogsUsers, bu_user_id=edit_user_id)
        else:
            mode = None

    if mode not in (None, "create", "edit"):
        mode = None

    return _render_users_page(request, mode=mode, edit_user=edit_user)


#-----------------------Create user--------------------------
@login_required_y
@role_required("admin")
def y_user_create(request):
    if request.method == "POST":
        first_name = (request.POST.get("first_name") or "").strip()
        last_name = (request.POST.get("last_name") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        role = (request.POST.get("role") or "viewer").strip().lower()
        status = (request.POST.get("status") or "Active").strip()
        password = request.POST.get("password") or ""
        confirm_password = request.POST.get("confirm_password") or ""

        if role not in ("admin", "writer", "viewer"):
            role = "viewer"

        if not first_name:
            messages.error(request, "First name is required.")
            return redirect(f"{redirect('y_users').url}?mode=create")

        if not email:
            messages.error(request, "Email is required.")
            return redirect(f"{redirect('y_users').url}?mode=create")

        if not password:
            messages.error(request, "Password is required.")
            return redirect(f"{redirect('y_users').url}?mode=create")

        if password != confirm_password:
            messages.error(request, "Password and Confirm Password do not match.")
            return redirect(f"{redirect('y_users').url}?mode=create")

        if BlogsUsers.objects.filter(bu_email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect(f"{redirect('y_users').url}?mode=create")

        try:
            BlogsUsers.objects.create(
                bu_first_name=first_name,
                bu_last_name=last_name,
                bu_email=email,
                bu_password_hash=make_password(password),
                bu_role=role,
                bu_status=status,
                bu_created_at=timezone.now(),
                bu_updated_at=timezone.now(),
            )
        except IntegrityError as e:
            messages.error(request, f"Could not create user: {e}")
            return redirect(f"{redirect('y_users').url}?mode=create")

        messages.success(request, "User created successfully.")
        return redirect("y_users")

    # Render the same single users page with the create form visible
    return _render_users_page(request, mode="create")


#-----------------------Edit-----------------------------
@login_required_y
@role_required("admin")
def y_user_edit(request, user_id):
    user = get_object_or_404(BlogsUsers, bu_user_id=user_id)

    if request.method == "POST":
        first_name = (request.POST.get("first_name") or "").strip()
        last_name = (request.POST.get("last_name") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        role = (request.POST.get("role") or user.bu_role).strip().lower()
        status = (request.POST.get("status") or user.bu_status).strip()

        new_password = request.POST.get("password") or ""
        confirm_password = request.POST.get("confirm_password") or ""

        if role not in ("admin", "writer", "viewer"):
            role = user.bu_role

        if not first_name:
            messages.error(request, "First name is required.")
            return redirect(f"{redirect('y_users').url}?mode=edit&user_id={user_id}")

        if not email:
            messages.error(request, "Email is required.")
            return redirect(f"{redirect('y_users').url}?mode=edit&user_id={user_id}")

        # unique email check (exclude current)
        if BlogsUsers.objects.filter(bu_email=email).exclude(bu_user_id=user_id).exists():
            messages.error(request, "Email already exists.")
            return redirect(f"{redirect('y_users').url}?mode=edit&user_id={user_id}")

        # password change only if typed
        if new_password or confirm_password:
            if new_password != confirm_password:
                messages.error(request, "Password and Confirm Password do not match.")
                return redirect(f"{redirect('y_users').url}?mode=edit&user_id={user_id}")
            user.bu_password_hash = make_password(new_password)

        user.bu_first_name = first_name
        user.bu_last_name = last_name
        user.bu_email = email
        user.bu_role = role
        user.bu_status = status
        user.bu_updated_at = timezone.now()
        user.save()

        messages.success(request, "User updated successfully.")
        return redirect("y_users")

    # Render the same single users page with the edit form visible
    return _render_users_page(request, mode="edit", edit_user=user)


#---------------------Delete-------------------------
@login_required_y
@role_required("admin")
def y_user_delete(request, user_id):
    user = get_object_or_404(BlogsUsers, bu_user_id=user_id)

    if request.session.get("user_id") == user.bu_user_id:
        messages.error(request, "You cannot delete your own account while logged in.")
        return redirect("y_users")

    if request.method == "POST":
        user.delete()
        messages.success(request, "User deleted successfully.")
        return redirect("y_users")

    return redirect("y_users")


#-------------Category---------------
@login_required_y
@role_required("admin")
def y_categories(request):
    mode = (request.GET.get("mode") or "").strip().lower() or None
    edit_category = None

    if mode == "edit":
        try:
            cid = int(request.GET.get("category_id") or 0)
        except ValueError:
            cid = 0
        if cid:
            edit_category = get_object_or_404(BlogsCategories, bc_category_id=cid)
        else:
            mode = None

    if mode not in (None, "create", "edit"):
        mode = None

    return _render_categories_page(request, mode=mode, edit_category=edit_category)

#--------------Create-----------------
@login_required_y
@role_required("admin")
def y_category_create(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        description = (request.POST.get("description") or "").strip()
        status = (request.POST.get("status") or "Active").strip()
        sort_order = request.POST.get("sort_order") or "0"
        parent_id = request.POST.get("parent_id") or ""

        if not name:
            messages.error(request, "Category name is required.")
            return redirect(f"{redirect('y_categories').url}?mode=create")

        try:
            sort_order_int = int(sort_order)
        except ValueError:
            sort_order_int = 0

        base = _make_cat_slug(name)
        slug = _unique_cat_slug(base)

        try:
            BlogsCategories.objects.create(
                bc_category_name=name,
                bc_slug=slug,
                bc_description=description or None,
                bc_category_status=status,
                bc_parent_id=int(parent_id) if parent_id else None,
                bc_sort_order=sort_order_int,
                bc_created_at=timezone.now(),
                bc_updated_at=timezone.now(),
            )
        except IntegrityError as e:
            messages.error(request, f"Could not create category: {e}")
            return redirect(f"{redirect('y_categories').url}?mode=create")

        messages.success(request, "Category created successfully.")
        return redirect("y_categories")

    return _render_categories_page(request, mode="create")

#-------------------Edit-------------------
@login_required_y
@role_required("admin")
def y_category_edit(request, category_id):
    cat = get_object_or_404(BlogsCategories, bc_category_id=category_id)

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        description = (request.POST.get("description") or "").strip()
        status = (request.POST.get("status") or cat.bc_category_status or "Active").strip()
        sort_order = request.POST.get("sort_order") or str(cat.bc_sort_order or 0)
        parent_id = request.POST.get("parent_id") or ""

        if not name:
            messages.error(request, "Category name is required.")
            return redirect(f"{redirect('y_categories').url}?mode=edit&category_id={category_id}")

        try:
            sort_order_int = int(sort_order)
        except ValueError:
            sort_order_int = 0

        # prevent self parent
        if parent_id and int(parent_id) == cat.bc_category_id:
            messages.error(request, "Category cannot be its own parent.")
            return redirect(f"{redirect('y_categories').url}?mode=edit&category_id={category_id}")

        cat.bc_category_name = name
        cat.bc_description = description or None
        cat.bc_category_status = status
        cat.bc_sort_order = sort_order_int
        cat.bc_parent_id = int(parent_id) if parent_id else None
        cat.bc_updated_at = timezone.now()

        cat.save()
        messages.success(request, "Category updated successfully.")
        return redirect("y_categories")

    return _render_categories_page(request, mode="edit", edit_category=cat)

#-----------------Delete------------------
@login_required_y
@role_required("admin")
def y_category_delete(request, category_id):
    cat = get_object_or_404(BlogsCategories, bc_category_id=category_id)

    if request.method == "POST":
        try:
            cat.delete()
            messages.success(request, "Category deleted successfully.")
        except IntegrityError:
            # If FK constraint exists (blogs attached), make inactive instead
            cat.bc_category_status = "Inactive"
            cat.bc_updated_at = timezone.now()
            cat.save(update_fields=["bc_category_status", "bc_updated_at"])
            messages.warning(request, "Category is used in blogs, so it was marked Inactive instead.")
        return redirect("y_categories")

    return redirect("y_categories")

#----------------Profile pic---------------------
@login_required_y
def y_profile(request):
    user_id = request.session.get("user_id")
    u = get_object_or_404(BlogsUsers, bu_user_id=user_id)
    return render(request, "blog/y_profile.html", {"u": u})

#-----------------Edit---------------------------
@login_required_y
def y_profile_edit(request):
    user_id = request.session.get("user_id")
    u = get_object_or_404(BlogsUsers, bu_user_id=user_id)

    if request.method == "POST":
        first_name = (request.POST.get("first_name") or "").strip()
        last_name = (request.POST.get("last_name") or "").strip()
        username = (request.POST.get("username") or "").strip()
        bio = (request.POST.get("bio") or "").strip()

        if username:
            if BlogsUsers.objects.filter(bu_username=username).exclude(bu_user_id=user_id).exists():
                messages.error(request, "Username already taken.")
                return redirect("y_profile_edit")

        pic = request.FILES.get("profile_pic")
        if pic:
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, "profile_pics"))
            filename = fs.save(pic.name, pic)
            u.bu_profile_pic = f"profile_pics/{filename}"

        u.bu_first_name = first_name
        u.bu_last_name = last_name
        u.bu_username = username or u.bu_username
        u.bu_bio = bio or None
        u.bu_updated_at = timezone.now()
        u.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("y_profile")

    return render(request, "blog/y_profile_edit.html", {"u": u})