from typing import Type, Any, Dict, List, Sequence, Optional, Union, Set

from starlette.requests import Request
from starlette_admin import BaseModelView, fields
from starlette_admin.exceptions import FormValidationError
from starlette_admin.helpers import prettify_class_name
from tortoise import Model
from tortoise.exceptions import BaseORMException
from tortoise.expressions import Q
from tortoise.models import MODEL

from .converter import ModelConverter


class ModelView(BaseModelView):
    model: Type[MODEL]

    def __init__(
            self,
            model: Optional[Type[Model]] = None,
            icon: Optional[str] = None,
            name: Optional[str] = None,
            label: Optional[str] = None,
            identity: Optional[str] = None,
    ):
        self.model = model or self.model
        self.identity = (
                identity or self.identity or self.model._meta.db_table
        )
        print('>>>>>>', self.identity)
        self.label = (
                label or self.label or prettify_class_name(self.model.__name__) + "s"
        )
        self.name = name or self.name or prettify_class_name(self.model.__name__)
        self.icon = icon or self.icon
        self.pk_attr = self.model._meta.pk_attr
        if self.fields is None or len(self.fields) == 0:
            self.fields = self.model._meta.fields

        self.fields = ModelConverter().convert_fields_list(
            fields=self.fields, model=self.model
        )
        super().__init__()

    def get_queryset(self):
        queryset = self.model.all()
        return queryset

    def resolve_order_by(self, order_by: Optional[List[str]] = None):
        orderings = set()

        for name, direction in [o.split(maxsplit=1) for o in order_by]:
            if direction == 'asc':
                orderings.add(name)
            elif direction == 'desc':
                orderings.add(f'-{name}')
            else:
                raise Exception(f'Unknown "order_by" value "{order_by}"')

        return orderings

    def resolve_query(self, where: Union[Dict[str, Any], str, None] = None) -> Q:
        if where is None:
            return Q()
        if isinstance(where, dict):
            return self.resolve_deep_query(where)
        else:
            return self.resolve_text_search(where)

    def resolve_text_search(self, where: str):
        conditions: List[Q] = []
        for field in self.fields:
            if (
                    field.searchable
                    and field.name in self.model._meta.fields
                    and field.name != "id"
                    and type(field) in [
                fields.StringField,
                fields.TextAreaField,
                fields.EmailField,
                fields.URLField,
                fields.PhoneField,
                fields.ColorField,
            ]
            ):
                q = f'{field.name}__contains'
                conditions.append(Q(**{q: where}))
        return Q(*conditions, join_type='OR')

    def resolve_deep_query(self, where: Dict[str, Any] = None):
        raise NotImplemented

    async def find_all(
            self,
            request: Request,
            skip: int = 0,
            limit: int = 100,
            where: Union[Dict[str, Any], str, None] = None,
            order_by: Optional[List[str]] = None
    ) -> Sequence[Any]:
        query = self.resolve_query(where)
        order_by = self.resolve_order_by(order_by)
        queryset = self.get_queryset().filter(query).order_by(*order_by).offset(skip).limit(limit)
        return await queryset

    async def count(self, request: Request, where: Union[Dict[str, Any], str, None] = None) -> int:
        query = self.resolve_query(where)
        queryset = self.model.filter(query)
        return await queryset.count()

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        query = {f'{self.pk_attr}__in': pks}
        return await self.model.filter(**query).delete()

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        query = {self.pk_attr: pk}
        queryset = self.get_queryset().get(**query)
        return await queryset

    async def find_by_pks(self, request: Request, pks: List[Any]) -> Sequence[Any]:
        query = {f'{self.pk_attr}__in': pks}
        queryset = self.get_queryset().filter(**query).all()
        return await queryset

    def ensure_model_data(self, data: Dict) -> Dict:
        validated_data = {}
        for key, value in data.items():
            if key not in self.model._meta.fk_fields:
                validated_data.setdefault(key, value)
            else:  # field is fk
                field = self.model._meta.fields_map[key]
                validated_data.setdefault(field.source_field, value)

        # validated_data = dict(filter(lambda item: item[1] is not None, validated_data.items()))
        return validated_data

    async def create(self, request: Request, data: Dict) -> Any:
        data = self.ensure_model_data(data)
        return await self.model.create(**data)

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        try:
            query = {self.pk_attr: pk}
            obj = await self.model.get(**query)
            data = self.ensure_model_data(data)
            await obj.update_from_dict(data).save()
            return await self.find_by_pk(request, pk)
        except Exception as e:
            self.handle_exception(e)

    def handle_exception(self, exc: Exception) -> None:
        if isinstance(exc, BaseORMException):
            raise FormValidationError({'error': str(exc)})
        raise exc
