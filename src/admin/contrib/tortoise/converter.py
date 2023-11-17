from typing import Type, Sequence, Any, Callable, Dict

import starlette_admin.fields as sa
import tortoise.fields as t
from starlette_admin.converters import BaseModelConverter, converts
from tortoise import ForeignKeyFieldInstance, OneToOneFieldInstance, Model
from tortoise.fields.data import CharEnumFieldInstance, IntEnumFieldInstance


class BaseTortoiseModelConverter(BaseModelConverter):
    def get_converter(self, field: t.Field) -> Callable[..., sa.BaseField]:
        if field.__class__ in self.converters:
            return self.converters[field.__class__]
        for cls, converter in self.converters.items():
            if isinstance(field, cls):
                return converter
        raise Exception(
            f"{field.model.__name__}.{field.model_field_name} ({field.__class__.__name__}) "
            f"can not be converted automatically. Find the appropriate field "
            "manually or provide your custom converter"
        )

    def convert(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return self.get_converter(kwargs.get("field"))(*args, **kwargs)

    def convert_fields_list(
            self,
            *,
            fields: Sequence[Any],
            model: Type[Model],
            **kwargs: Any
    ) -> Sequence[sa.BaseField]:
        # print('start convert fields for model', model.__name__)
        converted_fields = []
        for value in fields:
            # print(f'\tsearching field {model.__name__}.{value}')

            if isinstance(value, sa.BaseField):
                converted_fields.append(value)
            elif isinstance(value, str):
                field = model._meta.fields_map.get(value)
                if field is not None:
                    # print(f'\tfound {model.__name__}.{value} {field}')
                    converted_fields.append(self.convert(field=field))
                else:
                    raise ValueError(f'Cant find field {model.__name__}.{value}')

        return converted_fields


class ModelConverter(BaseTortoiseModelConverter):
    @classmethod
    def _field_common(cls, *, field: t.Field, **kwargs: Any) -> Dict[str, Any]:
        return {
            "name": field.model_field_name,
            "help_text": field.description,
            "required": field.required,
        }

    @classmethod
    def _numeric_field_common(
            cls, *, field: t.Field, **kwargs: Any
    ) -> Dict[str, Any]:
        return {
            "min": getattr(field, "min_value", None),
            "max": getattr(field, "max_value", None),
        }

    @converts(t.CharField, t.UUIDField)
    def conv_string_field(self, *args: Any, **kwargs) -> sa.BaseField:
        return sa.StringField(**self._field_common(*args, **kwargs))

    @converts(t.IntField, t.BigIntField, t.SmallIntField)
    def conv_int_field(self, *args: Any, **kwargs) -> sa.BaseField:
        return sa.IntegerField(
            **self._field_common(*args, **kwargs),
            **self._numeric_field_common(*args, **kwargs)
        )

    @converts(t.FloatField)
    def conv_float_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.FloatField(**self._field_common(*args, **kwargs))

    @converts(t.DecimalField)
    def conv_decimal_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.DecimalField(
            **self._field_common(*args, **kwargs),
            **self._numeric_field_common(*args, **kwargs),
        )

    @converts(t.BooleanField)
    def conv_boolean_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.BooleanField(**self._field_common(*args, **kwargs))

    @converts(t.DatetimeField)
    def conv_datetime_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.DateTimeField(**self._field_common(*args, **kwargs))

    @converts(t.DateField)
    def conv_date_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.DateField(**self._field_common(*args, **kwargs))

    # NOT FIELD
    def conv_email_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.EmailField(**self._field_common(*args, **kwargs))

    # NOT FIELD
    def conv_url_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.URLField(**self._field_common(*args, **kwargs))

    # NOT FIELD
    def conv_file_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        # return internal_fields.FileField(**self._field_common(*args, **kwargs))
        raise NotImplemented

    # NOT FIELDS
    def conv_image_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        # return internal_fields.ImageField(**self._field_common(*args, **kwargs))
        raise NotImplemented

    @converts(CharEnumFieldInstance, IntEnumFieldInstance)
    def conv_enum_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        field = kwargs['field']
        return sa.EnumField(**self._field_common(*args, **kwargs), enum=field.enum_type)

    @converts(ForeignKeyFieldInstance)
    def conv_reference_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        field = kwargs['field']
        identity = field.related_model._meta.db_table  # not tested
        return sa.HasOne(**self._field_common(*args, **kwargs), identity=identity)

    @converts(t.JSONField)
    def conv_json(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.JSONField(**self._field_common(*args, **kwargs))

    @converts(t.BinaryField)
    def conv_binary(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.TextAreaField(**self._field_common(*args, **kwargs))

    @converts(t.TextField)
    def conv_text_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.TextAreaField(**self._field_common(*args, **kwargs))

    @converts(OneToOneFieldInstance)
    def conv_one_to_one_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        field = kwargs['field']
        identity = field.related_model._meta.db_table  # not tested
        return sa.HasOne(**self._field_common(*args, **kwargs), identity=identity)

    # @converts(ManyToManyRelation)
    # def conv_many_to_many_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
    #     field = kwargs['field']
    #     print(field)
    #     identity = field.related_model._meta.db_table
    #     print('m2m conv >> ', field, identity)
    #     return sa.HasMany(**self._field_common(*args, **kwargs), identity=identity)
    #
    # @converts(BackwardFKRelation)
    # def conv_back_fk_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
    #     field = kwargs['field']
    #     identity = field.related_model._meta.db_table
    #     # return sa.HasMany(**self._field_common(*args, **kwargs), identity=identity)
    #     return sa.ListField(self.convert(*args, field=ManyToManyRelation), required=field.required)
