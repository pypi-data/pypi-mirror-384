_patches_run = False


def run_patches():
    global _patches_run
    if not _patches_run:
        from .drf_serializers import patch_drf_fields

        patch_drf_fields()
        _patches_run = True


__all__ = ["run_patches"]
