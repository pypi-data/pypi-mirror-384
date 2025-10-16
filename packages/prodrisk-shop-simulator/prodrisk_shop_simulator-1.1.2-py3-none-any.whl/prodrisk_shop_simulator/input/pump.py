import numpy as np

from pyprodrisk import ProdriskSession


def get_power(PQ: dict[float, dict[str, list[float]]], q: float, h: float) -> float:
    if q == 0:
        return 0.0
    P_res = []
    for (h, pq) in PQ.items():
        P_res.append(np.interp(q, pq['q'], pq['p']))
    return np.interp(h, list(PQ.keys()), P_res)


def get_pump_values(PQ: dict[float, dict[str, list[float]]], max_h_upflow: float, min_h_upflow: float, n_pumps: int): # -> tuple[list[float], list[float], list[float]]:
    h_arr = list(PQ.keys())
    min_h = h_arr[0]
    max_h = h_arr[-1]
    max_h_upflows = [0.0, PQ[max_h]['q'][0]]
    min_h_upflows = [0.0, PQ[min_h]['q'][0]]
    for p in range (1, n_pumps):
        max_h_upflows.append((PQ[max_h]['q'][-1] - PQ[max_h]['q'][0]) / (n_pumps - 1))
        min_h_upflows.append((PQ[min_h]['q'][-1] - PQ[min_h]['q'][0]) / (n_pumps - 1))
    max_h_upflow_steps = np.cumsum(max_h_upflows)
    min_h_upflow_steps = np.cumsum(min_h_upflows)
    average_powers = []
    for p in range(n_pumps):
        # max_h_upflows.append(max_h_upflow / n_pumps)
        # min_h_upflows.append(min_h_upflow / n_pumps)
        min_h_power = get_power(PQ, min_h_upflow_steps[p+1], min_h) - get_power(PQ, min_h_upflow_steps[p], min_h)
        max_h_power = get_power(PQ, max_h_upflow_steps[p+1], max_h) - get_power(PQ, max_h_upflow_steps[p], max_h)
        average_powers.append(0.5 * (min_h_power + max_h_power))

    return max_h_upflows[1:], min_h_upflows[1:], average_powers


def add_variable_pump(ps: ProdriskSession, name: str, max_height: float, min_height: float, topology: list[int], average_powers: list[float], max_h_upflows: list[float], min_h_upflows: list[float]) -> None:
    for i in range(len(average_powers)):
        add_simple_pump(ps, name+str(i), average_powers[i], topology, max_h_upflows[i], min_h_upflows[i], max_height, min_height)


def add_simple_pump(ps: ProdriskSession, name: str, average_power: float, topology: list[int], max_height_upflow: float, min_height_upflow: float, max_pump_height: float, min_pump_height: float, ownerShare: float = 1.0) -> None:
    if not name in ps.model.pump.get_object_names():
        pump = ps.model.pump.add_object(name)
    else:
        pump = ps.model.pump[name]
    pump.name.set(name.upper())
    if topology is not None:
        pump.topology.set(topology) # [module containing the pump, pumped to, pumped from]
    pump.maxHeightUpflow.set(max_height_upflow)
    pump.minHeightUpflow.set(min_height_upflow) # m3/s
    pump.averagePower.set(average_power)
    pump.maxPumpHeight.set(max_pump_height)
    pump.minPumpHeight.set(min_pump_height)
    pump.ownerShare.set(ownerShare)
