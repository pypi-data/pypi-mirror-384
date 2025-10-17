# Dapla Suv Tools
A collection of tools for integrating with the SUV-platform

### Install `dapla-suv-tools` from PyPI

```python
pip install dapla-suv-tools
```

### Initialize a client using `SuvClient`

```python
from dapla_suv_tools.suv_client import SuvClient

client = SuvClient()
```

### Setup pagination using `PaginationInfo`

```python
from dapla_suv_tools.pagination import PaginationInfo

p_info = PaginationInfo(page=1, size=5)
```

### Example 1: fetch skjema by id 

```python
from dapla_suv_tools.suv_client import SuvClient

client = SuvClient()

x = client.get_skjema_by_id(skjema_id=116)

print(x)
```

### Example 2: fetch skjema's with PaginationInfo

```python
from dapla_suv_tools.suv_client import SuvClient
from dapla_suv_tools.pagination import PaginationInfo

client = SuvClient()
p_info = PaginationInfo(page=1, size=5)

y = client.get_skjema_by_ra_nummer(
    ra_nummer="RA-5566", max_results=0, latest_only=False, pagination_info=p_info
)

print(y)
```

### Function `get_skjema_by_id`

```python
output = client.get_skjema_by_id(skjema_id=1, max_results=0, latest_only=False)
print(output)
```

**Parameters:**


- `skjema:id` (int, reguired): Skjema's RA-number.
- `max_results` (Optional[int]): Maximum number of results int the result set.  A value of 0 will get ALL results. Default is 0.
- `latest_only` (Optional[bool]): A boolean flag to trigger a special condition. Default is 'False'.
- `pagination_info` (Optional[PaginationInfo]): An object holding pagination metadata. Default is 'None'.

**Returns:**  
- `dict`: A json object matching the id


### Function `get_skjema_by_ra_nummer`

```python
output = client.get_skjema_by_ra_nummer(ra_nummer="RA-5566", max_results=0, versjon=1, latest_only=False)
print(output)
```

**Parameters:**


- `ra_number` (str): Skjema's RA-number.
- `versjon` (Optional[int]): Limit result to selected version. 
- `max_results` (Optional[int]): Maximum number of results int the result set.  A value of 0 will get ALL results. Default is 0.
- `latest_only` (Optional[bool]): A boolean flag to trigger a special condition. Default is 'False'.
- `pagination_info` (Optional[PaginationInfo]): An object holding pagination metadata. Default is 'None'.

**Returns:**  
- `dict`: A list of skjema json objects matching the RA-number


### Function `get_all_skjema`

```python
output = client.get_all_skjema()
print(output)
```

**Parameters:**

None

**Returns:**
- `OperationResult`: A list of skjema json objects for all skjema's


### Function `update_skjema_by_id`

```python
output = client.update_skjema_by_id(skjema_id=1, beskrivelse="Test")
print(output)
```
**Parameters:**

- `skjema_id` (int), required: The id of the skjema to update.
- `datamodell` (Optional[str]): The data model of the skjema.
- `beskrivelse` (Optional[str]): The description of the skjema.
- `navn_nb` (Optional[str]): The name of the skjema in Norwegian Bokmål.
- `navn_nn` (Optional[str]): The name of the skjema in Norwegian Nynorsk.
- `navn_en` (Optional[str]): The name of the skjema in English.
- `infoside` (Optional[str]): URL for the information page of the skjema.
- `eier` (Optional[str]): The owner of the skjema.
- `kun_sky` (Optional[bool]): Whether the skjema is only in the cloud.
- `gyldig_fra` (Optional[date]): The valid from date of the skjema.
- `gyldig_til` (Optional[date]): The valid to date of the skjema.
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: An object containing the updated skjema or an error message if the retrieval fails.



### Function `update_skjema_by_ra_number`

```python
output = client.update_skjema_by_ra_number(ra_number='RA-1234', versjon=1, undersokelse_nr="0001", beskrivelse="Test")
print(output)
```
**Parameters:**

- `ra_nummer` (str), required: Skjema's RA-number, e.g. 'RA-1234'.
- `versjon` (int), required: The version of the skjema.
- `undersokelse_nr` (str), required: The investigation number of the skjema.
- `datamodell` (Optional[str]): The data model of the skjema.
- `beskrivelse` (Optional[str]): The description of the skjema.
- `navn_nb` (Optional[str]): The name of the skjema in Norwegian Bokmål.
- `navn_nn` (Optional[str]): The name of the skjema in Norwegian Nynorsk.
- `navn_en` (Optional[str]): The name of the skjema in English.
- `infoside` (Optional[str]): URL for the information page of the skjema.
- `eier` (Optional[str]): The owner of the skjema.
- `kun_sky` (Optional[bool]): Whether the skjema is only in the cloud.
- `gyldig_fra` (Optional[date]): The valid from date of the skjema.
- `gyldig_til` (Optional[date]): The valid to date of the skjema.
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: An object containing the updated skjema or an error message if the retrieval fails.




### Function `get_periode_by_id`

```python
output = client.get_periode_by_id(periode_id=123)
print(output)
```

**Parameters:**

- `periode_id` (int): The ID of the period to retrieve.
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: An object containing the period information if found, or an error message if the retrieval fails.





### Function `get_perioder_by_skjema_id`

```python
output = client.get_perioder_by_skjema_id(skjema_id=123,periode_type="KVRT", periode_aar=2023)
print(output)
```

**Parameters:**

- `skjema_id` (int): The skjema_id of the period to retrieve.
- `periode_type` (Optional[str]): The type of the period to filter by. If None, periods of any type will be retrieved.
- `periode_nr` (Optional[int]): The number of the period to filter by. If None, periods of any number will be retrieved.
- `periode_aar` (Optional[int]): The year of the period to filter by. If None, periods of any year will be retrieved.
- `delreg_nr` (Optional[int]): The delreg_nr of the period to filter by. If None, periods of any delreg_nr will be retrieved.
- `enhet_type` (Optional[int]): The enhet_type of the period to filter by. If None, periods of any enhet_type will be retrieved.
- `max_results` (int): Maximum number of results in the result set. A value of 0 will get ALL results. Defaults to 0
- `latest_only` (bool): A boolean flag to trigger a special condition. A True value will retrieve the latest periode added. Defaults to False.
- `pagination_info` (Optional[int]): An object holding pagination metadata. Defaults to None. 
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: An object containing the period information if found, or an error message if the retrieval fails.




### Function `update_periode_by_id`

```python
output = client.update_periode_by_id(
        periode_id=456, vis_oppgavebyrde=True
    )
print(output)
```

**Parameters:**

- `periode_id` (int): The ID of the period to update.
- `periode_dato` (Optional[date]): Date for the period. If None, the existing date will be used.
- `delreg_nr` (Optional[int]): delreg_nr. If None, the existing number will be used.
- `enhet_type` (Optional[str]): enhet_type. If None, the existing type will be used.
- `vis_oppgavebyrde` (Optional[bool]): A boolean flag to indicate visibility of "oppgavebyrde". Defaults to None.
- `vis_brukeropplevelse` (Optional[bool]): A boolean flag to indicate visibility of "brukeropplevelse". Defaults to None.
- `har_skjemadata` (Optional[bool]): A boolean flag to indicate the presence of schema data. Defaults to None.
- `journalnummer` (Optional[str]): Journal number. If None, the existing number will be used.
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: An object containing the updated period information, or an error message if the update fails.



### Function `update_periode_by_skjema_id`

```python
output = client.update_periode_by_skjema_id(skjema_id=456, periode_type="KVRT", periode_aar=2023, periode_nr=1, delreg_nr=3)
print(output)
```

**Parameters:**

- `skjema_id` (int): The skjema_id of the period to update.
- `periode_type` (str): Periode type of the period to update.
- `periode_aar` (int): Year of the period to update.
- `periode_nr` (int): Periode number of the period to update.
- `periode_dato` (Optional[date]): Date for the period. If None, the existing date will be used.
- `delreg_nr` (Optional[int]): The delreg_nr of the period to filter by. If None, periods of any delreg_nr will be retrieved.
- `enhet_type` (Optional[int]): The enhet_type of the period to filter by. If None, periods of any enhet_type will be retrieved.
- `vis_oppgavebyrde` (Optional[bool]): A boolean flag to indicate visibility of "oppgavebyrde". Defaults to None.
- `vis_brukeropplevelse` (Optional[bool]): A boolean flag to indicate visibility of "brukeropplevelse". Defaults to None.
- `har_skjemadata` (Optional[bool]): A boolean flag to indicate the presence of schema data. Defaults to None.
- `journalnummer` (Optional[str]): Journal number. If None, the existing number will be used.
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: An object containing the updated period information, or an error message if the update fails.


### Function `create_periode`

```python
output = client.create_periode(
        skjema_id=456, periode_type="KVRT", periode_aar=2023, periode_nr=1
    )
print(output)
```

**Parameters:**

- `skjema_id` (int): The skjema_id associated with the new period.
- `periode_type` (Optional[str]): Periode type of the new periode.
- `periode_aar` (Optional[int]): Year of the new periode.
- `periode_nr` (Optional[int]): Periode number of the new periode.
- `periode_dato` (Optional[date]): Date for the period.
- `delreg_nr` (Optional[int]): delreg_nr
- `enhet_type` (Optional[int]): enhet_type
- `vis_oppgavebyrde` (Optional[bool]): A boolean flag to indicate visibility of "oppgavebyrde". Defaults to None.
- `vis_brukeropplevelse` (Optional[bool]): A boolean flag to indicate visibility of "brukeropplevelse". Defaults to None.
- `har_skjemadata` (Optional[bool]): A boolean flag to indicate the presence of schema data. Defaults to None.
- `journalnummer` (Optional[str]): Journal number. If None, the existing number will be used.
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`:         An object containing the ID of the created period, or an error message if the creation fails.





### Function `delete_periode`

```python
output = client.delete_periode(periode_id=123)
print(output)
```

**Parameters:**

- `periode_id` (int): The ID of the period to delete.
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: An object containing the result of the deletion operation, or an error message if the deletion fails.

=======
- `ra_number` (str, required): Skjema's RA-number.
- `max_results` (int, optional): Maximum number of results in the result set.  A value of `0` will get ALL results. Defaults to `0`.
- `latest_only` (bool, optional): A boolean flag to trigger a special condition. Defaults to `False`.
- `pagination_info` (PaginationInfo, optional): An object holding pagination metadata. Defaults to `None`.

**Returns:**  
- `dict`: A list of skjema json objects matching the RA-number




### Function `get_pulje_by_id`

```python
output = client.get_pulje_by_id(pulje_id=123)
print(output)
```

**Parameters:**

- `pulje_id` (int): The ID of the pulje to retrieve.
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: An object containing the pulje information if found, or an error message if the retrieval fails.



### Function `get_pulje_by_periode_id`

```python
output = client.get_pulje_by_periode_id(periode_id=123)
print(output)
```

**Parameters:**

- `periode_id` (int): The periode_id of the pulje to retrieve.
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: A list of objects containing the pulje information for every pulje under the given pulje_id if found, or an error message if the retrieval fails.



### Function `update_pulje_by_id`

```python
output = client.update_pulje_by_id(pulje_id=123,altinn_tilgjengelig=datetime(2023,12,12))
print(output)
```

**Parameters:**

- `pulje_id` (int): The pulje_id of the pulje to update.
- `altinn_tilgjengelig` (Optional[datetime]): Date and time for altinn_tilgjengelig.
- `altinn_svarfrist` (Optional[date]): Date for altinn_svarfrist.
- `tvangsmulkt_svarfrist` (Optional[date]): Date for tvangsmulkt_svarfrist.
- `send_si` (Optional[date]): Date for send_si. 
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: An object containing the updated pulje information, or an error message if the update fails.



### Function `update_pulje_by_periode_id`

```python
output = client.update_pulje_by_periode_id(periode_id=123, pulje_nr=1, altinn_tilgjengelig=datetime(2023,12,12))
print(output)
```

**Parameters:**

- `periode_id` (int): The periode_id of the pulje to update.
- `pulje_nr` (int): The pulje_nr of the pulje to update.
- `altinn_tilgjengelig` (Optional[datetime]): Date and time for altinn_tilgjengelig.
- `altinn_svarfrist` (Optional[date]): Date for altinn_svarfrist.
- `tvangsmulkt_svarfrist` (Optional[date]): Date for tvangsmulkt_svarfrist.
- `send_si` (Optional[date]): Date for send_si. 
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: An object containing the updated pulje information, or an error message if the update fails.



### Function `create_pulje`

```python
output = client.create_pulje(periode_id=123)
print(output)
```

**Parameters:**

- `periode_id` (int): The periode_id of the pulje to create.
- `pulje_nr` (Optional[int]): The pulje_nr of the pulje to create.
- `altinn_tilgjengelig` (Optional[datetime]): Date and time for altinn_tilgjengelig.
- `altinn_svarfrist` (Optional[date]): Date for altinn_svarfrist.
- `tvangsmulkt_svarfrist` (Optional[date]): Date for tvangsmulkt_svarfrist.
- `send_si` (Optional[date]): Date for send_si. 
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: An object containing the ID of the new pulje,  or an error message if the creation fails.


### Function `delete_pulje`

```python
output = client.delete_pulje(pulje_id=123)
print(output)
```

**Parameters:**

- `pulje_id` (int): The pulje_id of the pulje to delete.
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: An object containing the ID of the deleted pulje, or an error message of the deletion fails. 


### Function `get_prefill_meta_by_skjema_id`

```python
output = client.get_prefill_meta_by_skjema_id(skjema_id=123)
print(output)
```

**Parameters:**

- `skjema_id` (int): The ID of the skjema.
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: A list of objects containing meta data for skjema's matching the supplied id, or an error message if the retrieval fails.


### Function `get_utvalg_from_sfu`

```python
output = client.get_utvalg_from_sfu(delreg_nr="123456789", ra_nummer="123456789", pulje="123456789")
print(output)
```

**Parameters:**

- `delreg_nr` (int): The delreg number of the selection.
- `ra_nummer` (str): Skjema's RA-number, e.g. 'RA-1234'.
- `pulje` Optional(str): Limit the selection by pulje.
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: A list of objects with the selection, or an error message of the deletion fails. 


### Function `get_enhet_from_sfu`

```python
output = client.get_enhet_from_sfu(delreg_nr="123456789", orgnr="123456789")
print(output)
```

**Parameters:**

- `delreg_nr` (int): The delreg number of the selection.
- `orgnr` (str): The organization number of the unit.
- `context` (SuvOperationContext): Operation context for logging and error handling. This is injected by the underlying pipeline.  Adding a custom context will result in an error

**Returns:**  
- `OperationResult`: An object with the organization, or an error message of the deletion fails. 
