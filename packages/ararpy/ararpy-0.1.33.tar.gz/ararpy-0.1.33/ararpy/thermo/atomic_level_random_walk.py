#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2024 Yang
# argon atomic_level_random_walk model - main
# ==========================================
#
#
#
"""
import os
import pickle
import numpy as np
import math
import copy
import time
from typing import List

np.set_printoptions(precision=18, threshold=10000, linewidth=np.inf)

SETUP_PRINT = "natoms = {0}, nsteps = {1}, grain_size = {2}, time_scale = {3}, size_scale = {4}, number_scale = {5}"


def _uniform_sphere_step(step_length, shape):
    """
    在三维空间中生成均匀分布的球面样本，且步长严格为指定长度。

    Parameters:
        step_length (array, float): 步长的固定长度, (n, m)
        num_samples (tuple): 步长shape, (n, m)

    Returns:
        np.ndarray: 形状为 (num_samples, 3) 的数组，每行是一个随机步长向量
    """
    # 随机生成方位角 phi 和极角的 cos(theta)
    num_samples, dimension = shape
    phi = np.random.uniform(0, 2 * np.pi, num_samples)
    cos_theta = np.random.uniform(-1, 1, num_samples)
    sin_theta = np.sqrt(1 - cos_theta ** 2)  # sin(theta) = sqrt(1 - cos^2(theta))

    # 将球面坐标转换为笛卡尔坐标
    x = sin_theta * np.cos(phi)
    y = sin_theta * np.sin(phi)
    z = cos_theta

    # 构建单位向量
    unit_vectors = np.vstack((x, y, z)).T

    # 乘以步长，得到最终的步长向量
    steps = step_length * unit_vectors
    return steps


def walker(pos, step_length, total_nsteps, min_bound, max_bound, scale=0., compensation=0, remove=True,
           conditions=None, boundary_factor=1, decay=0, parent=0):

    if len(pos) == 0:
        return pos

    dimension = pos.shape[1] if len(pos.shape) > 1 else 1

    sigma = step_length * math.sqrt(scale)

    if conditions is None:
        if dimension == 3:
            conditions = np.array([[-50, -50, -50, 50, 50, 50, 1]])
        else:
            conditions = np.array([[-50, -50, 50, 50, 1]])

    num_big_steps = int(total_nsteps // scale) if int(scale) > 1 else 0
    num_small_steps = int(total_nsteps % scale) if int(scale) > 1 else int(total_nsteps)

    for _ in range(num_big_steps):
        # print(f"new walker {_ = } {len(pos) = }")
        # 边界判断（布尔掩码）
        in_boundary_mask = np.all(
            (pos >= (min_bound + sigma * compensation)) & (pos <= (max_bound - sigma * compensation)), axis=1)
        in_core = pos[in_boundary_mask]
        in_boundary = pos[~in_boundary_mask]

        # 核心粒子随机行走
        coefficients = np.ones(len(in_core))
        for each in conditions:
            # each = x1, y1, z1, x2, y2, z2, coeff for dimension=3
            cond = np.all(
                (in_core >= np.array(each[:dimension])) & (in_core <= np.array(each[dimension:int(2*dimension)])),
                axis=1)
            coefficients = np.where(cond, each[-1] ** 0.5, coefficients)
        steps = np.random.normal(0, sigma, size=in_core.shape)
        in_core += steps * coefficients[:, None]

        # 将边界粒子以更小 scale 的步长模拟
        if scale > 1:
            in_boundary = walker(in_boundary, step_length, scale, min_bound, max_bound, scale // 2,
                                 compensation, remove, conditions, boundary_factor)

        # 拼接核心和边界粒子
        pos = np.concatenate((in_boundary, in_core))

        # 移除超出范围的粒子
        if remove:
            pos = pos[np.all((pos >= min_bound) & (pos <= max_bound), axis=1)]

    # 最后处理 scale < 1 的小步模拟, boundary_factor用来缩放这里的处理步数，1 < boundary_factor <= 1如果 boundary_factor=1，将完全吻合实际
    # boundary_factor < 1 将加快一些速度， boundary_factor=0 将忽略小步数
    k = boundary_factor * max(conditions[:, -1])
    for _ in range(int(num_small_steps * k)):
        coefficients = np.ones(len(pos))
        for each in conditions:
            cond = np.all((pos >= np.array(each[:dimension])) & (pos <= np.array(each[dimension:int(2*dimension)])),
                          axis=1)
            coefficients = np.where(cond, (each[-1] / k) ** 0.5, coefficients)
            # coefficients = np.where(cond, coeff ** 0.5, coefficients)
        steps = np.random.normal(0, step_length, size=np.shape(pos))
        pos += steps * coefficients[:, None]

        if remove:
            pos = pos[np.all((pos >= min_bound) & (pos <= max_bound), axis=1)]

    return pos


def walker2(pos: np.ndarray, duration, step_length, min_bound, max_bound, time_scale, frequency,
            conditions=None, remove: bool = True, decay=0, parent=0):
    """
    :return:
    """

    # Ar40模拟时不能判断，因为会增加
    # if len(pos) == 0:
    #     return pos

    dimension = pos.shape[-1] if len(pos.shape) > 1 else 1


    dt = time_scale
    if conditions is None:
        if dimension == 3:
            conditions = np.array([[-50, -50, -50, 50, 50, 50, 1]])
        else:
            conditions = np.array([[-50, -50, 50, 50, 1]])

    for step in range(int(1e16)):
        n = parent - int(parent * math.exp(-1 * decay * dt / (3600 * 24 * 365.2425)))
        # print(f"number of new pos = {n}")
        parent = parent - n
        new_pos = np.random.uniform(max(max_bound), min(min_bound), size=(int(n), dimension))
        new_pos = new_pos[np.all((new_pos >= min_bound) & (new_pos <= max_bound), axis=1)]
        pos = np.concatenate((pos, new_pos), axis=0)

        res = np.zeros(0).reshape(0, dimension)
        for index, each in enumerate(conditions):
            # each = (x1, y1, z1, x2, y2, z2, gamma)
            d = step_length * math.sqrt(each[-1] * frequency * time_scale)

            locs = np.ones(len(pos)) * 999
            for _index, _each in enumerate(conditions):
                cond = np.all((pos >= np.array(_each[:dimension])) & (pos <= np.array(_each[dimension:int(2*dimension)])), axis=1)
                locs = np.where(cond, _index, locs)

            partial_pos = pos[locs == index]

            # c = len(partial_pos)
            # # 初始化步长
            # steps = np.zeros(partial_pos.shape, dtype=float)
            # # 移动方向, x or y or z
            # directions = np.random.choice(list(range(dimension)), size=c)
            # # 方向, positive or negative, 步长
            # steps[np.arange(c), directions] = np.random.choice([-d, d], size=c, p=[0.5, 0.5])
            steps = np.random.normal(0, d, size=partial_pos.shape)

            partial_pos += steps

            if remove:
                partial_pos = partial_pos[np.all((partial_pos >= min_bound) & (partial_pos <= max_bound), axis=1)]

            res = np.concatenate((res, partial_pos))

        pos = copy.deepcopy(res)

        _t = (step + 1) * dt

        if abs(_t - duration) < dt:
            break

    return pos


class OverEpsilonError(Exception):
    def __init__(self, i, d, e):
        self.i = i
        self.d = d
        self.e = e

    def __str__(self):
        return f"OverEpsilonError: Index = {self.i}, d = {self.d} > e = {self.e}"


class Domain:
    def __init__(self, dimension: int = 3, atom_density: float = 1e14, fraction: float = 1.0,
                 min_bound=None, max_bound=None, **kwargs):

        self.dimension = dimension
        self.size = ...
        self.atom_density = atom_density
        self.fraction = fraction
        self.time_scale = 1
        self.size_scale = 0.05

        self.energy = 120 * 1000  # J/mol
        self.density = 0
        self.fracture = 0
        self.boundary = 0
        self.defect = 0
        self.pho = 1
        self.step_length = 0.0001  # 1 A = 0.1 nm = 0.0001 μm

        self.current_temp = 273.15

        self.inclusions: List[Domain] = []
        self.natoms: int = 0
        self.positions = []
        self.min_bound = min_bound
        self.max_bound = max_bound
        self.remained_per_step = []
        self.released_per_step = []

        self.attr = {}

        for key, val in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, val)

        self.setup()

    def setup(self):
        """
        Used to set or reset positions of atoms
        :return:
        """

        # 初始化粒子位置，随机分布在网格内
        # 初始原子个数  1e14 原子密度 个/立方厘米   1e-4是单位换算 cm/µm
        natoms = int(self.atom_density ** (self.dimension / 3) * (abs(max(self.max_bound) - min(self.min_bound)) * 1e-4) ** self.dimension)
        natoms = 1 if natoms == 0 else natoms
        self.positions = np.random.uniform(max(self.max_bound), min(self.min_bound), size=(int(natoms), self.dimension))
        self.positions = self.positions[np.all((self.positions >= self.min_bound) & (self.positions <= self.max_bound), axis=1)]
        for dom in self.inclusions:
            self.positions = self.positions[~np.all((self.positions >= dom.min_bound) & (self.positions <= dom.max_bound), axis=1)]
        self.natoms = len(self.positions)

        self.remained_per_step = []
        self.released_per_step = []

    def get_gamma(self, energy: float = None, temperature: float = None):
        r = 8.31446261815324  # J / (K * mol)
        T = self.current_temp if temperature is None else temperature
        e = self.energy if energy is None else energy
        alpha = 1 - self.density
        p1 = math.exp(- e / (r * T))
        p2 = math.exp(- e / 2 / (r * T))  # p2是给定活化能的一半，用于假定晶面扩散的活化能
        gamma = p1 * alpha * (1 - self.fracture) + self.fracture * p2 + self.boundary + self.defect
        return gamma

    def get_natoms(self, pos=None):
        if pos is None:
            return len(self.positions)
        pos = pos[np.all((pos >= self.min_bound) & (pos <= self.max_bound), axis=1)]
        for dom in self.inclusions:
            pos = pos[~np.all((pos >= dom.min_bound) & (pos <= dom.max_bound), axis=1)]
        return len(pos)

    def set_attr(self, name, value, index=None):
        if index is None:
            self.attr.update({name: value})
        else:
            if name not in self.attr.keys():
                self.attr.update({name: {}})
            self.attr[name].update({index: value})


class DiffSimulation:
    def __init__(self):
        self.name = "example"
        self.loc = "examples"
        self.score = 0
        self.end_at = 0
        self.dimension = 3

        self.thermal_log = []

        self.size_scale = 1
        self.length_scale = 1

        self.atom_density = 1e14  # 原子密度 个/立方厘米
        self.frequency = 1e13  # 每秒振动的次数, Debye frequency

        self.grain_size = 300  # 0.3 mm = 300 μm = 300000 nm
        self.grid_size = self.grain_size * self.size_scale  # 网格大小
        self.nsteps: int = ...
        self.natoms: int = ...
        self.epsilon = 1e-5
        self.step_length = 0.0001 * 2.5  # 1 A = 0.1 nm = 0.0001 μm

        self.seq: [List, np.ndarray] = []
        self.domains: List[Domain] = []
        self.positions: [List, np.ndarray] = []

        self.remained_per_step = []
        self.released_per_step = []

    def setup(self):
        """
        Used to set or reset positions of atoms
        :return:
        """
        # 网格大小和颗粒边界
        self.grid_size = self.grain_size * self.size_scale  # 网格大小
        center = np.array([0 for i in range(self.dimension)])
        self.min_bound = center - self.grid_size / 2
        self.max_bound = center + self.grid_size / 2

        # 粒子位置
        self.positions = np.concatenate([dom.positions for dom in self.domains])
        # 粒子数目
        self.natoms = len(self.positions)

        self.remained_per_step = []
        self.released_per_step = []

    def run_sequence(self, times, temperatures, statuses, targets, domains: List[Domain], nsteps_factor=None,
                     simulating: bool = False, epsilon=0.001, start_time=0, k=1.2, use_walker1=True,
                     scoring: bool = False, decay=0, parent=0):
        pos = copy.deepcopy(self.positions)
        self.seq = []  # 用于记录参数

        for index, (duration, temperature, target, status) in enumerate(zip(times, temperatures, targets, statuses)):

            self.seq.append({})

            loop = 0
            e_low = 100 * 1000
            e_up = 300 * 1000

            _start = time.time()
            heating_duration = duration - start_time  # in seconds
            start_time = duration
            temperature = temperature + 273.15  # in Kelvin

            while loop < 50:

                e = (e_low + e_up) / 2

                total_steps = self.frequency * heating_duration  # 振动次数
                conditions = np.array(
                    [[*dom.min_bound, *dom.max_bound,
                      dom.get_gamma(temperature=temperature, energy=e if simulating else None)] for dom in domains if dom.energy != 0 and not simulating])

                if use_walker1:

                    # print(f"调整前: {nsteps_factor = }, gamma = {conditions[0][-1]}, {total_steps = }")
                    nsteps_factor = 10 ** math.floor(
                        -math.log10(max(conditions[:, -1]))) * 1000  # 用来调节次数和步长的巨大差异，次数太大，但步程太小
                    while int(total_steps / nsteps_factor) < 1:
                        nsteps_factor /= 10
                    while int(total_steps / nsteps_factor) > 10000:
                        nsteps_factor *= 10
                    total_steps = int(total_steps / nsteps_factor)  # 振动次数
                    conditions[:, -1] *= nsteps_factor
                    compensation = max(3, *(np.ceil(np.sqrt(conditions[:, -1])) * 3))
                    boundary_factor = 1
                    if max(conditions[:, -1]) > 1000:
                        # k = 0时，bf = 1, 完全无缩放 # k = 1时，bf <= 0.5 小步行走将至少缩放一半   # 推荐值 k = 1.2
                        boundary_factor = 0.1 ** (k * math.log10(1 + (max(conditions[:, -1]) // 1000)))
                    step_length = self.step_length / np.sqrt(pos.shape[1] if len(pos.shape) > 1 else 1)
                    scale = int(total_steps)
                    print(f"调整后: {nsteps_factor = }, gamma = {conditions[0][-1]}, {total_steps = }, {compensation = }, {boundary_factor = }")

                    _pos = walker(
                        copy.deepcopy(pos), step_length=step_length, total_nsteps=total_steps,
                        min_bound=self.min_bound, max_bound=self.max_bound, scale=scale,
                        compensation=compensation, remove=True, conditions=conditions, boundary_factor=boundary_factor,
                        decay=decay, parent=parent
                    )

                    # self.seq[index].update({
                    #     "duration": duration, "temperature": temperature, "target": target, "step_length": step_length,
                    #     "scale": scale, "compensation": compensation, "boundary_factor": boundary_factor, "e": e,
                    #     "simulation": simulating, "nsteps_factor": nsteps_factor, "conditions": conditions
                    # })

                else:
                    step_length = self.step_length / np.sqrt(pos.shape[1] if len(pos.shape) > 1 else 1)
                    scale = k
                    _pos = walker2(copy.deepcopy(pos), duration=heating_duration, step_length=step_length,
                                   min_bound=self.min_bound, max_bound=self.max_bound, time_scale=scale,
                                   frequency=self.frequency, conditions=conditions, remove=True, decay=decay, parent=parent)
                    boundary_factor = 1
                    compensation = 0

                self.seq[index].update({
                    "duration": duration, "temperature": temperature, "target": target, "step_length": step_length,
                    "scale": scale, "compensation": compensation, "boundary_factor": boundary_factor, "e": e,
                    "simulation": simulating, "nsteps_factor": nsteps_factor, "conditions": conditions
                })

                released = 1 - len(_pos) / self.natoms
                d = released - target
                if simulating:
                    loop += 1
                    print(f"{e = }, {d = }, {abs(d) <= epsilon}")
                    if abs(d) <= epsilon:
                        break
                    elif d > 0:
                        e_low = e
                    else:
                        e_up = e
                elif scoring:
                    self.score += (d * 100) ** 2
                    print(f"{self.score = }, {d = }")
                    if self.score > 4 * (index + 1):
                        raise OverEpsilonError(index, self.score, 4 * (index + 1))
                    else:
                        break
                else:
                    break

            pos = _pos

            if status:
                # status == True: argon collection, False: pumping
                for dom in self.domains:
                    _c = dom.get_natoms(pos)
                    dom.remained_per_step.append(_c)
                    dom.released_per_step.append(dom.natoms - _c)
                    dom.set_attr("energy", float(e), index=index)

                self.remained_per_step.append(len(pos))
                self.released_per_step.append(self.natoms - len(pos))

            print(f"{index = } {duration = }s - {heating_duration = }s - {temperature = }K - {total_steps = } - conc = {len(pos) / self.natoms * 100:.2f}% - {time.time() - _start:.5f}s")

        self.positions = copy.deepcopy(pos)

    def run_persecond(self, times, temperatures, statuses, targets, domains: List[Domain], scale=None,
                     simulation: bool = False, epsilon=0.001, start_time=0):
        seq = []
        for i in range(1, int(times[-1] + 1), 300):
            for index, time in enumerate(times):
                if (times[index-1] if index > 0 else 0) < i <= times[index]:
                    seq.append([i, temperatures[index], statuses[index], targets[index]])
        seq = np.transpose(seq)
        return self.run_sequence(*seq, domains=domains, nsteps_factor=scale, simulating=simulation,
                                 epsilon=epsilon, start_time=start_time)

def demo_init(n, es, fs, di, gs, ds, fr, ss=1):
    demo = DiffSimulation()
    # fs 应从大到小，父空间在前，子空间在后

    # demo.grain_size = 300
    # demo.size_scale = 0.05
    # demo.atom_density = 1e14  # 原子密度 个/立方厘米

    demo.dimension = di                 # dimension, 1 or 3
    demo.size_scale = 1                 # size_scale
    demo.grain_size = gs                # grain_szie
    demo.frequency = fr                 # frequency

    # domains应该从外到内
    domains = []
    for i in range(n-1, 0-1, -1):
        size = int(demo.grain_size * fs[i]) * demo.size_scale
        center = np.zeros(demo.dimension)
        if isinstance(ds, (int, float)) or len(ds) == 1:
            demo.atom_density = ds              # atom_density  # 原子密度 个/立方厘米
            if i == 2:
                ad = ds * 5 / 4
            else:
                ad = ds
        else:
            ad = ds[i]
        dom = Domain(
            dimension=demo.dimension, atom_density=ad, min_bound=center - size / 2, max_bound=center + size / 2,
            energy=es[i], fraction=fs[i], inclusions=[domains[-1]] if len(domains) >= 1 else []
        )
        domains.append(dom)
    # domains应该从外到内, 上面为了inclusion以及方便不同扩散域设置不同的密度，要按照从小到大的顺序生成，但是后面行走的时候要根据不同条件设置系数，要从外到内
    demo.domains = sorted(domains, key=lambda dom: dom.fraction, reverse=True)

    demo.setup()

    a = [f"{dom.fraction = }, {dom.energy = }, {dom.natoms = }, {dom.atom_density = }" for dom in demo.domains]

    print(
        f"Total Atoms: {demo.natoms}\n" + "\n".join(a)
    )

    return demo

def run(times, temps, statuses, energies, fractions, ndoms: int = 1, grain_szie=275, atom_density=1e10, frequency=1e13,
        dimension: int = 3, targets: list = None, epsilon: float = 0.001, simulation: bool = False,
        file_name: str = "Y70", ignore_error: bool = False, positions=None, **kwargs):
    """
    :param times:
    :param temps:
    :param statuses:
    :param energies:
    :param fractions:
    :param dimension:
    :param ndoms:
    :param targets:
    :param epsilon:
    :param simulation:
    :param file_name:
    :param ignore_error:
    :return:
    """

    try:
        # demo.run_persecond(times=times, temperatures=temps, domains=demo.domains, targets=target,
        #                    epsilon=epsilon, simulation=simulation)
        demo = demo_init(ndoms, energies, fractions, dimension, grain_szie, atom_density, frequency, ss=1)
        demo.name = f"{file_name}"
        demo.thermal_log = list(zip(times, temps))

        if positions is not None:
            demo.positions = positions
            demo.natoms = len(positions)

        demo.run_sequence(times=times, temperatures=temps, statuses=statuses, targets=targets, domains=demo.domains,
                          epsilon=epsilon, simulating=simulation, **kwargs)
        return demo, True
    except OverEpsilonError as e:
        if ignore_error:
            return demo, False
        else:
            raise


def run_40ar(times, temps, statuses, energies, fractions, ndoms: int = 1, grain_szie=275, atom_density=1e10, frequency=1e13,
        dimension: int = 3, targets: list = None, epsilon: float = 0.001, simulation: bool = False,
        file_name: str = "Y70", ignore_error: bool = False, **kwargs):
    """
    :param times:
    :param temps:
    :param statuses:
    :param energies:
    :param fractions:
    :param dimension:
    :param ndoms:
    :param targets:
    :param epsilon:
    :param simulation:
    :param file_name:
    :param ignore_error:
    :return:
    """

    demo = DiffSimulation()

    def _(n, es, fs):
        # fs 应从大到小，父空间在前，子空间在后

        # demo.grain_size = 300
        # demo.size_scale = 0.05
        # demo.atom_density = 1e14  # 原子密度 个/立方厘米
        demo.dimension = dimension

        demo.size_scale = 1
        demo.grain_size = grain_szie
        demo.atom_density = atom_density  # 原子密度 个/立方厘米
        demo.frequency = frequency

        # domains应该从外到内
        domains = []
        for i in range(n-1, 0-1, -1):
            size = int(demo.grain_size * fs[i]) * demo.size_scale
            center = np.zeros(demo.dimension)
            dom = Domain(
                dimension=demo.dimension, atom_density=demo.atom_density, min_bound=center - size / 2, max_bound=center + size / 2,
                energy=es[i], fraction=fs[i], inclusions=[domains[-1]] if len(domains) >= 1 else []
            )
            domains.append(dom)
        # domains应该从外到内, 上面为了inclusion以及方便不同扩散域设置不同的密度，要按照从小到大的顺序生成，但是后面行走的时候要根据不同条件设置系数，要从外到内
        demo.domains = sorted(domains, key=lambda dom: dom.fraction, reverse=True)

        demo.setup()

        demo.name = f"{file_name}"

        print(f"Total Atoms: {demo.natoms}, atoms in each dom: {[dom.natoms for dom in demo.domains]} filename: {demo.name}")

        demo.run_sequence(times=times, temperatures=temps, statuses=statuses, targets=targets, domains=demo.domains,
                          epsilon=epsilon, simulating=simulation, **kwargs)
        # demo.run_persecond(times=times, temperatures=temps, domains=demo.domains, targets=target,
        #                    epsilon=epsilon, simulation=simulation)

        return demo

    try:
        return _(ndoms, energies, fractions), True
    except OverEpsilonError as e:
        if ignore_error:
            return demo, False
        else:
            raise


def save_ads(ads: DiffSimulation, dir_path: str = None, name: str = None):
    if dir_path is None:
        dir_path = ""
    if name is None:
        name = ads.name
    if not name.endswith(".ads"):
        name = f"{name}.ads"
    dir_path = os.path.join(dir_path, name)
    with open(dir_path, 'wb') as f:
        f.write(pickle.dumps(ads))
    return name


def read_ads(file_path: str) -> DiffSimulation:

    class RenameUnpickler(pickle.Unpickler):
        def find_class(self, module: str, name: str):
            if "argon_diffusion_simulator" in module:
                return super(RenameUnpickler, self).find_class(DiffSimulation().__module__, name)
            else:
                return super(RenameUnpickler, self).find_class(module, name)

    def renamed_load(file_obj) -> DiffSimulation:
        return RenameUnpickler(file_obj).load()

    try:
        with open(file_path, 'rb') as f:
            return renamed_load(f)
    except (Exception, BaseException):
        raise ValueError(f"ModuleNotFoundError")
