from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AuditLog, Document


@receiver(post_save, sender=Document)
def write_document_audit_log(sender, instance, created, **kwargs):
    is_create = instance._state.adding or created
    AuditLog.objects.create(
        actor=instance.created_by,
        action='created' if is_create else 'updated',
        model_name='Document',
        object_id=str(instance.id),
    )