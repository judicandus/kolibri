"""
Update content node thumbnails and create class thumbnail marker activity.
Run inside the Docker container via: kolibri manage shell < update_thumbnails.py
"""
import hashlib
import os
import shutil
import uuid

from kolibri.core.content.models import ContentNode, File, LocalFile
from kolibri.core.lessons.models import Lesson
from kolibri.utils.conf import KOLIBRI_HOME

STORAGE_DIR = os.path.join(KOLIBRI_HOME, "content", "storage")
MEDIA_DIR = "/media/media"  # mounted volume

# Map of content node IDs to their new thumbnail images
THUMBNAIL_MAP = {
    # The Angel's Path (video)
    "07c26349741a4c1a9af42d4e527d4c26": "Angelspath.png",
    # Prologue_ The Bible as the Base (document)
    "d8fff73042a64540ba28745fddfe7376": "prologue.png",
    # The Bible as the Base (document)
    "cbd6fd3319ac457c87e0493a4442e119": "bible_horizontal.png",
    # QUIZ - The Bible as the Base (exercise)
    "bd3a51401dce447096b0575344d4ecda": "bible_horizontal.png",
}

# Class thumbnail marker
CLASS_THUMB_IMAGE = "sp.jpg"
LESSON_TITLE = "Angel's Path"
CHANNEL_ID = "db574380504e44769f73f4b09d49a29d"


def store_image(image_path):
    """Copy image to Kolibri content storage and return (md5_hash, extension, file_size)."""
    with open(image_path, "rb") as f:
        data = f.read()

    md5_hash = hashlib.md5(data).hexdigest()
    ext = os.path.splitext(image_path)[1].lstrip(".")
    file_size = len(data)

    # Storage path: storage/<first>/<second>/<hash>.<ext>
    storage_subdir = os.path.join(STORAGE_DIR, md5_hash[0], md5_hash[1])
    os.makedirs(storage_subdir, exist_ok=True)
    dest_path = os.path.join(storage_subdir, f"{md5_hash}.{ext}")
    with open(dest_path, "wb") as f:
        f.write(data)

    print(f"  Stored: {dest_path} ({file_size} bytes)")
    return md5_hash, ext, file_size


def update_thumbnail(node_id, image_filename):
    """Update thumbnail for a content node."""
    image_path = os.path.join(MEDIA_DIR, image_filename)
    if not os.path.exists(image_path):
        print(f"  ERROR: {image_path} not found!")
        return False

    md5_hash, ext, file_size = store_image(image_path)

    # Create or update LocalFile
    local_file, created = LocalFile.objects.update_or_create(
        id=md5_hash,
        defaults={
            "extension": ext,
            "file_size": file_size,
            "available": True,
        },
    )
    action = "Created" if created else "Updated"
    print(f"  {action} LocalFile: {md5_hash}")

    # Remove old thumbnail Files for this node
    old_thumbs = File.objects.filter(contentnode_id=node_id, thumbnail=True)
    count = old_thumbs.count()
    if count:
        old_thumbs.delete()
        print(f"  Deleted {count} old thumbnail File(s)")

    # Determine preset based on content kind
    node = ContentNode.objects.get(id=node_id)
    preset_map = {
        "video": "video_thumbnail",
        "document": "document_thumbnail",
        "exercise": "exercise_thumbnail",
        "html5": "html5_thumbnail",
        "audio": "audio_thumbnail",
    }
    preset = preset_map.get(node.kind, "document_thumbnail")

    # Create new thumbnail File
    file_obj = File.objects.create(
        id=uuid.uuid4().hex,
        contentnode_id=node_id,
        local_file=local_file,
        preset=preset,
        thumbnail=True,
        supplementary=True,
        priority=0,
    )
    print(f"  Created File: {file_obj.id} (preset={preset})")
    return True


def create_class_thumb_marker():
    """Create a __class_thumb__ marker ContentNode and add to lesson."""
    print("\n=== Creating class thumbnail marker ===")

    image_path = os.path.join(MEDIA_DIR, CLASS_THUMB_IMAGE)
    if not os.path.exists(image_path):
        print(f"  ERROR: {image_path} not found!")
        return False

    # Check if marker already exists
    existing = ContentNode.objects.filter(title="__class_thumb__", channel_id=CHANNEL_ID)
    if existing.exists():
        print(f"  Marker already exists: {existing.first().id}")
        node = existing.first()
    else:
        # Find the lesson's parent topic to place the marker under
        lesson = Lesson.objects.get(title=LESSON_TITLE)
        # Get the first resource's parent as the topic
        first_resource_id = lesson.resources[0]["contentnode_id"]
        first_node = ContentNode.objects.get(id=first_resource_id)
        parent = first_node.parent

        # Create a new content node
        node_id = uuid.uuid4().hex
        node = ContentNode.objects.create(
            id=node_id,
            title="__class_thumb__",
            content_id=uuid.uuid4().hex,
            channel_id=CHANNEL_ID,
            kind="document",
            available=True,
            parent=parent,
            sort_order=9999,
            coach_content=False,
            lang_id="en",
            options="{}",
            lft=0,
            rght=0,
            tree_id=first_node.tree_id,
            level=first_node.level,
        )
        print(f"  Created ContentNode: {node.id}")

    # Store the thumbnail image
    md5_hash, ext, file_size = store_image(image_path)

    local_file, _ = LocalFile.objects.update_or_create(
        id=md5_hash,
        defaults={"extension": ext, "file_size": file_size, "available": True},
    )

    # Remove old thumbnail
    File.objects.filter(contentnode=node, thumbnail=True).delete()

    File.objects.create(
        id=uuid.uuid4().hex,
        contentnode=node,
        local_file=local_file,
        preset="document_thumbnail",
        thumbnail=True,
        supplementary=True,
        priority=0,
    )
    print(f"  Thumbnail set for marker node")

    # Add to lesson resources if not already there
    lesson = Lesson.objects.get(title=LESSON_TITLE)
    resources = lesson.resources
    marker_in_lesson = any(r["contentnode_id"] == node.id for r in resources)
    if not marker_in_lesson:
        resources.append({
            "contentnode_id": node.id,
            "content_id": node.content_id,
            "channel_id": CHANNEL_ID,
        })
        lesson.resources = resources
        lesson.save()
        print(f"  Added marker to lesson '{LESSON_TITLE}'")
    else:
        print(f"  Marker already in lesson")

    return True


# Main execution
print("=== Updating activity thumbnails ===")
for node_id, image_file in THUMBNAIL_MAP.items():
    node = ContentNode.objects.get(id=node_id)
    print(f"\n{node.title} ({node.kind}):")
    update_thumbnail(node_id, image_file)

create_class_thumb_marker()

print("\n=== Done! ===")
