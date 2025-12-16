"""
InvestmentManager

ДП (Беллман) для управления портфелем на 3 этапах.

Деньги храним в копейках (int), чтобы не ловить ошибки округления.

solve() строит policy только для достижимых состояний (ветви ситуаций).

simulate_expected_path() строит "среднюю" траекторию (по матожиданию множителей),
поэтому промежуточные состояния могут оказаться недостижимыми.
"""

from typing import Tuple, Dict, List, Set

from problem import (
    START_ZB1, START_ZB2, START_DEP, START_FREE,
    CHANGE_ZB1, CHANGE_ZB2, CHANGE_DEP,
    MIN_ZB1, MIN_ZB2, MIN_DEP,
    COMMISSION_ZB1, COMMISSION_ZB2, COMMISSION_DEP,
    STAGES
)

State = Tuple[int, int, int, int]     # (zb1, zb2, dep, free) in cents
Control = Tuple[int, int, int]        # (dzb1, dzb2, ddep) in cents


class InvestmentManager:
    def __init__(self) -> None:
        self.start_state: State = (
            int(START_ZB1 * 100),
            int(START_ZB2 * 100),
            int(START_DEP * 100),
            int(START_FREE * 100),
        )

        self.step_zb1 = int(CHANGE_ZB1 * 100)
        self.step_zb2 = int(CHANGE_ZB2 * 100)
        self.step_dep = int(CHANGE_DEP * 100)

        self.min_zb1 = int(MIN_ZB1 * 100)
        self.min_zb2 = int(MIN_ZB2 * 100)
        self.min_dep = int(MIN_DEP * 100)

        self.c_zb1 = float(COMMISSION_ZB1)
        self.c_zb2 = float(COMMISSION_ZB2)
        self.c_dep = float(COMMISSION_DEP)

        self.stages = self._prepare_stages(STAGES)

        self.dp: Dict[int, Dict[State, float]] = {}
        self.policy: Dict[int, Dict[State, Control]] = {}
        self.reachable: Dict[int, Set[State]] = {}

        # маленький кэш для snap, чтобы не искать каждый раз заново
        self._snap_cache: Dict[Tuple[int, State], State] = {}

    @staticmethod
    def _prepare_stages(raw: Dict) -> Dict[int, List[Dict]]:
        stages: Dict[int, List[Dict]] = {}
        for k, situations in raw.items():
            stages[k] = []
            for s in situations.values():
                stages[k].append({
                    "p": float(s["p"]),
                    "zb1": int(round(float(s["zb1"]) * 100)),
                    "zb2": int(round(float(s["zb2"]) * 100)),
                    "dep": int(round(float(s["dep"]) * 100)),
                })
        return stages

    def _commission(self, dz1: int, dz2: int, dd: int) -> int:
        return (
            int(round(abs(dz1) * self.c_zb1)) +
            int(round(abs(dz2) * self.c_zb2)) +
            int(round(abs(dd) * self.c_dep))
        )

    def _quantize(self, state: State) -> State:
        z1, z2, d, f = state

        def q(x: int, step: int) -> int:
            return (x // step) * step

        return (
            q(z1, max(100, self.step_zb1 // 2)),
            q(z2, max(100, self.step_zb2 // 4)),
            q(d, max(100, self.step_dep // 2)),
            q(f, 100),
        )

    def _apply_control(self, state: State, u: Control) -> State | None:
        z1, z2, d, f = state
        dz1, dz2, dd = u

        if dz1 % self.step_zb1 != 0 or dz2 % self.step_zb2 != 0 or dd % self.step_dep != 0:
            return None

        nz1, nz2, nd = z1 + dz1, z2 + dz2, d + dd
        if nz1 < self.min_zb1 or nz2 < self.min_zb2 or nd < self.min_dep:
            return None

        comm = self._commission(dz1, dz2, dd)
        nf = f - dz1 - dz2 - dd - comm
        if nf < 0:
            return None

        return self._quantize((nz1, nz2, nd, nf))

    def _apply_situation(self, state: State, s: Dict) -> State:
        z1, z2, d, f = state
        return self._quantize((
            (z1 * s["zb1"]) // 100,
            (z2 * s["zb2"]) // 100,
            (d * s["dep"]) // 100,
            f
        ))

    def _buy_controls(self, free: int) -> List[Control]:
        res: List[Control] = []

        max_k1 = free // self.step_zb1
        for k1 in range(max_k1 + 1):
            dz1 = k1 * self.step_zb1
            cost1 = dz1 + int(round(dz1 * self.c_zb1))
            if cost1 > free:
                break

            max_k2 = (free - cost1) // self.step_zb2
            for k2 in range(max_k2 + 1):
                dz2 = k2 * self.step_zb2
                cost2 = dz2 + int(round(dz2 * self.c_zb2))
                if cost1 + cost2 > free:
                    break

                rest = free - cost1 - cost2
                max_kd = rest // self.step_dep
                for kd in range(max_kd + 1):
                    dd = kd * self.step_dep
                    costd = dd + int(round(dd * self.c_dep))
                    if cost1 + cost2 + costd > free:
                        break

                    res.append((dz1, dz2, dd))

        return res

    def _corner_sales(self, state: State) -> List[Control]:
        z1, z2, d, _ = state
        res: List[Control] = [(0, 0, 0)]

        if z1 > self.min_zb1:
            res.append((-(z1 - self.min_zb1), 0, 0))
        if z2 > self.min_zb2:
            res.append((0, -(z2 - self.min_zb2), 0))
        if d > self.min_dep:
            res.append((0, 0, -(d - self.min_dep)))

        return res

    def build_reachable(self) -> None:
        self.reachable = {1: set(), 2: set(), 3: set(), 4: set()}
        self.reachable[1].add(self._quantize(self.start_state))

        for k in (1, 2, 3):
            for st in self.reachable[k]:
                _, _, _, free = st
                controls = self._buy_controls(free) + self._corner_sales(st)

                for u in controls:
                    st_u = self._apply_control(st, u)
                    if st_u is None:
                        continue
                    for sit in self.stages[k]:
                        self.reachable[k + 1].add(self._apply_situation(st_u, sit))

    def solve(self) -> None:
        self._snap_cache.clear()
        self.build_reachable()

        self.dp = {4: {}}
        for st in self.reachable[4]:
            self.dp[4][st] = float(sum(st))

        self.policy = {1: {}, 2: {}, 3: {}}

        for k in (3, 2, 1):
            self.dp[k] = {}
            for st in self.reachable[k]:
                best_val = -1e18
                best_u: Control = (0, 0, 0)

                _, _, _, free = st
                controls = self._buy_controls(free) + self._corner_sales(st)

                for u in controls:
                    st_u = self._apply_control(st, u)
                    if st_u is None:
                        continue

                    val = 0.0
                    for sit in self.stages[k]:
                        st_next = self._apply_situation(st_u, sit)
                        val += sit["p"] * self.dp[k + 1][st_next]

                    if val > best_val:
                        best_val = val
                        best_u = u

                self.dp[k][st] = best_val
                self.policy[k][st] = best_u

    def _snap_state(self, stage: int, st: State) -> State:
        """
        Если st отсутствует в policy[stage], выбираем ближайшее по простой метрике.
        Это нужно только для демонстрационной траектории.
        """
        st = self._quantize(st)
        key = (stage, st)
        if key in self._snap_cache:
            return self._snap_cache[key]

        if st in self.policy[stage]:
            self._snap_cache[key] = st
            return st

        candidates = list(self.policy[stage].keys())
        if not candidates:
            self._snap_cache[key] = st
            return st

        z1, z2, d, f = st

        def dist(a: State) -> int:
            a1, a2, ad, af = a
            return (
                abs(a1 - z1) // max(1, self.step_zb1) +
                abs(a2 - z2) // max(1, self.step_zb2) +
                abs(ad - d) // max(1, self.step_dep) +
                abs(af - f) // 100
            )

        best = min(candidates, key=dist)
        self._snap_cache[key] = best
        return best

    def simulate_expected_path(self) -> Dict:
        self.solve()

        cur = self._quantize(self.start_state)
        states: List[State] = [cur]
        controls: List[Control] = []
        commissions: List[int] = []

        for k in (1, 2, 3):
            cur_for_policy = self._snap_state(k, cur)
            u = self.policy[k][cur_for_policy]

            controls.append(u)
            commissions.append(self._commission(*u))

            st_u = self._apply_control(cur_for_policy, u)
            if st_u is None:
                st_u = cur_for_policy

            # матожидательные коэффициенты (для печати "средней" траектории)
            zb1_exp = sum(s["p"] * s["zb1"] for s in self.stages[k])
            zb2_exp = sum(s["p"] * s["zb2"] for s in self.stages[k])
            dep_exp = sum(s["p"] * s["dep"] for s in self.stages[k])

            z1, z2, d, f = st_u
            cur = self._quantize((
                int((z1 * zb1_exp) // 100),
                int((z2 * zb2_exp) // 100),
                int((d * dep_exp) // 100),
                f
            ))
            states.append(cur)

        return {
            "states": [(a / 100, b / 100, c / 100, f / 100) for a, b, c, f in states],
            "controls": [(u1 / 100, u2 / 100, ud / 100) for u1, u2, ud in controls],
            "commissions": [x / 100 for x in commissions],
            "final_value": sum(states[-1]) / 100
        }
