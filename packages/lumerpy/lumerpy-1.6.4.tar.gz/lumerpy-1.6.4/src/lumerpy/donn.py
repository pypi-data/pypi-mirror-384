# donn=diffractive optical neural network
# 本页面包含衍射网络建模用的一些函数
import os
import sys
import lumerpy as lupy
from .fdtd_manager import get_fdtd_instance
import numpy as np

u = 1e-6


def add_metalines(length_ls, x_start=0, y_start=0, width=0.2 * u, height=0.22 * u, period=0.5 * u, distance=3 * u,
				  layer_num=1, group_num=3, layer_temp=0, material="SiO2 (Glass) - Palik"
				  ):
	metaline_ls = []
	FD = get_fdtd_instance()
	FD.addstructuregroup(name="metalines" + str(layer_temp))
	FD.set("x", 0)
	FD.set("y", 0)
	FD.set("z", 0)
	x = x_start  # 从x=0开始放槽
	y = y_start  # 从y=0开始放槽
	length_pin = 0  # 用于位移槽长列表的指针
	name_series_slot = "metalines"
	name_series_phase = "phase"
	# layer_num = length_ls.shape[0]	# 为了兼容性，还是先手动指定层数吧
	for j in range(layer_num):  # 放完一层放下一层
		# 此处共有三种y的初始值设置方法：①y=0；②y=period / 2；③y=width/2
		# ①并不好，会有边界问题，程序这里其实没写好y=0情况下的应对，不要用
		# ②是较为美观且推荐的做法，会让槽组整体往上平移半个周期，美观一些
		# ③是可行但不是那么推荐的做法，让槽组的边缘和仿真边缘贴合，可能出现边缘问题
		y = period / 2  # period/2是整体往上提一点，对称好看一些，width/2是为了解决中心线一半在仿真区域外的问题
		# name_layer_slot = name_series_slot + f"{j}"	# 这里注释掉，这是以前只有一层的写法
		name_layer_slot = name_series_slot + str(layer_temp)
		name_layer_phase = name_series_phase + f"{j}"
		group_count = 0  # 用于辅助计数槽组是否放置完毕的中间变量
		for i in range(int(group_num * len(length_ls) / layer_num)):  # 放完一个放下一个
			name_slot = name_layer_slot + f"{i}"
			name_phase = name_layer_phase + f"{i}"
			y_min, y_max = lupy.tools.span_min(y, width)
			metaline_ls.append(lupy.add_rect(name_slot,
											 x_min=x, x_max=x + length_ls[length_pin],
											 y_min=y_min, y_max=y_max,
											 z_min=0, z_max=height,
											 material=material))
			# FD.addtogroup("slots")		# 如果添加到槽组里会有很多bug，例如不方便通过对象列表访问了，这里先注释掉
			# 这一段开始添加槽监视器
			# lupy.add_power_monitor(name_phase + "_front", monitor_type="2D X-normal", x_min=x, x_max=x,
			# 				  y_min=y - width / 2, y_max=y + width / 2, z_min=0, z_max=height)
			# # FD.addtogroup("slots")
			# lupy.add_power_monitor(name_phase + "_back", monitor_type="2D X-normal", x_min=x + length_ls[length_pin],
			# 				  x_max=x + length_ls[length_pin], y_min=y - width / 2, y_max=y + width / 2, z_min=0,
			# 				  z_max=height)
			# # FD.addtogroup("slots")
			# lupy.add_power_monitor(name_phase + "_oversee", monitor_type="2D Z-normal", x_min=x,
			# 				  x_max=x + length_ls[length_pin], y_min=y - width / 2, y_max=y + width / 2,
			# 				  z_min=height / 2,
			# 				  z_max=height / 2)
			# # FD.addtogroup("slots")
			# lupy.add_power_monitor(name=name_phase + "_middle", x_min=x, x_max=x + length_ls[length_pin], y_min=y,
			# 				   y_max=y,
			# 				   z_min=height / 2, z_max=height / 2)
			group_count = group_count + 1
			if group_count % group_num == 0:
				length_pin = length_pin + 1
			y = y + period  # 向y正方向放置下一个槽
		x = x + distance  # 向x正方形放置下一个层
	# x = x + distance + 2 * u  # 向x正方形放置下一个层
	# print("警告，这里x随层有位移！")
	# x = x - 2 * u * layer_num
	# return metaline_ls[-1]["x max"], y - period / 2  # 对应②
	return x, y - period / 2, metaline_ls  # 对应②


def add_metalines_shift(length_ls, x_start=0, y_start=0, width=0.2 * u, height=0.22 * u, period=0.5 * u, distance=3 * u,
						layer_num=1, group_num=3, layer_temp=0, material="SiO2 (Glass) - Palik",
						mesh_metaline_flag=False, mesh_equ_idx=2
						):
	"""
	批量化放置衍射线，并返回相关参数
	需要注意，返回的x_min,x_max,y_min,y_max都是下一个周期的初始位置，其真实结果需要减去周期值
	"""
	metaline_ls = []
	FD = get_fdtd_instance()
	FD.addstructuregroup(name="metalines" + str(layer_temp))
	FD.set("x", 0)
	FD.set("y", 0)
	FD.set("z", 0)
	x = x_start  # 从x=0开始放槽
	y = y_start  # 从y=0开始放槽，注意这里y指的是SiO2槽的中心位置，这个中心位置为0，意味着Si槽的中心位置和理论设计位置重合
	length_pin = 0  # 用于位移槽长列表的指针
	name_series_slot = "metalines"
	name_series_phase = "phase"
	# layer_num = length_ls.shape[0]	# 为了兼容性，还是先手动指定层数吧
	for j in range(layer_num):  # 放完一层放下一层
		# y = -width / 2  # 向下偏移1/2width长度，使得硅槽中心位置和理论设计位置重合
		# y = 0
		name_layer_slot = name_series_slot + str(layer_temp)
		name_layer_phase = name_series_phase + f"{j}"
		group_count = 0  # 用于辅助计数槽组是否放置完毕的中间变量
		for i in range(int(group_num * len(length_ls) / layer_num)):  # 放完一个放下一个
			name_slot = name_layer_slot + f"{i}"
			name_phase = name_layer_phase + f"{i}"
			y_min, y_max = lupy.tools.span_min(y, width)
			metaline_ls.append(lupy.add_rect(name_slot,
											 x_min=x, x_max=x + length_ls[length_pin],
											 y_min=y_min, y_max=y_max,
											 z_min=0, z_max=height,
											 material=material))
			# FD.addtogroup("slots")		# 如果添加到槽组里会有很多bug，例如不方便通过对象列表访问了，这里先注释掉
			# 这一段开始添加槽监视器
			# lupy.add_power_monitor(name_phase + "_front", monitor_type="2D X-normal", x_min=x, x_max=x,
			# 				  y_min=y - width / 2, y_max=y + width / 2, z_min=0, z_max=height)
			# # FD.addtogroup("slots")
			# lupy.add_power_monitor(name_phase + "_back", monitor_type="2D X-normal", x_min=x + length_ls[length_pin],
			# 				  x_max=x + length_ls[length_pin], y_min=y - width / 2, y_max=y + width / 2, z_min=0,
			# 				  z_max=height)
			# # FD.addtogroup("slots")
			# lupy.add_power_monitor(name_phase + "_oversee", monitor_type="2D Z-normal", x_min=x,
			# 				  x_max=x + length_ls[length_pin], y_min=y - width / 2, y_max=y + width / 2,
			# 				  z_min=height / 2,
			# 				  z_max=height / 2)
			# # FD.addtogroup("slots")
			# lupy.add_power_monitor(name=name_phase + "_middle", x_min=x, x_max=x + length_ls[length_pin], y_min=y,
			# 				   y_max=y,
			# 				   z_min=height / 2, z_max=height / 2)
			group_count = group_count + 1
			if group_count % group_num == 0:
				length_pin = length_pin + 1
			y = y + period  # 向y正方向放置下一个槽
		if mesh_metaline_flag:
			lupy.simulation.add_mesh(x_min=x - 1 * u, x_max=x + 5 * u,
									 y_min=y_start - width / 2, y_max=y,
									 z_min=0, z_max=height,
									 set_equ_inx_flag=True,
									 equ_x_index=mesh_equ_idx,
									 equ_y_index=mesh_equ_idx,
									 equ_z_index=mesh_equ_idx, )
		x = x + distance  # 向x正方形放置下一个层
	x_min = x_start
	x_max = x
	y_min = y_start - width / 2
	y_max = y - width / 2
	return x_min, x_max, y_min, y_max, metaline_ls


# return x, y	# 对应①
# return x, y - width / 2		# 对应③


# 返回此时的x和y，便于后续设定仿真区域大小和自动放监视器
# y减去width/2的原因是为了补偿前面循环中写的多加的width/2
# y不减去period/2的原因是因为返回值如果也低了，后面的fdtd区域，slab范围整体也会低
def loop_waveguide_neff(length=1 * u, distance=3 * u, source="plane", source_x=0, gaussian_delta_y=1 * u,
						mesh_accuracy=2, dipole_avoid=False, dipole_avoid_delta_x=0.5 * u, run_flag=True, GPU=True,
						group_num=3):
	"""提供一个便于循环调用仿真的函数"""
	length_ls = [length]
	# 用户在这里设置 API 和文件路径
	api_path = r"C:\Program Files\Lumerical\v241\api\python".replace("\\", "/")
	file_path = r"E:\0_Work_Documents\Simulation\12_ERI_LuPy".replace("\\", "/")
	file_name = r"12.0_temp.fsp"
	sys.path.append(os.path.normpath(api_path))  # 添加 API 路径以确保可以成功导入 lumapi
	lupy.tools.check_path_and_file(file_path=file_path, file_name=file_name)
	lupy.setup_paths(api_path, file_path, file_name)  # 设置路径到库
	# --------------------基本设置结束--------------------

	fdtd_instance = lupy.get_fdtd_instance(hide=True, solution_type="FDTD")  # 创建fdtd实例，这应该是第一个实例，hide=True时，隐藏窗口
	# lupy.version()  # 测试一下是否成功
	FD = lupy.get_existing_fdtd_instance()  # 返回创建的实例，以便使用lumapi
	if not FD:
		print("未正确创建实例，请检查")

	# --------------------现在既可以调用lumapi，也可以调用lupy库--------------------

	# return x, y	# 对应①
	# return x, y - width / 2		# 对应③

	# 返回此时的x和y，便于后续设定仿真区域大小和自动放监视器
	# y减去width/2的原因是为了补偿前面循环中写的多加的width/2
	# y不减去period/2的原因是因为返回值如果也低了，后面的fdtd区域，slab范围整体也会低

	def add_basic_monitors():
		# 添加全局监视器，看场俯视图
		ob_moni_glo = FD.addpower()
		FD.set("name", "global")
		FD.set("monitor type", "2D Z-normal")
		FD.set("x min", fdtd_x_min)
		FD.set("x max", fdtd_x_max)
		FD.set("y min", fdtd_y_min)
		FD.set("y max", fdtd_y_max)
		FD.set("z", (fdtd_z_max + fdtd_z_min) / 2)
		# 添加前监视器，看场相位图
		ob_moni_fro = FD.addpower()
		FD.set("name", "front")
		FD.set("monitor type", "2D X-normal")
		FD.set("x", 0)
		FD.set("y min", fdtd_y_min)
		FD.set("y max", fdtd_y_max)
		FD.set("z min", fdtd_z_min)
		FD.set("z max", fdtd_z_max)
		# 添加后监视器，看场相位图
		ob_moni_bac = FD.addpower()
		FD.set("name", "back")
		FD.set("monitor type", "2D X-normal")
		FD.set("x", length_ls[0])
		FD.set("y min", fdtd_y_min)
		FD.set("y max", fdtd_y_max)
		FD.set("z min", fdtd_z_min)
		FD.set("z max", fdtd_z_max)

		return ob_moni_glo, ob_moni_fro, ob_moni_bac

	def add_eri_monitors():
		name_series_eri = "eri"
		for j in range(layer_num):  # 放完一层放下一层
			name_layer_eri = name_series_eri + f"{j}"
			for i in range(len(metaline_ls) - 1):
				moni_x_min = metaline_ls[i]["x min"]
				moni_x_max = metaline_ls[i]["x max"]
				moni_y = (metaline_ls[i + 1]["y"] + metaline_ls[i]["y"]) / 2
				moni_z = metaline_ls[i]["z"]
				lupy.add_power_monitor(name=name_layer_eri + f"{i}", x_min=moni_x_min, x_max=moni_x_max, y_min=moni_y,
									   y_max=moni_y,
									   z_min=moni_z, z_max=moni_z, monitor_type="Linear X")

	u = 1 * 10 ** -6  # micron
	pi = 3.1415927

	width = 0.2 * u
	height = 0.22 * u
	period = 0.5 * u
	# distance = 3 * u
	# distance = 10 * u
	wavelength = 1.55 * u
	source_x_min = -0.5 * u
	# length_ls = [1.437 * u,0.862 * u ,0.287 * u]
	# length_ls = [0.586 * u]
	group_num = group_num  # 单槽组的槽数
	layer_num = 1  # 衍射网络的层数
	k0 = 2 * pi / wavelength
	neff = 2.166
	nslab = 2.84
	metaline_ls = []

	# FD.switchtolayout()  # 例如调用 lumapi 自带的方法
	# FD.deleteall()
	# slots_x_max, slots_y_max = add_slots()
	slots_x_max, slots_y_max, metaline_ls = lupy.add_metalines(width=width, height=height, period=period,
															   distance=distance,
															   layer_num=layer_num, group_num=group_num,
															   length_ls=length_ls,
															   )
	fdtd_y_min = 0
	fdtd_y_max = slots_y_max
	fdtd_x_min = 0 - distance - 1 * u
	# fdtd_x_max = slots_x_max+0.5*distance
	fdtd_x_max = min(10 * u, slots_x_max)
	# fdtd_x_max = 10 * u

	fdtd_z_min = -0.22 * u
	fdtd_z_max = height + 0.22 * u
	if source == "plane":
		lupy.add_simulation_fdtd(x_min=fdtd_x_min, x_max=fdtd_x_max,
								 y_min=fdtd_y_min, y_max=fdtd_y_max,
								 z_min=fdtd_z_min, z_max=fdtd_z_max,
								 x_min_bc="PML", x_max_bc="PML",
								 y_min_bc="periodic", y_max_bc="periodic",
								 z_min_bc="PML", z_max_bc="PML",
								 background_material="SiO2 (Glass) - Palik",
								 mesh_accuracy=mesh_accuracy)
	elif source == "dipole":
		lupy.add_simulation_fdtd(x_min=fdtd_x_min, x_max=fdtd_x_max,
								 y_min=fdtd_y_min, y_max=fdtd_y_max,
								 z_min=fdtd_z_min, z_max=fdtd_z_max,
								 x_min_bc="PML", x_max_bc="PML",
								 y_min_bc="PML", y_max_bc="PML",
								 z_min_bc="PML", z_max_bc="PML",
								 background_material="SiO2 (Glass) - Palik",
								 mesh_accuracy=mesh_accuracy)
	elif source == "gaussian":
		lupy.add_simulation_fdtd(x_min=fdtd_x_min, x_max=fdtd_x_max,
								 y_min=fdtd_y_min, y_max=fdtd_y_max,
								 z_min=fdtd_z_min, z_max=fdtd_z_max,
								 x_min_bc="PML", x_max_bc="PML",
								 y_min_bc="PML", y_max_bc="PML",
								 z_min_bc="PML", z_max_bc="PML",
								 background_material="SiO2 (Glass) - Palik",
								 mesh_accuracy=mesh_accuracy)
	else:
		print("请检查输入，光源类型仅允许「plane」、「dipole」、「gaussian」！")
	lupy.add_slab(x_min=fdtd_x_min, x_max=fdtd_x_max,
				  y_min=fdtd_y_min - 0.1 * u, y_max=fdtd_y_max + 0.1 * u,
				  z_min=0, z_max=height)
	# add_basic_monitors()
	y, y_span = lupy.tools.min_span(fdtd_y_min, fdtd_y_max)
	eff_direction = ""
	if source == "plane":
		y_min, y_max = lupy.tools.span_min(y, y_span * 10)
		z_min, z_max = lupy.tools.span_min(height / 2, height * 10)
		lupy.add_source_plane(x_min=source_x, x_max=source_x, y_min=y_min, y_max=y_max, z_min=z_min,
							  z_max=z_max)
		eff_direction = "Ey"  # 默认的电场偏振方向
	elif source == "dipole":
		lupy.add_source_dipole(x=source_x, y=y, z=height / 2)
		eff_direction = "Ez"  # 默认的电场偏振方向
	elif source == "gaussian":
		# y_min = (fdtd_y_min + fdtd_y_max) / 2 - gaussian_delta_y / 2
		# y_max = (fdtd_y_min + fdtd_y_max) / 2 + gaussian_delta_y / 2
		y_min = 1.5 * u - gaussian_delta_y / 2
		y_max = 1.5 * u + gaussian_delta_y / 2
		lupy.add_source_gaussian(x_min=source_x, y_min=y_min, y_max=y_max, z_min=0 + 0.1 * u, z_max=height - 0.1 * u,
								 injection_axis="x")
		eff_direction = "Ey"  # 默认的电场偏振方向
	else:
		print("请检查输入，光源类型仅允许「plane」和「dipole」！")
	# lupy.add_rect()		 # 例如调用lupy库
	# print(rect_ls)

	# input("输入回车保存并结束程序\n")
	if dipole_avoid == True:
		lupy.add_global_monitor(name="no_dipole", dipole_avoid=True, dipole_avoid_delta_x=dipole_avoid_delta_x)
	# lupy.add_global_monitor()
	add_eri_monitors()

	if GPU == True:
		lupy.simulation.GPU_on()  # 尝试使用GPU加速
	else:
		lupy.simulation.GPU_off()
	FD.save()
	if run_flag == True:  # 运行仿真并计算结果
		FD.run()
		# FD.close()
		# FD.message("请打开python终端输入回车以继续程序\n")
		# input("输入回车以继续程序\n")
		FD.save()

		mean_eff = 0
		eff_list = []
		for i in range(group_num - 1):
			eff = lupy.cal_eff_delta(f"eri0{i}", "x", eff_direction)
			eff_list.append(eff)
			mean_eff = mean_eff + eff
		# print(f"eri0{i}计算的有效折射率为：{eff:.3f}")
		mean_eff = mean_eff / (group_num - 1)
		lupy.u_print(f"L={length_ls[0]:},\t"
					 f"dis={distance:},\t"
					 f"src={source_x},\t"
					 f"neff={mean_eff:.3f}")
		# print(f"L={length_ls[0]:.2f}\t，neff={mean_eff:.3f}")

		return mean_eff, eff_list
	else:
		return 0, []


def eff_get_and_cal(group_num=5, eff_direction="Ey", length=1 * u, distance=3 * u, source_x=0):
	mean_eff = 0
	eff_list = []
	for i in range(group_num - 1):
		eff = lupy.cal_eff_reg(f"eri0{i}", "x", eff_direction)
		eff_list.append(eff)
		mean_eff = mean_eff + eff
	# print(f"eri0{i}计算的有效折射率为：{eff:.3f}")
	mean_eff = mean_eff / (group_num - 1)

	mean_eff_delta = 0
	eff_list_delta = []
	for i in range(group_num - 1):
		eff = lupy.cal_eff_delta(f"eri0{i}", "x", eff_direction)
		eff_list_delta.append(eff)
		mean_eff_delta = mean_eff_delta + eff
	# print(f"eri0{i}计算的有效折射率为：{eff:.3f}")
	mean_eff_delta = mean_eff_delta / (group_num - 1)
	lupy.u_print(f"L={length:},\t"
				 f"dis={distance:},\t"
				 # f"src={source_x},\t"
				 f"neff={mean_eff:.5f},\t"
				 f"neff_delta={mean_eff_delta:.5f}")
	return mean_eff, eff_list, mean_eff_delta, eff_list_delta


# def phase_to_length(phase_ls, n_eff, n_slab, wave_length=1.55e-6):
# 	import math
# 	phase_ls_negative = [x if x < 0 else x - 2 * math.pi for x in phase_ls]
# 	k_0 = 2 * 3.1415927 / wave_length
# 	length_ls = []
# 	for phi in phase_ls_negative:
# 		L = phi / k_0 / (n_eff - n_slab)
# 		length_ls.append(L)
# 	return length_ls
def phase_to_length(phase_ls, n_eff, n_slab, wave_length=1.55e-6):
	phase_ls = np.array(phase_ls)  # 确保输入是 NumPy 数组
	# 对每个元素做条件判断：若小于0则保留，否则减去2π
	phase_ls_negative = np.where(phase_ls < 0, phase_ls, phase_ls - 2 * np.pi)
	k_0 = 2 * np.pi / wave_length
	length_ls = phase_ls_negative / k_0 / (n_eff - n_slab)
	return length_ls


def phase_to_length_database(db_file: str, targets_file: str, k: int = 2):
	"""
	对每个目标相移 (phase)，在数据库中找距离最近的两条记录，
	用它们做线性插值，返回插值后的长度 (length)。

	Parameters
	----------
	db_file : str
		两列 CSV：第 1 列=相移 (phase)，第 2 列=长度 (length)
	targets_file : str
		单行或单列 CSV，包含若干目标相移
	k : int, optional
		为兼容旧接口保留，但必须等于 2；否则抛 ValueError

	Returns
	-------
	list[float]
		与目标相移一一对应的插值长度
	"""
	if k != 2:
		raise ValueError("线性插值版本要求 k 必须为 2")

	# ---------- 读取数据库 ----------
	db = np.loadtxt(db_file, delimiter=',')
	phases_db = db[:, 1]  # 相移列
	lengths_db = db[:, 0]  # 长度列

	# ---------- 读取并预处理目标相移 ----------
	targets = np.loadtxt(targets_file, delimiter=',').ravel()
	targets = np.where(targets > 0, targets - 2 * np.pi, targets)

	# ---------- 逐个目标做线性插值 ----------
	results = []
	for tgt in targets:
		# 取距离最近的两条记录
		idx = np.argsort(np.abs(phases_db - tgt))[:2]
		x1, x2 = phases_db[idx]
		y1, y2 = lengths_db[idx]

		# 若两点相移不同，按 y = m x + b 插值
		if x1 != x2:
			m = (y2 - y1) / (x2 - x1)  # 斜率
			b = y1 - m * x1  # 截距
			y_pred = m * tgt + b
		else:
			# 极端情况：两点重合，直接取平均长度
			y_pred = (y1 + y2) / 2.0

		results.append(y_pred)

	# print(results)  # 题目要求“以列表形式打印输出”
	results_np = np.array(results) * 1e-6
	return results_np
