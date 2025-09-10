## registered_reports

```python
{
    'ven_id_123': [
        {
            'duration': datetime.timedelta(seconds=3600),
            'report_descriptions': [
                {
                    'r_id': '1e8bee9e-8125-47af-bf8c-dc998d765f53',
                    'report_data_source': {'resource_id': 'device001'},
                    'report_type': 'reading',
                    'reading_type': 'Direct Read',
                    'sampling_rate': {
                        'min_period': datetime.timedelta(seconds=10),
                        'max_period': datetime.timedelta(seconds=10),
                        'on_change': False
                    },
                    'measurement': {
                        'name': 'voltage',
                        'description': 'Voltage',
                        'unit': 'V',
                        'scale': 'none'
                    }
                }
            ],
            'report_request_id': 0,
            'report_specifier_id': '12c940b2-984f-47fe-ae21-fe4e353a712c',
            'report_name': 'TELEMETRY_USAGE',
            'created_date_time': datetime.datetime(2025, 9, 10, 13, 34, 21, 185375, tzinfo=datetime.timezone.utc)
        }
    ]
}
```

## report_requests

```python
[
    ReportRequest(
        report_request_id='2bd3abb1-7d51-41c5-a032-c5ee3757a280',
        report_specifier=ReportSpecifier(
            report_specifier_id='12c940b2-984f-47fe-ae21-fe4e353a712c',
            granularity=datetime.timedelta(seconds=10),
            specifier_payloads=[
                SpecifierPayload(
                    r_id='1e8bee9e-8125-47af-bf8c-dc998d765f53',
                    reading_type='Direct Read', measurement=None
                )
            ],
            report_interval=None,
            report_back_duration=datetime.timedelta(seconds=10)
        )
    )
]
```

## response_payload

```python
{
    'report_requests': [
        ReportRequest(
            report_request_id='0ab2039b-2b74-4169-9692-84bb50c44db0',
            report_specifier=ReportSpecifier(
                report_specifier_id='5ae30d6b-4ed4-430c-9953-505ed0f67885',
                granularity=datetime.timedelta(seconds=10),
                specifier_payloads=[
                    SpecifierPayload(
                        r_id='0be87e24-6234-4ee8-87db-db45b689ede5',
                        reading_type='Direct Read',
                        measurement=None
                    )
                ],
                report_interval=None,
                report_back_duration=datetime.timedelta(seconds=10)
            )
        )
    ]
}
```

## on_register_report

```python
{
    'duration': datetime.timedelta(seconds=3600),
    'report_descriptions': [
        {
            'r_id': '5402691b-f618-4bab-be0a-06a828f0e589',
            'report_data_source': {'resource_id': 'device001'},
            'report_type': 'reading',
            'reading_type': 'Direct Read',
            'sampling_rate': {
                'min_period': datetime.timedelta(seconds=10),
                'max_period': datetime.timedelta(seconds=10),
                'on_change': False
            },
            'measurement': {
                'name': 'voltage',
                'description': 'Voltage',
                'unit': 'V',
                'scale': 'none'
            }
        }
    ],
    'report_request_id': 0,
    'report_specifier_id': '28f5fc42-d367-478a-b023-3cb304ff4b0b',
    'report_name': 'METADATA_TELEMETRY_USAGE',
    'created_date_time': datetime.datetime(2025, 9, 10, 15, 1, 45, 380864, tzinfo=datetime.timezone.utc)
}
```
