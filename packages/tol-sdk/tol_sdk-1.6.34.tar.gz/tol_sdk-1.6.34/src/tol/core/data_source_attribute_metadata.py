# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Optional, Type

from cachetools.func import ttl_cache

from .attribute_metadata import (AttributeMetadata, DefaultAttributeMetadata)
from .data_object import DataObject


def data_source_attribute_metadata(
    data_source_config: DataObject,
) -> Type[AttributeMetadata]:
    """
    Takes a DataSourceConfig, and creates an AbstractMetadata
    implementation that refers to all of the child DataSourceConfigAttributes.
    """

    class DataSourceAttributeMetadata(DefaultAttributeMetadata):
        """
        AbstractMetadata that gets its info from one or more DataSources
        """
        @ttl_cache(ttl=3600)
        def __read_attributes_from_datasource(self):
            ret = {}
            # Recreate the data_source_config
            dsc = data_source_config._host.get_one(
                'data_source_config', data_source_config.id
            )
            for attribute in dsc.data_source_config_attributes:
                if attribute.object_type not in ret:
                    ret[attribute.object_type] = {}
                ret[attribute.object_type][attribute.name] = attribute
            return ret

        @ttl_cache(ttl=3600)
        def __read_cardinality_from_datasource(self, object_type):
            stats = self.host.get_stats(
                object_type,
                stats=['cardinality'],
                stats_fields=self.host.attribute_types[object_type].keys())
            ret = {}
            for attribute in self.host.attribute_types[object_type].keys():
                ret[attribute] = stats['stats'][attribute]['cardinality']
            return ret

        def __get_attribute(
                self,
                object_type: str,
                attribute_name: str) -> str:
            attributes = self.__read_attributes_from_datasource()
            if object_type in attributes:
                if attribute_name in attributes[object_type]:
                    return attributes[object_type][attribute_name]
            return None

        def get_display_name(
                self,
                object_type: str,
                attribute_name: str) -> str:
            attribute = self.__get_attribute(object_type, attribute_name)
            if attribute is None:
                return super().get_display_name(object_type, attribute_name)
            return attribute.display_name

        def is_available_on_relationships(
                self,
                object_type: str,
                attribute_name: str) -> bool:
            attribute = self.__get_attribute(object_type, attribute_name)
            if attribute is None:
                return False  # available attributes must be in DataSource
            return attribute.available_on_relationships

        def is_authoritative(
                self,
                object_type: str,
                attribute_name: str) -> bool:
            attribute = self.__get_attribute(object_type, attribute_name)
            if attribute is None:
                return False  # authoritative attributes must be in DataSource
            return attribute.is_authoritative

        def get_cardinality(
                self,
                object_type: str,
                attribute_name: str) -> Optional[int]:
            cardinality = self.__read_cardinality_from_datasource(object_type)
            if attribute_name in cardinality:
                return cardinality[attribute_name]
            return super().get_cardinality(object_type, attribute_name)

        def get_description(
                self,
                object_type: str,
                attribute_name: str) -> Optional[str]:
            attribute = self.__get_attribute(object_type, attribute_name)
            if attribute is None:
                return super().get_description(
                    object_type, attribute_name)
            return attribute.description

        def get_source(
                self,
                object_type: str,
                attribute_name: str) -> str:
            attribute = self.__get_attribute(object_type, attribute_name)
            if attribute is None:
                return super().get_source(object_type, attribute_name)
            return attribute.source

    return DataSourceAttributeMetadata
