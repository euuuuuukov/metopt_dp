"""
Класс Asset представляет один актив (ценную бумагу или депозит).
Содержит информацию о текущей сумме, шаге управления,
минимальном ограничении и комиссии.
"""


class Asset:
    def __init__(self, name: str, current_amount: float, step: float,
                 min_amount: float, commission: float):
        """
        Args:
            name: Название актива
            current_amount: Текущая сумма
            step: Шаг управления (размер пакета)
            min_amount: Минимальное допустимое значение
            commission: Комиссия брокера (в долях)
        """
        self.name = name
        self.current_amount = current_amount
        self.step = step
        self.min_amount = min_amount
        self.commission = commission

    def calculate_commission(self, change: float) -> float:
        """Рассчитывает комиссию для заданного изменения"""
        return abs(change) * self.commission if change != 0 else 0

    def is_change_valid(self, change: float) -> bool:
        """
        Проверяет, что изменение допустимо:
        1. Кратно шагу
        2. Не приводит к значению ниже минимума
        """
        # Проверка кратности шагу (с учетом погрешности)
        if abs(change % self.step) > 1e-10 and abs(change % self.step - self.step) > 1e-10:
            return False

        # Проверка минимального ограничения
        new_amount = self.current_amount + change
        return new_amount >= self.min_amount - 1e-10

    def __repr__(self) -> str:
        return (f"{self.name}: {self.current_amount:.2f} "
                f"(шаг: {self.step:.2f}, мин: {self.min_amount:.2f}, "
                f"комиссия: {self.commission * 100:.1f}%)")