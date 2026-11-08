import json
import boto3
import time
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('pumproom_data_test')
table2 = dynamodb.Table('pumproom_latest_test')

def to_decimal(v):
    if v is None:
        return None
    try:
        return Decimal(str(v))
    except:
        return None

def lambda_handler(event, context):

    # IoT Core payload kommt direkt im event
    print("Incoming event:", json.dumps(event))

    # Falls AWS IoT Wrapper-Struktur vorhanden ist
    # (manche Setups packen Payload in "payload")
    data = event.get("payload", event)

    # Device ID fallback
    device_id = data.get("device_id", "unknown_device22")

    # Timestamp fallback (wenn SPS keinen sendet)
    timestamp = data.get("timestamp", int(time.time()))

    # Item bauen (flach + robust)
    item = {
        "device_id": device_id,
        "timestamp": timestamp,
        "last_pump_running_timestamp": data.get("last_pump_running_timestamp"),
        "uptime": data.get("uptime"),

        "temp_primary_supply": to_decimal(data.get("temp_primary_supply")),
        "temp_primary_return": to_decimal(data.get("temp_primary_return")),
        "temp_secondary_supply": to_decimal(data.get("temp_secondary_supply")),
        "temp_secondary_return": to_decimal(data.get("temp_secondary_return")),
        "temp_heat_exchanger": to_decimal(data.get("temp_heat_exchanger")),
        "temp_heat_exchanger_warning": data.get("temp_heat_exchanger_warning"),
        "temp_heat_exchanger_error": data.get("temp_heat_exchanger_error"),
        "temp_room": to_decimal(data.get("temp_room")),

        "pressure_secondary": to_decimal(data.get("pressure_secondary")),
        "pressure_secondary_warning": to_decimal(data.get("pressure_secondary_warning")),
        "pressure_secondary_error": to_decimal(data.get("pressure_secondary_error")),
        "flow_secondary_lps": to_decimal(data.get("flow_secondary_lps")),

        "well_level_cm": to_decimal(data.get("well_level_cm")),

        "pump_setpoint_percent": to_decimal(data.get("pump_setpoint_percent")),
        "alarm_lamp_state": to_decimal(data.get("alarm_lamp_state")),
    }

    # None-Werte entfernen (wichtig für DynamoDB!)
    item = {k: v for k, v in item.items() if v is not None}

    # In DynamoDB schreiben
    table.put_item(Item=item) #historie







    # device_id und timestamp immer aktualisieren
    update_expr = ["#ts = :ts"]
    expr_attr_names = {
        "#ts": "timestamp"
    }
    expr_attr_values = {
        ":ts": timestamp
    }

    # alle übrigen Felder aus dem JSON übernehmen
    for key, value in data.items():

        if key in ("device_id", "timestamp"):
            continue

        if value is None:
            continue

        placeholder_name = f"#{key}"
        placeholder_value = f":{key}"

        expr_attr_names[placeholder_name] = key

        if isinstance(value, float):
            expr_attr_values[placeholder_value] = Decimal(str(value))
        else:
            expr_attr_values[placeholder_value] = value

        update_expr.append(f"{placeholder_name} = {placeholder_value}")

    table2.update_item(
        Key={
            "device_id": device_id
        },
        UpdateExpression="SET " + ", ".join(update_expr),
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values
    )















    return {
        "statusCode": 200,
        "body": "ok"
    }