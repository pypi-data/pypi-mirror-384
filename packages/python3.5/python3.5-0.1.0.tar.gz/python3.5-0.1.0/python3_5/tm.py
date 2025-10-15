import time
import datetime


class TTime:
    @staticmethod
    def check_time():
        return "Basic time check method"

    @staticmethod
    def system_time():
        current_time = time.strftime("%H:%M:%S")
        return f"sys time: {current_time}"

    @staticmethod
    def world_time_utc():
        utc_time = datetime.datetime.utcnow()
        return f"world time (UTC): {utc_time.strftime('%H:%M:%S')}"

    @staticmethod
    def full_datetime():
        current_datetime = datetime.datetime.now()
        return f"full time: {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
