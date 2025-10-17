import csv
import re
import html
from lxml import etree
from urllib.parse import unquote

from imerit_ango.models.question_types import QUESTION_TYPES

class AssetBuilderUploader:
    def __init__(self):
        # Constants
        self.SUPPORTED_TAGS = {
            'video': 'video',
            'img': 'img',
            'audio': 'audio',
            'iframe': 'iframe',
            'a': 'a',
            'p': 'p',
        }
        self.SUPPORTED_MEDIA_TAGS = [
            self.SUPPORTED_TAGS['img'],
            self.SUPPORTED_TAGS['audio'],
            self.SUPPORTED_TAGS['video'],
        ]
        self.DENIED_TAGS = ['script']
        self.DEFAULT_STORAGE_OPTION = 'Public'


    def __prepare_asset_context_data(self, row, columns, data_config):
        context_data = {}
        for col in columns:
            if data_config.get(col, {}).get("includeInExport", False):
                context_data[col] = row[col]
        return context_data

    def __prepare_asset_html(self, placeholder_html, row, data_config, classifications):
        if classifications is None:
            classifications = []
        
        # Parse the HTML string
        unescaped_html = html.unescape(placeholder_html)
        parser = etree.HTMLParser()
        dom = etree.fromstring(unescaped_html, parser)
        
        # Replace placeholders
        self.__replace_placeholders(dom, data_config, classifications, row)
        
        # Get the body content
        body = dom.find('body')
        if body is not None:
            final_html = etree.tostring(body, encoding='unicode')
            # Remove body tags
            final_html = re.sub(r'</?body>', '', final_html).strip()
        else:
            final_html = etree.tostring(dom, encoding='unicode')
        
        return final_html

    def __is_multi_selection_classification(self, cla):
        multi_selection_types = [
            QUESTION_TYPES.CHECKBOX.value,
            QUESTION_TYPES.MULTIPLE_DROPDOWN.value,
            QUESTION_TYPES.RANK.value
        ]
        return cla.get('tool') in multi_selection_types
    
    def __wrap_with_double_curly(self, text):
        return f"{{{{{text}}}}}"

    def __get_column_from_resource_name(self, columns, resource_name):
        for column in columns:
            if self.__wrap_with_double_curly(column) == resource_name:
                return column
        return None

    def __check_column(self, columns, resource_name):
        if not resource_name:
            return {'column': None, 'is_column': False}
        column = self.__get_column_from_resource_name(columns, resource_name)
        return {'column': column, 'is_column': bool(column)}

    def __decode_uri_and_extract_resource_name(self, uri):
        decoded_uri = unquote(uri)
        return decoded_uri.split('/')[-1]

    def __replace_text_node(self, node, data_settings, current_data):
        trimmed_value = node.text.strip() if node.text else None
        if not trimmed_value:
            return
        result = self.__check_column(data_settings.keys(), trimmed_value)
        if result['is_column']:
            node.text = f"\n\n{current_data[result['column']]}\n\n"

    def __replace_media_node(self, node, data_settings, current_data):
        resource_name = self.__decode_uri_and_extract_resource_name(node.get('src', ''))
        column = self.__get_column_from_resource_name(data_settings.keys(), resource_name)
        if column:
            new_src = current_data[column]
            storage_info = data_settings[column].get('storage') if column in data_settings else None
            if storage_info and storage_info != self.DEFAULT_STORAGE_OPTION:
                new_src += f"?storageId={storage_info}"
            node.set('src', new_src)

    def __replace_anchor_node(self, node, data_settings, current_data):
        resource_name = self.__decode_uri_and_extract_resource_name(node.get('href', ''))
        column = self.__get_column_from_resource_name(data_settings.keys(), resource_name)
        if column:
            node.set('href', current_data[column])

    def __replace_iframe_node(self, node, data_settings, current_data):
        resource_name = self.__decode_uri_and_extract_resource_name(node.get('src', ''))
        column = self.__get_column_from_resource_name(data_settings.keys(), resource_name)
        if column:
            node.set('src', current_data[column])
            node.attrib.pop('sandbox', None)
            node.attrib.pop('srcdoc', None)

    def __replace_inner_html(self, node, data_settings, current_data):
        inner_html = html.unescape(node.text or '')
        result = self.__check_column(data_settings.keys(), inner_html)
        if result['is_column']:
            node_text = current_data[result['column']]
            node.text = f"\n\n{node_text}\n\n"

    def __is_classification(self, text, classifications):
        return next((c for c in classifications if self.__wrap_with_double_curly(c['title']) == text.strip()), None)

    def __generate_classification_id(self, schema_id):
        return f"cla-portal-{schema_id}"

    def __replace_placeholders(self, root, data_settings, classifications, current_data):
        if root is None:
            return

        for node in root:
            cla = self.__is_classification(html.unescape(node.text or ''), classifications)
            if cla:
                node.set('id', self.__generate_classification_id(cla['schemaId']))
                node.text = ''
            elif isinstance(node, etree._Comment):
                continue
            elif isinstance(node, etree._ProcessingInstruction):
                continue
            else:
                current_tag_name = node.tag.lower()
                if current_tag_name in self.DENIED_TAGS:
                    node.getparent().remove(node)
                elif current_tag_name in self.SUPPORTED_MEDIA_TAGS:
                    self.__replace_media_node(node, data_settings, current_data)
                elif current_tag_name == self.SUPPORTED_TAGS['a']:
                    self.__replace_anchor_node(node, data_settings, current_data)
                elif current_tag_name == self.SUPPORTED_TAGS['iframe']:
                    self.__replace_iframe_node(node, data_settings, current_data)
                else:
                    self.__replace_inner_html(node, data_settings, current_data)

                # Recursively call replace_placeholders for child nodes
                self.__replace_placeholders(node, data_settings, classifications, current_data)

            # Handle text nodes
            if node.text:
                self.__replace_text_node(node, data_settings, current_data)

    def __is_multiple_instances_necessary(self, cla):
        return cla.get('multiple', False) and not self.__is_multi_selection_classification(cla)

    def __prepare_asset_pre_labels(self, row_data, selected_pre_label_columns):
        pre_label_column_entries = selected_pre_label_columns.items()
        
        result = []
        for _, pre_label_instance in pre_label_column_entries:
            if self.__is_multiple_instances_necessary(pre_label_instance.get('cla')):
                data_points = row_data.get(pre_label_instance.get('value', ''), '').split(';')
                multiple_enabled_pre_labels = [
                    {
                        'title': pre_label_instance['cla']['title'],
                        'schemaId': pre_label_instance['cla']['schemaId'],
                        'answer': d
                    }
                    for d in data_points
                ]
                result.extend(multiple_enabled_pre_labels)
            else:
                pre_label = row_data.get(pre_label_instance.get('value', ''), '')

                if self.__is_multi_selection_classification(pre_label_instance.get('cla')):
                    pre_label = row_data.get(pre_label_instance.get('value', ''), '').split(';')

                result.append({
                    'title': pre_label_instance['cla']['title'],
                    'schemaId': pre_label_instance['cla']['schemaId'],
                    'answer': pre_label
                })
        
        return result

    def __prepare_asset_external_id(self, row, selected_external_id_column):
        return row[selected_external_id_column]

    def __prepare_asset_batches(self, row, batch_column):
        if not batch_column:
            return []
        
        batch_names = row[batch_column]
        if not batch_names:
            return []
        batch_name_list = batch_names.split(";")
        return batch_name_list
    
    def read_file(self, file_path, parse_config={}):
        with open(file_path, 'r') as f:
            custom_delimiter = parse_config.get("delimiter", ",")
            csv_dict_reader = csv.DictReader(f, delimiter=custom_delimiter)
            
            self.columns = csv_dict_reader.fieldnames
            self.rows = list(csv_dict_reader)

    def prepare_assets(self, template, classifications):
        columns = self.columns
        rows = self.rows
        accummulated_batches = set() 

        if not columns or not rows:
            raise Exception("Cannot prepare assets before reading the input file")

        placeholder_html = template.get("template", "")
        data_config = template.get("dataConfig", {})
        pre_label_config = template.get("preLabelConfig", {})
        external_id_column = template.get("selectedExternalId", "")
        batch_column_name = template.get("batch_column_name", "")
        assets = []

        if not placeholder_html:
            raise Exception("Placeholder HTML is empty. Can't continue the upload process.")

        for row in rows:
            context_data = self.__prepare_asset_context_data(row, columns, data_config)
            asset_html = self.__prepare_asset_html(placeholder_html, row, data_config, classifications)
            pre_labels = self.__prepare_asset_pre_labels(row, pre_label_config)
            external_id = self.__prepare_asset_external_id(row, external_id_column)
            asset_batches = self.__prepare_asset_batches(row, batch_column_name)

            for batch_name in asset_batches:
                accummulated_batches.add(batch_name)

            assets.append({
                "data": asset_html,
                "externalId": external_id,
                "contextData": context_data,
                "classifications": pre_labels,
                "batch_names": asset_batches
            })

        self.assets = assets
        return assets, accummulated_batches
    
    def replace_batch_names_with_batch_ids(self, batch_list):
        batch_id_map = {batch['name']: batch['_id'] for batch in batch_list}

        asset_objs = self.assets
        for asset in asset_objs:
            asset['batches'] = [batch_id_map.get(batch_name) for batch_name in asset['batch_names']]
            del asset['batch_names']
        return asset_objs
