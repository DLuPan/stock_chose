# 简单示例，可根据实际模式扩展
class GridGenerator:
    def __init__(self, symbol: str, current_price: float):
        self.symbol = symbol
        self.current_price = current_price

    def generate(self):
        lower_bound = self.current_price * 0.9
        upper_bound = self.current_price * 1.1
        grid_count = 20
        grid_spacing_mode = "FIXED_%"
        grid_spacing_pct = 1.5
        step = (upper_bound - lower_bound) / grid_count
        grid_levels = [round(lower_bound + i * step, 2) for i in range(grid_count + 1)]

        return {
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "grid_count": grid_count,
            "grid_spacing_mode": grid_spacing_mode,
            "grid_spacing_pct": grid_spacing_pct,
            "current_price": round(self.current_price, 2),
            "grid_levels": grid_levels,
        }
