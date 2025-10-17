import logging
from typing import Dict, List

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListCreateAPIView, ListAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework.views import status
from django.db.models import Count, Q

from .utils import LookupFieldMixin, JSONFieldFilterBackend
from .exceptions import BulkError
from .utils import assert_valid
from .models import MappingSetting, Mapping, ExpenseAttribute, DestinationAttribute, EmployeeMapping, \
    CategoryMapping, ExpenseField
from .serializers import ExpenseAttributeMappingSerializer, MappingSettingSerializer, MappingSerializer, \
    EmployeeMappingSerializer, CategoryMappingSerializer, DestinationAttributeSerializer, \
    EmployeeAttributeMappingSerializer, ExpenseFieldSerializer, CategoryAttributeMappingSerializer, \
    FyleFieldsSerializer

from .helpers import ExpenseAttributeFilter, DestinationAttributeFilter

logger = logging.getLogger(__name__)


class MappingSettingsView(ListCreateAPIView, DestroyAPIView):
    """
    Mapping Settings VIew
    """
    serializer_class = MappingSettingSerializer

    def get_queryset(self):
        return MappingSetting.objects.filter(workspace_id=self.kwargs['workspace_id']).order_by('updated_at')

    def post(self, request, *args, **kwargs):
        """
        Post mapping settings
        """
        try:
            mapping_settings: List[Dict] = request.data

            assert_valid(mapping_settings != [], 'Mapping settings not found')

            mapping_settings = MappingSetting.bulk_upsert_mapping_setting(mapping_settings, self.kwargs['workspace_id'])

            return Response(data=self.serializer_class(mapping_settings, many=True).data, status=status.HTTP_200_OK)
        except BulkError as exception:
            logger.error(exception.response)
            return Response(
                data=exception.response,
                status=status.HTTP_400_BAD_REQUEST
            )


class MappingsView(ListCreateAPIView):
    """
    Mapping Settings VIew
    """
    serializer_class = MappingSerializer

    def get_queryset(self):
        source_type = self.request.query_params.get('source_type')
        destination_type = self.request.query_params.get('destination_type')
        source_active = self.request.query_params.get('source_active')

        assert_valid(source_type is not None, 'query param source type not found')

        if int(self.request.query_params.get('table_dimension')) == 3:
            mappings = Mapping.objects.filter(source_id__in=Mapping.objects.filter(
                source_type=source_type, workspace_id=self.kwargs['workspace_id']).values('source_id').annotate(
                    count=Count('source_id')).filter(count=2).values_list('source_id'))
        else:
            params = {
                'source_type': source_type,
                'workspace_id': self.kwargs['workspace_id']
            }
            if destination_type:
                params['destination_type'] = destination_type

            if source_active and source_active == 'true':
                params['source__active'] = True

            mappings = Mapping.objects.filter(**params)

        return mappings.order_by('source__value')

    def post(self, request, *args, **kwargs):
        """
        Post mapping settings
        """
        source_type = request.data.get('source_type', None)

        assert_valid(source_type is not None, 'source type not found')

        destination_type = request.data.get('destination_type', None)

        assert_valid(destination_type is not None, 'destination type not found')

        source_value = request.data.get('source_value', None)

        destination_value = request.data.get('destination_value', None)

        destination_id = request.data.get('destination_id', None)

        app_name = request.data.get('app_name', None)

        assert_valid(destination_value is not None, 'destination value not found')
        try:
            mappings = Mapping.create_or_update_mapping(
                source_type=source_type,
                destination_type=destination_type,
                source_value=source_value,
                destination_value=destination_value,
                destination_id=destination_id,
                app_name=app_name,
                workspace_id=self.kwargs['workspace_id']
            )

            return Response(data=self.serializer_class(mappings).data, status=status.HTTP_200_OK)
        except ExpenseAttribute.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'message': 'Fyle {0} with name {1} does not exist'.format(source_type, source_value)
                }
            )
        except DestinationAttribute.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'message': 'Destination {0} with name {1} does not exist'.format(
                        destination_type, destination_value)
                }
            )


class EmployeeMappingsView(ListCreateAPIView):
    """
    Employee Mappings View
    """
    serializer_class = EmployeeMappingSerializer

    def get_queryset(self):
        return EmployeeMapping.objects.filter(
            workspace_id=self.kwargs['workspace_id']
        ).all().order_by('source_employee__value')


class CategoryMappingsView(ListCreateAPIView):
    """
    Category Mappings View
    """
    serializer_class = CategoryMappingSerializer

    def get_queryset(self):
        source_active = self.request.query_params.get('source_active')

        params = {}
        if source_active and source_active == 'true':
            params['source_category__active'] = True

        return CategoryMapping.objects.filter(
            workspace_id=self.kwargs['workspace_id'], **params
        ).all().order_by('source_category__value')


class SearchDestinationAttributesView(ListCreateAPIView):
    """
    Search Destination Attributes View
    """
    serializer_class = DestinationAttributeSerializer

    def get_queryset(self):
        destination_attribute_type = self.request.query_params.get('destination_attribute_type')
        destination_attribute_value = self.request.query_params.get('destination_attribute_value')

        assert_valid(destination_attribute_value is not None, 'query param destination_attribute_value not found')
        assert_valid(destination_attribute_type is not None, 'query param destination_attribute_type not found')

        destination_attributes = DestinationAttribute.objects.filter(
            value__icontains=destination_attribute_value,
            attribute_type=destination_attribute_type,
            workspace_id=self.kwargs['workspace_id']
        ).all()
        return destination_attributes


class MappingStatsView(ListCreateAPIView):
    """
    Stats for total mapped and unmapped count for a given attribute type
    """
    def get(self, request, *args, **kwargs):
        source_type = self.request.query_params.get('source_type')
        destination_type = self.request.query_params.get('destination_type')
        app_name = self.request.query_params.get('app_name', None)

        assert_valid(source_type is not None, 'query param source_type not found')
        assert_valid(destination_type is not None, 'query param destination_type not found')

        filters = {
            'attribute_type': source_type,
            'workspace_id': self.kwargs['workspace_id']
        }

        if source_type in ('PROJECT', 'CATEGORY') or app_name in ['Sage 300 CRE', 'QuickBooks Desktop Connector', 'Netsuite', 'Xero', 'QuickBooks Online', 'Sage Intacct', 'Sage 50 Accounting (US)']:
            filters['active'] = True

        total_attributes_count = ExpenseAttribute.objects.filter(**filters).count()

        if source_type == 'EMPLOYEE':
            filters = {}

            if destination_type == 'VENDOR':
                filters['destination_vendor__attribute_type'] = destination_type
            else:
                filters['destination_employee__attribute_type'] = destination_type

            if app_name == 'XERO':
                mapped_attributes_count = Mapping.objects.filter(
                    workspace_id=self.kwargs['workspace_id'], source_type='EMPLOYEE'
                ).count()
            else:
                mapped_attributes_count = EmployeeMapping.objects.filter(
                    **filters, workspace_id=self.kwargs['workspace_id']
                ).count()
        elif source_type == 'CATEGORY' and app_name in ['Sage Intacct', 'Sage 300 CRE', 'Dynamics 365 Business Central', 'NetSuite']:
            filters = {}

            if destination_type == 'ACCOUNT':
                filters['destination_account__attribute_type'] = destination_type
            else:
                filters['destination_expense_head__attribute_type'] = destination_type

            filters['source_category__active'] = True

            mapped_attributes_count = CategoryMapping.objects.filter(
                **filters, workspace_id=self.kwargs['workspace_id']
            ).count()
        else:
            filters = {
                'source_type': source_type,
                'destination_type': destination_type,
                'workspace_id': self.kwargs['workspace_id']
            }
            if app_name == 'QuickBooks Online' and source_type == 'CORPORATE_CARD':
                filters.pop('destination_type')
                filters['destination_type__in'] = ['CREDIT_CARD_ACCOUNT', 'BANK_ACCOUNT']

            if source_type in ('PROJECT', 'CATEGORY') or app_name in ['Sage 300 CRE', 'QuickBooks Desktop Connector', 'NetSuite', 'Xero', 'QuickBooks Online', 'Sage Intacct', 'Sage 50 Accounting (US)']:
                filters['source__active'] = True

            mapped_attributes_count = Mapping.objects.filter(**filters).count()
            activity_mapping = None

        if source_type == 'CATEGORY':
            activity_attribute_count = ExpenseAttribute.objects.filter(
                attribute_type='CATEGORY', value='Activity', workspace_id=self.kwargs['workspace_id'], active=True).count()
            
            if app_name in ('NetSuite', 'Sage Intacct', 'Sage 300 CRE', 'Dynamics 365 Business Central'):
                activity_mapping = CategoryMapping.objects.filter(
                    source_category__value='Activity', workspace_id=self.kwargs['workspace_id']).first()
            else:
                activity_mapping = Mapping.objects.filter(
                    source_type='CATEGORY', source__value='Activity', workspace_id=self.kwargs['workspace_id']).first()

            if activity_attribute_count and not activity_mapping:
                mapped_attributes_count += activity_attribute_count

        return Response(
            data={
                'all_attributes_count': total_attributes_count,
                'unmapped_attributes_count': total_attributes_count - mapped_attributes_count
            },
            status=status.HTTP_200_OK
        )


class ExpenseAttributesMappingView(ListAPIView):
    serializer_class = ExpenseAttributeMappingSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ExpenseAttributeFilter


    def get_serializer_context(self):
        context = super().get_serializer_context()

        source_type = self.request.query_params.get('source_type')
        app_name = self.request.query_params.get('app_name')
        destination_type = self.request.query_params.get('destination_type', '')

        if app_name == 'QuickBooks Online' and source_type == 'CORPORATE_CARD':
            destination_type_list = ['CREDIT_CARD_ACCOUNT', 'BANK_ACCOUNT']
        else:
            destination_type_list = [destination_type]

        context['destination_type_list'] = destination_type_list
        return context

    def get_queryset(self):
        mapped = self.request.query_params.get('mapped')
        source_type = self.request.query_params.get('source_type')
        destination_type = self.request.query_params.get('destination_type', '')
        destination_type = [destination_type]

        app_name = self.request.query_params.get('app_name', None)

        # Process the 'mapped' parameter
        if mapped and mapped.lower() == 'false':
            mapped = False
        elif mapped and mapped.lower() == 'true':
            mapped = True
        else:
            mapped = None

        # Prepare filters for the ExpenseAttribute
        base_filters = Q(workspace_id=self.kwargs['workspace_id']) & Q(attribute_type=source_type)

        if source_type in ('PROJECT', 'CATEGORY') or app_name in ['Sage 300 CRE', 'QuickBooks Desktop Connector', 'NetSuite', 'Xero', 'QuickBooks Online', 'Sage Intacct', 'Sage 50 Accounting (US)']:
            base_filters &= Q(active=True)

        # Handle Activity attribute if attribute mapping is present then show mappings else don't return Activity attribute
        if source_type == 'CATEGORY':
            activity_mapping = Mapping.objects.filter(
                source__value='Activity', source_type='CATEGORY', workspace_id=self.kwargs['workspace_id']).first()
            activity_attribute = ExpenseAttribute.objects.filter(
                attribute_type='CATEGORY', value='Activity', workspace_id=self.kwargs['workspace_id'], active=True).first()

            # Adjust the filters if 'Activity' attribute exists but not mapped
            if activity_attribute and not activity_mapping:
                base_filters &= ~Q(value='Activity')

        
        if app_name == 'QuickBooks Online' and source_type == 'CORPORATE_CARD':
            destination_type = ['CREDIT_CARD_ACCOUNT', 'BANK_ACCOUNT']
        
        # Handle the 'mapped' parameter
        param = None
        if mapped is True:
            param = Q(mapping__destination_type__in=destination_type)
        elif mapped is False:
            param = ~Q(mapping__destination_type__in=destination_type)
        else:
            return ExpenseAttribute.objects.filter(base_filters).order_by('value')

        # Combine the base filters with the param (if any)
        final_filter = base_filters
        if param:
            final_filter &= param

        # Return the final queryset
        return ExpenseAttribute.objects.filter(final_filter).order_by('value')


class CategoryAttributesMappingView(ListAPIView):
    """
    Category Mapping View
    """
    serializer_class = CategoryAttributeMappingSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ExpenseAttributeFilter

    def get_queryset(self):
        mapped = self.request.query_params.get('mapped')
        destination_type = self.request.query_params.get('destination_type', '')

        # Process the 'mapped' parameter
        if mapped and mapped.lower() == 'false':
            mapped = False
        elif mapped and mapped.lower() == 'true':
            mapped = True
        else:
            mapped = None

        # Prepare filters based on destination_type
        filters = {}

        if destination_type == 'ACCOUNT':
            filters['destination_account__attribute_type'] = destination_type
        else:
            filters['destination_expense_head__attribute_type'] = destination_type

        # Get source categories
        source_categories = CategoryMapping.objects.filter(
            **filters,
            source_category__active=True,
            workspace_id=self.kwargs['workspace_id'],
        ).values_list('source_category_id', flat=True)

        # Prepare filters for ExpenseAttribute
        base_filters = Q(workspace_id=self.kwargs['workspace_id']) & \
            Q(attribute_type='CATEGORY') & \
            Q(active=True)

        # Get the 'Activity' mapping and attribute
        activity_mapping = CategoryMapping.objects.filter(
            source_category__value='Activity', workspace_id=self.kwargs['workspace_id']).first()
        activity_attribute = ExpenseAttribute.objects.filter(
            attribute_type='CATEGORY', value='Activity', workspace_id=self.kwargs['workspace_id'], active=True).first()

        # Adjust the filters if 'Activity' attribute exists but not mapped
        if activity_attribute and not activity_mapping:
            base_filters &= ~Q(value='Activity')

        # Handle the mapped parameter
        param = None
        if mapped is True:
            param = Q(categorymapping__source_category_id__in=source_categories)
        elif mapped is False:
            param = ~Q(categorymapping__source_category_id__in=source_categories)
        else:
            return ExpenseAttribute.objects.filter(base_filters).order_by('value')

        # Combine the base filters with the param (if any)
        final_filter = base_filters
        if param:
            final_filter &= param

        # Return the final queryset
        return ExpenseAttribute.objects.filter(final_filter).order_by('value')


class EmployeeAttributesMappingView(ListAPIView):

    serializer_class = EmployeeAttributeMappingSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ExpenseAttributeFilter

    def get_queryset(self):
        mapped = self.request.query_params.get('mapped')
        destination_type = self.request.query_params.get('destination_type', '')

        if mapped and mapped.lower() == 'false':
            mapped = False
        elif mapped and mapped.lower() == 'true':
            mapped = True
        else:
            mapped = None

        filters = {}

        if destination_type == 'VENDOR':
            filters['destination_vendor__attribute_type'] = destination_type
        else:
            filters['destination_employee__attribute_type'] = destination_type

        source_employees = EmployeeMapping.objects.filter(
            **filters,
            workspace_id=self.kwargs['workspace_id'],
        ).values_list('source_employee_id', flat=True)

        filters = {
            'workspace_id': self.kwargs['workspace_id'],
            'attribute_type': 'EMPLOYEE'
        }

        param = None
        if mapped:
            param = Q(employeemapping__source_employee_id__in=source_employees)
        elif mapped is False:
            param = ~Q(employeemapping__source_employee_id__in=source_employees)
        else:
            return ExpenseAttribute.objects.filter(Q(**filters)).order_by('value')
        final_filter = Q(**filters)
        if param:
            final_filter = final_filter & param
        return ExpenseAttribute.objects.filter(final_filter).order_by('value')


class ExpenseFieldView(ListAPIView):
    """
    Expense Field View
    """
    serializer_class = ExpenseFieldSerializer

    def get_queryset(self):
        return ExpenseField.objects.filter(
            workspace_id=self.kwargs['workspace_id']
        ).all()


class DestinationAttributesView(LookupFieldMixin, ListAPIView):
    """
    Destination Attributes view
    """

    queryset = DestinationAttribute.objects.all().order_by('value')
    serializer_class = DestinationAttributeSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend, JSONFieldFilterBackend,)
    filterset_fields = {'attribute_type': {'exact', 'in'}, 'display_name': {'exact', 'in'}, 'active': {'exact'}, 'destination_id': {'exact', 'in'}}


class FyleFieldsView(ListAPIView):
    """
    Fyle Fields view
    """

    serializer_class = FyleFieldsSerializer
    pagination_class = None

    def get_queryset(self):
        return FyleFieldsSerializer().format_fyle_fields(self.kwargs["workspace_id"])


class PaginatedDestinationAttributesView(LookupFieldMixin, ListAPIView):
    """
    Paginated Destination Attributes view
    """
    queryset = DestinationAttribute.objects.filter(active=True).order_by('value')
    serializer_class = DestinationAttributeSerializer
    filter_backends = (DjangoFilterBackend, JSONFieldFilterBackend,)
    filterset_class = DestinationAttributeFilter


class DestinationAttributesStatsView(LookupFieldMixin, ListAPIView):
    """
    Destination Attributes Stats view
    """
    def get(self, request, *args, **kwargs):
        attribute_type = self.request.query_params.get('attribute_type')
        display_name = self.request.query_params.get('display_name', None)
        assert_valid(attribute_type is not None, 'query param attribute_type not found')

        filters = {
            'attribute_type': attribute_type,
            'workspace_id': self.kwargs['workspace_id']
        }

        if display_name:
            filters['display_name'] = display_name

        query = DestinationAttribute.objects.filter(**filters)

        total_attributes_count = query.count()
        active_attributes_count = query.filter(active=True).count()
        inactive_attributes_count = total_attributes_count - active_attributes_count

        return Response(
            data={
                'attributes_count': total_attributes_count,
                'active_attributes_count': active_attributes_count,
                'inactive_attributes_count': inactive_attributes_count
            },
            status=status.HTTP_200_OK
        )
