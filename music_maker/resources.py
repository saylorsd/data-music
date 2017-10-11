from enum import Enum


class DataSet(Enum):
    arrests = {
        'id': 'e03a89dd-134a-4ee8-a2bd-62c40aeebc6f',
        'date_field': 'ARRESTTIME',
        'target_field': 'CCR',
        'frequency': 'week',
        'note_length': 120,
        'method': 'count',
        'region_fields' : {
            'neighborhood': 'INCIDENTNEIGHBORHOOD'
        }
    }
    fires = {
        'id': '8d76ac6b-5ae8-4428-82a4-043130d17b02',
        'date_field': 'alarm_time',
        'target_field': 'type_description',
        'frequency': 'week',
        'note_length': 120,
        'method': 'count',
        'region_fields': {
            'neighborhood': 'neighborhood'
        }
    }
    three_one_one = {
        'id': '40776043-ad00-40f5-9dc8-1fde865ff571',
        'date_field': 'CREATED_ON',
        'target_field': 'REQUEST_TYPE',
        'target_condition': " LIKE 'Potholes%' ",
        'frequency': 'day',
        'note_length': 60,
        'method': 'count',
        'region_fields': {
            'neighborhood': 'NEIGHBORHOOD'
        }
    }
