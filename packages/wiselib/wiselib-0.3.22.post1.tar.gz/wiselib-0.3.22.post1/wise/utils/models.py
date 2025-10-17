import logging
import uuid

from django.db import models

_logger = logging.getLogger(__name__)


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class BaseModel(models.Model):
    key = models.UUIDField(
        default=uuid.uuid4, primary_key=True, editable=False, db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    objects = models.Manager()
    active_objects = ActiveManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)

            meta_options_to_merge = [
                "constraints",
                "ordering",
                "indexes",
                "unique_together",
            ]

            # Merge specific Meta options from BaseModel.Meta
            for option in meta_options_to_merge:
                base_value = getattr(BaseModel.Meta, option, None)
                if base_value is None:
                    continue

                child_value = getattr(cls, option, None)

                if child_value is not None:
                    if isinstance(base_value, (list, tuple)):
                        merged_value = list(child_value) + [
                            item for item in base_value if item not in child_value
                        ]
                        setattr(cls, option, merged_value)
                    else:
                        logging.warning(
                            f"Meta option {option} is not a list or tuple, skipping merge"
                        )
                else:
                    setattr(cls, option, base_value)

    def __str__(self) -> str:
        return str(self.key)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
