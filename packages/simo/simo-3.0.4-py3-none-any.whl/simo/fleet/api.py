import json
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets
from rest_framework.response import Response as RESTResponse
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as APIValidationError
from simo.core.api import InstanceMixin
from simo.core.permissions import IsInstanceSuperuser
from .models import InstanceOptions, Colonel, Interface
from .serializers import (
    InstanceOptionsSerializer, ColonelSerializer, ColonelInterfaceSerializer
)


class InstanceOptionsViewSet(InstanceMixin, viewsets.ReadOnlyModelViewSet):
    url = 'fleet/options'
    basename = 'options'
    serializer_class = InstanceOptionsSerializer

    def get_queryset(self):
        return InstanceOptions.objects.filter(instance=self.instance)


class ColonelsViewSet(InstanceMixin, viewsets.ModelViewSet):
    url = 'fleet/colonels'
    basename = 'colonels'
    serializer_class = ColonelSerializer

    def get_permissions(self):
        permissions = super().get_permissions()
        permissions.append(IsInstanceSuperuser())
        return permissions

    def get_queryset(self):
        return Colonel.objects.filter(instance=self.instance)

    @action(detail=True, methods=['post'])
    def check_for_upgrade(self, request, pk=None, *args, **kwargs):
        colonel = self.get_object()
        colonel.check_for_upgrade()
        return RESTResponse({'status': 'success'})

    @action(detail=True, methods=['post'])
    def upgrade(self, request, pk=None, *args, **kwargs):
        colonel = self.get_object()
        if colonel.major_upgrade_available:
            colonel.update_firmware(colonel.major_upgrade_available)
        elif colonel.minor_upgrade_available:
            colonel.update_firmware(colonel.minor_upgrade_available)
        return RESTResponse({'status': 'success'})

    @action(detail=True, methods=['post'])
    def restart(self, request, pk=None, *args, **kwargs):
        colonel = self.get_object()
        colonel.restart()
        return RESTResponse({'status': 'success'})

    @action(detail=True, methods=['post'])
    def update_config(self, request, pk=None, *args, **kwargs):
        colonel = self.get_object()
        colonel.update_config()
        return RESTResponse({'status': 'success'})

    @action(detail=True, methods=['post'])
    def move_to(self, request, pk, *args, **kwargs):
        colonel = self.get_object()
        data = json.loads(request.body)

        target = Colonel.objects.annotate(
            components_count=Count('components')
        ).filter(
            pk=data.get('target'), instance=self.instance,
            components_count=0, type=colonel.type
        ).first()
        if not target:
            raise APIValidationError(_('Invalid target.'), code=400)
        colonel.move_to(target)
        return RESTResponse({'status': 'success'})

    def perform_destroy(self, instance):
        if instance.components.all().count():
            raise APIValidationError(
                _('Deleting colonel which has components is not allowed!'),
                code=400
            )
        instance.delete()


class InterfaceViewSet(
    InstanceMixin,
    viewsets.mixins.RetrieveModelMixin, viewsets.mixins.UpdateModelMixin,
    viewsets.mixins.ListModelMixin, viewsets.GenericViewSet
):
    url = 'fleet/colonel-interfaces'
    basename = 'colonel-interfaces'
    serializer_class = ColonelInterfaceSerializer

    def get_permissions(self):
        permissions = super().get_permissions()
        permissions.append(IsInstanceSuperuser())
        return permissions

    def get_queryset(self):
        return Interface.objects.filter(colonel__instance=self.instance)

