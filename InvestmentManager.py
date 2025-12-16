"""
Класс InvestmentManager реализует метод динамического программирования
для решения задачи управления инвестиционным портфелем.
Использует рекуррентные соотношения Беллмана (обратный ход).
"""

from functools import lru_cache
from typing import Tuple, List, Dict
from problem import (
    START_ZB1, START_ZB2, START_DEP,
    START_FREE, CHANGE_ZB1, CHANGE_ZB2, CHANGE_DEP,
    MIN_ZB1, MIN_ZB2, MIN_DEP,
    COMMISSION_ZB1, COMMISSION_ZB2, COMMISSION_DEP,
    STAGES
)
from Asset import Asset


class InvestmentManager:
    """Управляет инвестиционным портфелем и ищет оптимальную стратегию."""

    def __init__(self):
        """Инициализация с данными из problem.py"""
        # Создаем активы
        self.zb1 = Asset('ЦБ1', START_ZB1, CHANGE_ZB1, MIN_ZB1, COMMISSION_ZB1)
        self.zb2 = Asset('ЦБ2', START_ZB2, CHANGE_ZB2, MIN_ZB2, COMMISSION_ZB2)
        self.dep = Asset('Депозит', START_DEP, CHANGE_DEP, MIN_DEP, COMMISSION_DEP)

        self.free_cash = START_FREE
        self.stages = STAGES

        # Для хранения оптимальной политики
        self.optimal_policy = {}

    def _calculate_total_commission(self, delta_zb1: float, delta_zb2: float,
                                    delta_dep: float) -> float:
        """Рассчитывает общую комиссию за все операции"""
        return (self.zb1.calculate_commission(delta_zb1) +
                self.zb2.calculate_commission(delta_zb2) +
                self.dep.calculate_commission(delta_dep))

    def _discretize_state(self, zb1_val: float, zb2_val: float, dep_val: float,
                          free_val: float) -> Tuple:
        """
        Дискретизация состояния для уменьшения пространства состояний.
        Округляем значения до ближайших кратных шагам.
        """
        # Определяем шаги дискретизации
        disc_step_zb1 = max(5, self.zb1.step / 2)
        disc_step_zb2 = max(20, self.zb2.step / 2)
        disc_step_dep = max(10, self.dep.step / 2)
        disc_step_free = max(10, min(self.zb1.step, self.zb2.step, self.dep.step) / 2)

        return (
            round(zb1_val / disc_step_zb1) * disc_step_zb1,
            round(zb2_val / disc_step_zb2) * disc_step_zb2,
            round(dep_val / disc_step_dep) * disc_step_dep,
            round(free_val / disc_step_free) * disc_step_free,
        )

    def _generate_controls_for_state(self, zb1_val: float, zb2_val: float,
                                     dep_val: float, free_val: float) -> List[Tuple]:
        """
        Генерирует все допустимые управления для данного состояния.

        Алгоритм:
        1. Определяем диапазоны для каждого актива в пакетах
        2. Генерируем разумные комбинации с учетом ограничений
        """
        controls = []

        # Определяем диапазоны для каждого актива в пакетах
        # Для продажи: от 0 до максимального количества (не ниже минимума)
        max_sell_zb1 = max(0, int((zb1_val - self.zb1.min_amount) // self.zb1.step))
        max_sell_zb2 = max(0, int((zb2_val - self.zb2.min_amount) // self.zb2.step))
        max_sell_dep = max(0, int((dep_val - self.dep.min_amount) // self.dep.step))

        # Ограничиваем фактическим количеством
        max_sell_zb1 = min(max_sell_zb1, int(zb1_val // self.zb1.step))
        max_sell_zb2 = min(max_sell_zb2, int(zb2_val // self.zb2.step))
        max_sell_dep = min(max_sell_dep, int(dep_val // self.dep.step))

        # Для покупки: ограничим разумными пределами
        # Рассчитываем максимальную сумму, которую можем потратить
        max_money = free_val
        if max_sell_zb1 > 0:
            max_money += max_sell_zb1 * self.zb1.step * (1 - self.zb1.commission)
        if max_sell_zb2 > 0:
            max_money += max_sell_zb2 * self.zb2.step * (1 - self.zb2.commission)
        if max_sell_dep > 0:
            max_money += max_sell_dep * self.dep.step * (1 - self.dep.commission)

        # Максимальное количество пакетов для покупки
        max_buy_zb1 = int(max_money // (self.zb1.step * (1 + self.zb1.commission)))
        max_buy_zb2 = int(max_money // (self.zb2.step * (1 + self.zb2.commission)))
        max_buy_dep = int(max_money // (self.dep.step * (1 + self.dep.commission)))

        # Ограничим для производительности
        MAX_PACKAGES = 20
        max_sell_zb1 = min(max_sell_zb1, MAX_PACKAGES)
        max_sell_zb2 = min(max_sell_zb2, MAX_PACKAGES)
        max_sell_dep = min(max_sell_dep, MAX_PACKAGES)
        max_buy_zb1 = min(max_buy_zb1, MAX_PACKAGES)
        max_buy_zb2 = min(max_buy_zb2, MAX_PACKAGES)
        max_buy_dep = min(max_buy_dep, MAX_PACKAGES)

        # Генерируем ключевые стратегии (не полный перебор)
        strategies = []

        # 1. Без изменений
        strategies.append((0, 0, 0))

        # 2. Только покупка одного актива (разные количества)
        for zb1_packages in range(1, max_buy_zb1 + 1):
            strategies.append((zb1_packages * self.zb1.step, 0, 0))

        for zb2_packages in range(1, max_buy_zb2 + 1):
            strategies.append((0, zb2_packages * self.zb2.step, 0))

        for dep_packages in range(1, max_buy_dep + 1):
            strategies.append((0, 0, dep_packages * self.dep.step))

        # 3. Только продажа одного актива
        for zb1_packages in range(1, max_sell_zb1 + 1):
            strategies.append((-zb1_packages * self.zb1.step, 0, 0))

        for zb2_packages in range(1, max_sell_zb2 + 1):
            strategies.append((0, -zb2_packages * self.zb2.step, 0))

        for dep_packages in range(1, max_sell_dep + 1):
            strategies.append((0, 0, -dep_packages * self.dep.step))

        # 4. Комбинированные стратегии (покупка двух активов)
        # ЦБ1 + ЦБ2
        for zb1_packages in range(0, min(3, max_buy_zb1) + 1):
            zb1_change = zb1_packages * self.zb1.step
            cost_zb1 = zb1_change * (1 + self.zb1.commission)

            for zb2_packages in range(0, min(3, max_buy_zb2) + 1):
                zb2_change = zb2_packages * self.zb2.step
                cost_zb2 = zb2_change * (1 + self.zb2.commission)

                if cost_zb1 + cost_zb2 <= free_val:
                    strategies.append((zb1_change, zb2_change, 0))

        # ЦБ1 + Депозит
        for zb1_packages in range(0, min(3, max_buy_zb1) + 1):
            zb1_change = zb1_packages * self.zb1.step
            cost_zb1 = zb1_change * (1 + self.zb1.commission)

            for dep_packages in range(0, min(3, max_buy_dep) + 1):
                dep_change = dep_packages * self.dep.step
                cost_dep = dep_change * (1 + self.dep.commission)

                if cost_zb1 + cost_dep <= free_val:
                    strategies.append((zb1_change, 0, dep_change))

        # ЦБ2 + Депозит
        for zb2_packages in range(0, min(3, max_buy_zb2) + 1):
            zb2_change = zb2_packages * self.zb2.step
            cost_zb2 = zb2_change * (1 + self.zb2.commission)

            for dep_packages in range(0, min(3, max_buy_dep) + 1):
                dep_change = dep_packages * self.dep.step
                cost_dep = dep_change * (1 + self.dep.commission)

                if cost_zb2 + cost_dep <= free_val:
                    strategies.append((0, zb2_change, dep_change))

        # Фильтруем по допустимости
        valid_controls = []
        for control in strategies:
            delta_zb1, delta_zb2, delta_dep = control

            # Проверяем кратность шагам
            if (not self.zb1.is_change_valid(delta_zb1) or
                    not self.zb2.is_change_valid(delta_zb2) or
                    not self.dep.is_change_valid(delta_dep)):
                continue

            # Рассчитываем комиссию
            commission = self._calculate_total_commission(delta_zb1, delta_zb2, delta_dep)

            # Новые значения
            new_zb1 = zb1_val + delta_zb1
            new_zb2 = zb2_val + delta_zb2
            new_dep = dep_val + delta_dep
            new_free = free_val - (delta_zb1 + delta_zb2 + delta_dep) - commission

            # Проверяем ограничения
            if (new_zb1 < self.zb1.min_amount - 1e-10 or
                    new_zb2 < self.zb2.min_amount - 1e-10 or
                    new_dep < self.dep.min_amount - 1e-10 or
                    new_free < -1e-10):
                continue

            valid_controls.append(control)

        return valid_controls

    @lru_cache(maxsize=20000)
    def _bellman_value(self, zb1_val: float, zb2_val: float, dep_val: float,
                       free_val: float, stage: int) -> Tuple[float, Tuple]:
        """
        Рекурсивная функция, реализующая рекуррентное соотношение Беллмана.
        Возвращает максимальное ожидаемое значение и оптимальное управление.

        Используется декоратор @lru_cache для кэширования результатов.
        """
        # Дискретизируем состояние для кэширования
        disc_state = self._discretize_state(zb1_val, zb2_val, dep_val, free_val)
        zb1_disc, zb2_disc, dep_disc, free_disc = disc_state

        # Базовый случай: после последнего этапа
        if stage > 3:
            # В базовом случае используем реальные значения, а не дискретизированные
            total_value = zb1_val + zb2_val + dep_val + free_val
            return total_value, (0, 0, 0)

        # Генерируем допустимые управления
        controls = self._generate_controls_for_state(zb1_disc, zb2_disc, dep_disc, free_disc)

        best_value = -float('inf')
        best_control = (0, 0, 0)

        # Для каждого управления вычисляем ожидаемое значение
        for control in controls:
            delta_zb1, delta_zb2, delta_dep = control

            # Рассчитываем комиссию
            commission = self._calculate_total_commission(delta_zb1, delta_zb2, delta_dep)

            # Применяем управление
            new_zb1 = zb1_val + delta_zb1
            new_zb2 = zb2_val + delta_zb2
            new_dep = dep_val + delta_dep
            new_free = free_val - (delta_zb1 + delta_zb2 + delta_dep) - commission

            # Вычисляем математическое ожидание по всем ситуациям
            expected_value = 0.0

            for situation in self.stages[stage].values():
                # Вероятность ситуации
                probability = situation['p']

                # Применяем коэффициенты роста
                zb1_after = new_zb1 * situation['zb1']
                zb2_after = new_zb2 * situation['zb2']
                dep_after = new_dep * situation['dep']

                # Рекурсивный вызов для следующего этапа
                future_value, _ = self._bellman_value(zb1_after, zb2_after, dep_after,
                                                      new_free, stage + 1)

                # Добавляем вклад этой ситуации
                expected_value += probability * future_value

            # Обновляем лучшее значение
            if expected_value > best_value:
                best_value = expected_value
                best_control = control

        return best_value, best_control

    def find_optimal_strategy(self) -> Dict:
        """
        Находит оптимальную стратегию с помощью обратного хода Беллмана.

        Returns:
            Словарь с информацией об оптимальной стратегии
        """
        # Очищаем кэш перед вычислением
        self._bellman_value.cache_clear()

        # Выполняем обратный ход из начального состояния
        optimal_value, first_control = self._bellman_value(
            self.zb1.current_amount,
            self.zb2.current_amount,
            self.dep.current_amount,
            self.free_cash,
            1
        )

        # Собираем информацию о кэше
        cache_info = self._bellman_value.cache_info()

        return {
            'optimal_value': optimal_value,
            'first_control': first_control,
            'cache_info': cache_info
        }

    def simulate_optimal_path(self) -> Dict:
        """
        Симулирует оптимальный путь для математического ожидания ситуаций.

        Returns:
            Словарь с историей состояний, управлений и комиссий
        """
        # Получаем оптимальную стратегию
        result = self.find_optimal_strategy()
        optimal_value = result['optimal_value']

        # Восстанавливаем оптимальный путь
        states = []
        controls = []
        commissions = []

        # Начальное состояние
        current_state = {
            'zb1': self.zb1.current_amount,
            'zb2': self.zb2.current_amount,
            'dep': self.dep.current_amount,
            'free': self.free_cash
        }
        states.append(current_state.copy())

        # Для каждого этапа
        for stage in range(1, 4):
            # Получаем оптимальное управление для текущего состояния
            if stage == 1:
                control = result['first_control']
            else:
                # Вычисляем оптимальное управление для текущего состояния
                _, control = self._bellman_value(
                    current_state['zb1'],
                    current_state['zb2'],
                    current_state['dep'],
                    current_state['free'],
                    stage
                )

            controls.append(control)

            # Рассчитываем комиссию
            delta_zb1, delta_zb2, delta_dep = control
            commission = self._calculate_total_commission(delta_zb1, delta_zb2, delta_dep)
            commissions.append(commission)

            # Применяем управление
            current_state['zb1'] += delta_zb1
            current_state['zb2'] += delta_zb2
            current_state['dep'] += delta_dep
            current_state['free'] -= (delta_zb1 + delta_zb2 + delta_dep) + commission

            # Применяем математическое ожидание ситуаций
            # Рассчитываем ожидаемые коэффициенты роста
            expected_growth = {
                'zb1': sum(s['zb1'] * s['p'] for s in self.stages[stage].values()),
                'zb2': sum(s['zb2'] * s['p'] for s in self.stages[stage].values()),
                'dep': sum(s['dep'] * s['p'] for s in self.stages[stage].values()),
            }

            current_state['zb1'] *= expected_growth['zb1']
            current_state['zb2'] *= expected_growth['zb2']
            current_state['dep'] *= expected_growth['dep']

            states.append(current_state.copy())

        # Финальное значение
        final_value = (current_state['zb1'] + current_state['zb2'] +
                       current_state['dep'] + current_state['free'])

        return {
            'optimal_expected_value': optimal_value,
            'final_expected_value': final_value,
            'states': states,
            'controls': controls,
            'commissions': commissions,
            'cache_info': result['cache_info']
        }