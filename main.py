from InvestmentManager import InvestmentManager


def main() -> None:
    manager = InvestmentManager()
    res = manager.simulate_expected_path()

    states = res["states"]
    controls = res["controls"]
    commissions = res["commissions"]

    for i in range(3):
        print(f"этап {i + 1}:")
        print(f"\tоптимальное управление: {controls[i]}")
        print(f"\tкомиссия: {commissions[i]:.2f}")
        print(f"\tсостояние в начале этапа: {states[i]}")
        print(f"\tсостояние в конце этапа (матожидание): {states[i + 1]}")

    print(f"\nитоговая сумма (матожидание): {res['final_value']:.2f}")


if __name__ == "__main__":
    main()
