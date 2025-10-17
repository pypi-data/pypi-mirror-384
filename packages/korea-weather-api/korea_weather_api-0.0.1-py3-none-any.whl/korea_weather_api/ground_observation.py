import datetime
from typing import Any
import requests
from fastapi import HTTPException


def get_synoptic_data(
    dt: datetime.datetime,
    station_id: str,
    auth_key: str,
) -> dict[str, Any]:
    response = requests.get(
        "https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd.php",
        params={
            "tm": dt.strftime("%Y%m%d"),
            "stn": station_id,
            "disp": "0",
            "help": "0",
            "authKey": auth_key,
        },
    )

    if response.status_code == 403:
        raise HTTPException(
            status_code=403,
            detail="활용신청이 필요한 API 입니다. 활용신청 후 다시 시도해 주십시오.",
        )

    data = response.text.splitlines()

    if len(data) < 7:
        raise HTTPException(
            status_code=404,
            detail="입력한 관측일 혹은 관측 지점에 데이터가 없습니다.",
        )

    data = data[-2]

    record = {
        "dt": datetime.datetime(
            int(data[:4]),
            int(data[4:6]),
            int(data[6:8]),
        ),
        "station_id": data[8:12],
        "wind_speed_average": float(data[12:17]),
        "wind_run": int(data[17:23]),
        "wind_direction_max": data[23:27],
        "wind_speed_max": float(data[27:32]),
        "wind_speed_max_dt": data[33:37],
        "wind_direction_instantaneous": data[37:41],
        "wind_speed_instantaneous": float(data[41:46]),
        "wind_speed_instantaneous_dt": data[47:51],
        "temperature_average": float(data[51:57]),
        "temperature_max": float(data[57:63]),
        "temperature_max_dt": data[64:68],
        "temperature_min": float(data[68:74]),
        "temperature_min_dt": data[75:79],
        "temperature_dew_point": float(data[79:85]),
        "temperature_ground": float(data[85:91]),
        "temperature_grass": float(data[91:97]),
        "humidity_average": float(data[97:103]),
        "humidity_min": float(data[103:109]),
        "humidity_min_dt": data[110:114],
        "water_vapor_pressure": float(data[114:120]),
        "evaporation_small": float(data[120:126]),
        "evaporation_large": float(data[126:132]),
        "fog_duration": float(data[132:138]),
        "atmospheric_pressure": float(data[138:145]),
        "atmospheric_pressure_sea_level": float(data[145:152]),
        "atmospheric_pressure_sea_level_max": float(data[152:159]),
        "atmospheric_pressure_sea_level_max_dt": data[160:164],
        "atmospheric_pressure_sea_level_min": float(data[164:171]),
        "atmospheric_pressure_sea_level_min_dt": data[172:176],
        "cloud_amount": float(data[176:181]),
        "sunshine": float(data[181:186]),
        "sunshine_duration": float(data[186:191]),
        "sunshine_campbell": float(data[191:196]),
        "solar_insolation": float(data[196:202]),
        "solar_insolation_60m_max": float(data[202:208]),
        "solar_insolation_60m_max_dt": data[209:213],
        "rainfall": float(data[213:220]),
        "rainfall_99": float(data[220:227]),
        "rainfall_duration": float(data[227:233]),
        "rainfall_60m_max": float(data[233:240]),
        "rainfall_60m_max_dt": data[241:245],
        "rainfall_10m_max": float(data[245:252]),
        "rainfall_10m_max_dt": data[253:257],
        "rainfall_intensity_max": float(data[257:264]),
        "rainfall_intensity_max_dt": data[265:269],
        "snow_depth_new": float(data[269:276]),
        "snow_depth_new_dt": data[277:281],
        "snow_depth_max": float(data[281:288]),
        "snow_depth_max_dt": data[289:293],
        "temperature_earth_05": float(data[293:299]),
        "temperature_earth_10": float(data[299:305]),
        "temperature_earth_15": float(data[305:311]),
        "temperature_earth_30": float(data[311:317]),
        "temperature_earth_50": float(data[317:]),
    }

    for key, value in record.items():
        if key.endswith("_dt"):
            if "-" in value:
                record[key] = None

            else:
                value = value.replace(" ", "0")

                record[key] = datetime.datetime(
                    record["dt"].year,
                    record["dt"].month,
                    record["dt"].day,
                    int(value[:2]),
                    int(value[2:]),
                )

        elif isinstance(value, int):
            if value == -9:
                record[key] = 0

        elif isinstance(value, float):
            if value == -9.0:
                record[key] = 0.0

        elif isinstance(value, str):
            record[key] = value.strip()

    return record
