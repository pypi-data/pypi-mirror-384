from django.apps import apps

from . import settings, autocomplete_serializers, viewsets

for app in settings['APPS']:
    for name, model in apps.all_models[app].items():
        model_name = model.__name__
        if isinstance(model, type):
            viewset_name = f"{model_name}ViewSet"
            if not viewset_name in dir():
                generated_class = type(viewset_name, (viewsets.GenericAutocompleteViewSet,), {
                    'model_name': model_name,
                    'app': app,
                    'serializer_class': getattr(autocomplete_serializers, f"{model_name}Serializer"),
                })
                globals()[viewset_name] = generated_class