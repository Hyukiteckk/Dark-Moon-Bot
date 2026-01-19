class PointsService:

    POINT_INTERVAL_SECONDS = 15 * 60  # 15 minutos

    @staticmethod
    def seconds_to_points(seconds: int) -> int:
        if not seconds or seconds < PointsService.POINT_INTERVAL_SECONDS:
            return 0

        return seconds // PointsService.POINT_INTERVAL_SECONDS

