"""
Основная программа для решения задачи управления инвестиционным портфелем.
Использует метод динамического программирования (рекуррентные соотношения Беллмана).
"""

from InvestmentManager import InvestmentManager


def main():
    """Основная функция программы."""
    manager = InvestmentManager()

    # Симулируем оптимальный путь
    result = manager.simulate_optimal_path()

    print(f"ОПТИМАЛЬНАЯ ТРАЕКТОРИЯ (математическое ожидание):")

    states = result['states']
    controls = result['controls']
    commissions = result['commissions']

    for i in range(3):
        print(f"\nЭТАП {i + 1}:")
        print(f"  Начало: ЦБ1={states[i]['zb1']:8.2f}, "
              f"ЦБ2={states[i]['zb2']:8.2f}, Деп={states[i]['dep']:8.2f}, "
              f"Свободные={states[i]['free']:8.2f}")

        print(f"  Управление: ΔЦБ1={controls[i][0]:+8.2f}, "
              f"ΔЦБ2={controls[i][1]:+8.2f}, ΔДеп={controls[i][2]:+8.2f}")

        if commissions[i] > 0:
            print(f"  Комиссия: {commissions[i]:.2f}")

        print(f"  После ситуации: ЦБ1={states[i + 1]['zb1']:8.2f}, "
              f"ЦБ2={states[i + 1]['zb2']:8.2f}, "
              f"Деп={states[i + 1]['dep']:8.2f}, "
              f"Свободные={states[i + 1]['free']:8.2f}")

    final_state = states[-1]
    print(f"\nФИНАЛЬНОЕ СОСТОЯНИЕ ПОРТФЕЛЯ:")
    print(f"  ЦБ1: {final_state['zb1']:10.2f} "
          f"(минимально допустимо: {manager.zb1.min_amount:.2f})")
    print(f"  ЦБ2: {final_state['zb2']:10.2f} "
          f"(минимально допустимо: {manager.zb2.min_amount:.2f})")
    print(f"  Депозит: {final_state['dep']:7.2f} "
          f"(минимально допустимо: {manager.dep.min_amount:.2f})")
    print(f"  Свободные средства: {final_state['free']:7.2f}")

    total_final = (final_state['zb1'] + final_state['zb2'] +
                   final_state['dep'] + final_state['free'])
    print(f"  ОБЩАЯ СУММА: {total_final:10.2f}")
 
    print(f"\nОБЩАЯ КОМИССИЯ ЗА ВСЕ ЭТАПЫ: {sum(commissions):.2f}")


if __name__ == "__main__":
    main()