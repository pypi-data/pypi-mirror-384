# import os
# import sys
# import lumerpy as lupy
from .fdtd_manager import get_fdtd_instance
import numpy as np
import matplotlib.pyplot as plt
import os

u = 1e-6


def plot_initialize(paper_font=False):
	"""避免GUI交互问题和中文不显示的问题"""
	import matplotlib
	matplotlib.use('TkAgg')  # 避免 GUI 交互问题
	# 设置支持中文的字体，并根据是否论文需要修改中文为宋体，英文为times new roman
	if paper_font is False:
		plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 黑体
	else:
		plt.rcParams['font.family'] = ['SimSun', 'Times New Roman']
	plt.rcParams['axes.unicode_minus'] = False  # 解决负号 "-" 显示为方块的问题


def select_E_component_by_range_from_dataset(
		Edatas, axis_name, component='Ey', min_val=None, max_val=None, fixed_axis_name=None, fixed_axis_value=None,
		plot_Ey_flag=False, Energyshow=True, selected_range=None, plot_energy_flag=False, save_path=None
):
	# 这里的Energyshow是为了是否计算能量分布，如果Energyshow为False，那么不会有能量分布的计算，也不会正确保存图像结果
	# 坐标轴与电场分量的名称到索引的映射
	axis_map = {'x': 0, 'y': 1, 'z': 2}
	comp_map = {'Ex': 0, 'Ey': 1, 'Ez': 2}

	# 参数检查：axis_name 与 component 必须在上面的映射中
	if axis_name not in axis_map:
		raise ValueError("axis_name 必须是 'x', 'y' 或 'z'")
	if component not in comp_map:
		raise ValueError("component 必须是 'Ex', 'Ey' 或 'Ez'")

	axis_idx = axis_map[axis_name]  # 要做区间筛选的“坐标轴”对应到 E_data 的哪个维度
	comp_idx = comp_map[component]  # 要选取的电场分量（最后一维的索引）

	coord_values = np.array(Edatas[axis_name])
	E_data = Edatas["E"]  # 完整的电场数据

	# 如果需要固定 z/x/y
	fixed_coord_value = None
	if fixed_axis_name and fixed_axis_value is not None:
		if fixed_axis_name not in axis_map:
			raise ValueError("fixed_axis_name 必须是 'x', 'y' 或 'z'")
		fixed_axis_idx = axis_map[fixed_axis_name]
		fixed_coord_array = np.array(Edatas[fixed_axis_name])
		# 找到与 fixed_axis_value 最接近的坐标点索引
		closest_index = np.argmin(np.abs(fixed_coord_array - fixed_axis_value))
		fixed_coord_value = fixed_coord_array[closest_index]

		# 构造切片列表 slicer，长度 = E_data.ndim（每个维度给一个索引器）
		# 先全部置为 slice(None) 表示“取该维的所有元素”
		slicer = [slice(None)] * E_data.ndim
		# 在固定的轴维度上仅保留 [closest_index : closest_index+1] 这一段（长度为1，维度不丢）
		slicer[fixed_axis_idx] = slice(closest_index, closest_index + 1)
		# 应用切片（tuple(...) 是 NumPy 索引约定）
		E_data = E_data[tuple(slicer)]
		# 若固定的轴刚好就是我们要做区间筛选的轴，那么相应 coord_values 也只剩下一个坐标点
		if fixed_axis_name == axis_name:
			coord_values = fixed_coord_array[closest_index:closest_index + 1]

	# 用于收集每个区间的结果（支持多区间）
	E_all, coord_all, energy_all = [], [], []

	# 多区域处理
	# 构造区间列表：
	# - 若提供了 selected_range（形如 [[min1,max1], [min2,max2]]），逐个区间处理；
	# - 否则退化为单一区间 [min_val, max_val]
	region_list = []
	if selected_range is not None:
		region_list = selected_range
	else:
		region_list = [[min_val, max_val]]

	# —— 逐区间进行筛选与取分量 ——
	for r in region_list:
		r_min, r_max = r
		# 1) 先用布尔掩码选出坐标落在 [r_min, r_max] 范围内的位置
		#    mask 的形状与 coord_values 相同（通常是一维），True 表示该索引落在区间内
		mask = (coord_values >= r_min) & (coord_values <= r_max)
		# 2) 把 True 的位置拿出来做索引数组（range_indices 是一维整型数组）
		range_indices = np.where(mask)[0]
		# 3) 取出这些位置对应的坐标值，作为该区间的坐标数组
		coord_selected = coord_values[range_indices]
		# 4) 构造对 E_data 的高维切片：
		#    - 我们要在“筛选轴”（axis_idx）上使用一个“整型索引数组”（range_indices）
		#    - 在“最后一维”（分量维）上使用“单个整型索引”（comp_idx）取出 Ex/Ey/Ez
		#
		# ★ 索引规则要点（NumPy）：
		#   a) 基本索引（basic indexing）：切片 slice(start, stop, step)、单个 int、... —— 这些不会触发“高级索引”规则；
		#   b) 高级索引（advanced indexing）：用“整型数组”或“布尔数组”当索引器会触发高级索引；
		#   c) 当混合使用基本索引与高级索引时：
		#      - 所有“高级索引的轴”会被提到结果的“前面”，其形状是各高级索引器广播后的形状；
		#      - 其余采用基本索引的轴，按原顺序跟在后面；
		#      - 若在某个维度上用的是“单个 int”（属于基本索引），该维会被移除（减少一个维度）。
		#
		#   在本例中：
		#     - 在 axis_idx 维，我们用的是 “整型索引数组 range_indices” → 这是高级索引；
		#     - 在最后一维（-1），我们用的是 “单个整型 comp_idx” → 这是基本索引，且会移除“分量维”；
		#     - 其它维度用 slice(None) → 基本索引，维度保留。
		#
		#   因为出现了高级索引（range_indices），返回结果的形状会把该高级轴（len(range_indices)）放到最前面，
		#   然后拼上其余保留下来的各轴（不含被 int 取走的最后一维）。
		# 选出电场分量
		slicer = [slice(None)] * E_data.ndim
		# 在“筛选轴”上放入“整型索引数组”（高级索引），只取区间内的那几层
		slicer[axis_idx] = range_indices
		# 在“最后一维”（分量维）上放入“单个整型”（基本索引），从而只取一个分量（该维度被移除）
		slicer[-1] = comp_idx

		# 实际取数：
		# E_selected 的形状规则（举例）：若 E_data 原形状是 (Nx, Ny, Nz, 3)
		# - 假设 axis_idx=0（即沿 x 轴筛选，range_indices 长度为 K）
		# - 则 E_selected 的形状通常为 (K, Ny, Nz) —— 注意 K 这个高级索引维会被“提到最前面”
		E_selected = E_data[tuple(slicer)]
		# 为了后续处理方便，去掉长度为 1 的维度（例如前面固定轴但保留了长度为1的维度）
		# 小提示：np.squeeze 只会移除 size=1 的轴，不会改变轴顺序；若想“固定轴也完全消失”，就靠这里的 squeeze。
		E_all.append(np.squeeze(E_selected))
		coord_all.append(coord_selected)

		# 可选的能量计算：对该区间的选中分量做 |E|^2 求和（对所有元素求和，跟轴顺序无关）
		if Energyshow:
			energy = np.sum(np.abs(E_selected) ** 2)
			energy_all.append(energy)

	# -------------------------
	# 🎨 统一纵坐标画图：电场分布
	# -------------------------
	if plot_Ey_flag:
		n = len(region_list)
		vmin = min([np.min(e) for e in E_all])
		vmax = max([np.max(e) for e in E_all])
		vmax = vmax * 1.1
		fig, axs = plt.subplots(1, n, figsize=(6 * n, 4))
		if n == 1:
			axs = [axs]
		for i in range(n):
			coord_um = coord_all[i] * 1e6
			ax = axs[i]
			e = E_all[i]
			if e.ndim == 1:
				ax.plot(coord_um, e)
				ax.set_ylim(vmin, vmax)
				ax.set_title(f"区域 {i} 的{component}")
				ax.set_xlabel(f"{axis_name} (μm)")
				ax.set_ylabel(component)
				ax.grid(True)
			elif e.ndim == 2:
				extent = [coord_um[0], coord_um[-1], 0, e.shape[1]]
				im = ax.imshow(e.T, aspect='auto', origin='lower', extent=extent, vmin=vmin, vmax=vmax)
				ax.set_title(f"区域 {i} 的 {component}")
				ax.set_xlabel(f"{axis_name} (μm)")
				ax.set_ylabel("Other axis index")
				plt.colorbar(im, ax=ax, label=component)
		plt.tight_layout()

	# -------------------------
	# 🎨 能量图 + 输出 + 能量标注
	# -------------------------
	if Energyshow:

		# ✅ 获取所有 Ey² 的全局最小/最大值
		all_Ey2 = [np.abs(e) ** 2 for e in E_all]
		ymin = min(np.min(e) for e in all_Ey2)
		ymax = max(np.max(e) for e in all_Ey2)
		ymax = ymax * 1.1

		fig, axs = plt.subplots(1, len(E_all), figsize=(6 * len(E_all), 4))
		if len(E_all) == 1:
			axs = [axs]

		for i, Ey2 in enumerate(all_Ey2):
			coord_um = coord_all[i] * 1e6
			energy = energy_all[i]
			ax = axs[i]

			if Ey2.ndim == 1:
				ax.plot(coord_um, Ey2)
				ax.set_ylim(ymin, ymax)  # ✅ 统一 y 轴范围
				ax.set_title(f"区域 {i} 的 |{component}|²")
				ax.set_xlabel(f"{axis_name} (μm)")
				ax.set_ylabel(f"|{component}|²")
				ax.grid(True)
				ax.text(0.98, 0.95, f"累计能量 = {energy:.2e}",
						transform=ax.transAxes,
						fontsize=10, color='red',
						horizontalalignment='right',
						verticalalignment='top')

			elif Ey2.ndim == 2:
				extent = [coord_um[0], coord_um[-1], 0, Ey2.shape[1]]
				im = ax.imshow(Ey2.T, aspect='auto', origin='lower', extent=extent,
							   vmin=ymin, vmax=ymax)  # ✅ 统一色标范围
				ax.set_title(f"区域 {i} 的 |{component}|²")
				ax.set_xlabel(f"{axis_name} (μm)")
				ax.set_ylabel("Other axis index")
				plt.colorbar(im, ax=ax, label=f"|{component}|²")
				ax.text(0.98, 0.95, f"累计能量 = {energy:.2e}",
						transform=ax.transAxes,
						fontsize=10, color='red',
						horizontalalignment='right',
						verticalalignment='top')

		plt.tight_layout()
		if plot_energy_flag:
			plt.show()
		if save_path:
			import os
			os.makedirs(save_path, exist_ok=True)
			import time
			current_time = time.strftime("%m%d-%H%M")
			fig.savefig(f"{save_path}{current_time}_{component}.png", dpi=300)
	# print(f"✅ 所有能量图已保存至 {save_path}_{component}.png")
	# for i, e in enumerate(energy_all):
	# 	print(f"区域 {i} 累计 {component}² 能量为: {e:.4e}")

	return E_all, coord_all, fixed_coord_value, energy_all if Energyshow else None


def get_simple_out(selected_range, power_name="local_outputs", z_fixed=0.11e-6,
				   plot_Ey_flag=False, Energyshow=True, plot_energy_flag=False,
				   axis_name='y', component='Ey', fixed_axis_name='z', save_path=False):
	FD = get_fdtd_instance()
	Edatas = FD.getresult(power_name, "E")

	E_list, coord_list, z_used, energy_list = select_E_component_by_range_from_dataset(
		Edatas, axis_name=axis_name, component=component, fixed_axis_name=fixed_axis_name,
		fixed_axis_value=z_fixed, selected_range=selected_range,
		plot_Ey_flag=plot_Ey_flag, Energyshow=Energyshow, plot_energy_flag=plot_energy_flag, save_path=save_path)

	# print(energy_list)
	idx = int(np.argmax(energy_list))

	return idx, energy_list


# def cal_result(power_name):
# 	FD = get_fdtd_instance()
# 	Edatas = FD.getresult(power_name, "E")
#
# 	select_E_component_by_range(E_data=Edatas,coord_values=)
#
#
# 	Ez_index = int(len(Edatas["E"][0, 0, :, 0, 0]) / 2)  # 选取中间的那个值
# 	Eys = Edatas["E"][0, :, Ez_index, 0, 1]
# 	# Edatas["E"].shape = (1, 338, 10, 1, 3) # 应该分别是：x,y,z,f,(Ex,Ey,Ez)
# 	# 我有一个高维度数据组Edatas["E"]，其中Edatas["E"].shape=(1, 338, 10, 1, 3)，分别对应
# 	# x，y，z，f，(Ex,Ey,Ez)
# 	# 我现在希望：
# 	# 选取所有x在我指定的范围（例如：index=[3,5]）中的Ey数据，如何做？

def get_simulation_results(size=(1, 50), channals_output=2, duty_cycle_output=0.5, margins_cycle=(0, 0, 0, 0),
						   power_name="local_outputs",
						   period=0.5e-6, width=0.2e-6, z_fixed=0.11e-6,
						   file_path=r"E:\0_Work_Documents\Simulation\lumerpy\03_cat",
						   file_name=r"m00_temp.fsp", save_path=False, plot_Ey_flag=True, plot_energy_flag=True,
						   save_flag=False, show_area_flag=True, effective_y_span_flag=False,
						   double_output_record_flag=False, effective_y_span=0):
	'''
	返回输出的区域编码和能量；
	此外，save_flag若为True，则将能量图保存到save_path
	'''
	# import sys
	# import os

	# # 用户在这里设置 API 和文件路径
	# api_path = r"C:/Program Files/Lumerical/v241/api/python"
	# sys.path.append(os.path.normpath(api_path))  # 添加 API 路径以确保可以成功导入 lumapi
	# import lumerpy as lupy
	# lupy.tools.check_path_and_file(file_path=file_path, file_name=file_name, auto_newfile=False)
	# # import lumapi		# lupy库中已经包含了lumapi的导入，不需要额外导入lumapi
	# lupy.setup_paths(api_path, file_path, file_name)  # 设置路径到库
	#
	# # --------------------基本设置结束--------------------
	# fdtd_instance = lupy.get_fdtd_instance(hide=True, solution_type="FDTD")  # 创建fdtd实例，这应该是第一个实例，hide=True时，隐藏窗口
	# # lupy.version()  # 测试一下是否成功
	# FD = lupy.get_existing_fdtd_instance()  # 返回创建的实例，以便使用lumapi
	import lumerpy as lupy
	FD = lupy.initialize(file_path=file_path, file_name=file_name)
	# FD = lupy.get_existing_fdtd_instance()  # 旧的写法，关于实例继承的问题我没搞清楚，凑合着用吧
	if not FD:
		print("未正确创建实例，请检查")
	u = 1e-6

	# --------------------现在既可以调用lumapi，也可以调用lupy库--------------------
	# import numpy as np

	lupy.plot_initialize()
	# Edatas = FD.getresult(power_name, "E")
	out_y_pixel_center_ls, out_y_pixel_start_ls, out_y_pixel_span, _ = lupy.tools.get_single_inputs_center_x(
		channels=channals_output,
		data_single_scale=size,
		duty_cycle=duty_cycle_output,
		margins_cycle=margins_cycle)
	if effective_y_span_flag:
		# fdtd_y_span = FD.getnamed("effective_y_span", "y min")  # 通过仿真对象直接传递/px，先这样吧
		fdtd_y_span = effective_y_span
	else:
		fdtd_y_span = FD.getnamed("FDTD", "y span")  # 这里要改一下，不应该通过FDTD的区域范围获取有效宽度，这部分工作挺麻烦的

	scale_ratio = (fdtd_y_span / size[1])
	# extra_gap_y = (period - width) / 2  # 额外抬高半个槽和槽之间的间距
	# extra_gap_y = extra_gap_y + width  # 场发射位置本来就在槽和槽中间，这两行代码下来，这个额外抬高的y值就对应着槽和槽中间的硅板的y方向中心
	extra_gap_y = 0  # 新的设计思路转变为，不在输入和输出处讨论应当抬高多少位置，转变为在设置metaline的时候抬高多少位置
	out_y_metric_center_ls = []
	starts_ls = []
	out_y_metric_start_ls = []
	out_y_metric_total = np.zeros((channals_output, 2))
	out_y_span = out_y_pixel_span * scale_ratio
	for i in range(channals_output):  # 对每个输入/出通道操作
		# out_y_metric_center_ls.append(out_y_pixel_center_ls[i] * scale_ratio + extra_gap_y)		# 这里应该有点问题，涉及到extra_gap_y，先不管他
		out_y_metric_start_ls.append(out_y_pixel_start_ls[i] * scale_ratio + extra_gap_y)
		out_y_metric_total[i, :] = out_y_metric_start_ls[i], out_y_metric_start_ls[i] + out_y_span
	# print(f"输出位置[{i}]：{out_y_metric_start_ls[i]},{out_y_metric_start_ls[i] + out_y_span}")
	# print(out_y_metric_total)
	# 选择好输出范围即可
	# selected_ranges = np.array([
	# 	[0e-6, 6e-6],
	# 	[12e-6, 18e-6]
	# ])

	if save_flag:
		output_area_code, energy_list = lupy.get_simple_out(selected_range=out_y_metric_total, power_name=power_name,
															z_fixed=z_fixed, plot_Ey_flag=plot_Ey_flag,
															plot_energy_flag=plot_energy_flag, save_path=save_path)
	else:
		output_area_code, energy_list = lupy.get_simple_out(selected_range=out_y_metric_total, power_name=power_name,
															z_fixed=z_fixed, plot_Ey_flag=plot_Ey_flag,
															plot_energy_flag=plot_energy_flag,
															save_path=False)  # 我知道这里逻辑很古怪，先这样吧
	output_energy_ls = [round(float(x), 4) for x in energy_list]
	# print(f"输出区域是：{output_area_code}，并且各输出值为：{output_energy_ls}")
	if show_area_flag:
		for i in range(channals_output):
			area_start, area_end = out_y_metric_total[i, :]
			print(f"区域 {i} 范围：{area_start * 1e6:.2f},\t{area_end * 1e6:.2f}")
		# print(f"可能输出区域为：{out_y_metric_total}")
		print(f"输出区域是：区域 {output_area_code}，并且各区域输出值为：{output_energy_ls}")

	# 多存一次关于之前的输出区域的记录
	if double_output_record_flag:
		extra_gap_y = (period - width) / 2  # 额外抬高半个槽和槽之间的间距
		extra_gap_y = extra_gap_y + width  # 场发射位置本来就在槽和槽中间，这两行代码下来，这个额外抬高的y值就对应着槽和槽中间的硅板的y方向中心
		# extra_gap_y = 0  # 新的设计思路转变为，不在输入和输出处讨论应当抬高多少位置，转变为在设置metaline的时候抬高多少位置
		out_y_metric_center_ls_2 = []
		starts_ls = []
		out_y_metric_start_ls_2 = []
		out_y_metric_total_2 = np.zeros((channals_output, 2))
		out_y_span = out_y_pixel_span * scale_ratio
		for i in range(channals_output):  # 对每个输入/出通道操作
			# out_y_metric_center_ls.append(out_y_pixel_center_ls[i] * scale_ratio + extra_gap_y)		# 这里应该有点问题，涉及到extra_gap_y，先不管他
			out_y_metric_start_ls_2.append(out_y_pixel_start_ls[i] * scale_ratio + extra_gap_y)
			out_y_metric_total_2[i, :] = out_y_metric_start_ls_2[i], out_y_metric_start_ls_2[i] + out_y_span
		# print(f"输出位置[{i}]：{out_y_metric_start_ls[i]},{out_y_metric_start_ls[i] + out_y_span}")
		# print(out_y_metric_total)
		# 选择好输出范围即可
		# selected_ranges = np.array([
		# 	[0e-6, 6e-6],
		# 	[12e-6, 18e-6]
		# ])
		# save_path=os.path.join(save_path,"record-2")
		if save_flag:
			output_area_code_2, energy_list_2 = lupy.get_simple_out(selected_range=out_y_metric_total_2,
																	power_name=power_name,
																	z_fixed=z_fixed, plot_Ey_flag=plot_Ey_flag,
																	plot_energy_flag=plot_energy_flag,
																	save_path=save_path)
		else:
			output_area_code_2, energy_list_2 = lupy.get_simple_out(selected_range=out_y_metric_total_2,
																	power_name=power_name,
																	z_fixed=z_fixed, plot_Ey_flag=plot_Ey_flag,
																	plot_energy_flag=plot_energy_flag,
																	save_path=False)  # 我知道这里逻辑很古怪，先这样吧
		output_energy_ls_2 = [round(float(x), 4) for x in energy_list_2]
		return output_area_code, output_energy_ls, output_area_code_2, output_energy_ls_2
	else:
		return output_area_code, output_energy_ls


def read_unique_csv(path, delimiter=",", dtype=float, has_header=True):
	"""
	用 np.loadtxt 读取 CSV 文件并返回唯一记录数和唯一记录

	参数:
		path: str, CSV 文件路径
		delimiter: str, 分隔符，默认逗号 ","
		dtype: 数据类型，默认 float

	返回:
		unique_count: int, 不重复记录数
		unique_records: ndarray, shape=(n_unique, n_cols)
	"""
	# txt = "\n\t本函数已弃用，请调用difrannpy库里datas.py的同名函数。\n\t如果必然需要本函数，请手动进入源代码，删去注释使用"
	# raise NotImplementedError(txt)
	# 读取整个 CSV 文件
	if has_header:
		data = np.loadtxt(path, delimiter=delimiter, dtype=dtype, skiprows=1)
	else:
		data = np.loadtxt(path, delimiter=delimiter, dtype=dtype)

	# 找到唯一行
	unique_records, idx = np.unique(data, axis=0, return_index=True)
	unique_records = unique_records[np.argsort(idx)]  # 保持原本的顺序
	unique_count = unique_records.shape[0]
	return unique_count, unique_records


def save_csv_results(save_path, save_name, int_to_record, list_to_append="", save_index=-1):
	'''以每行记录形如：【0,0.1,0.2】的形式保存仿真结果为csv格式'''
	if save_index == -1:
		file_csv_path = os.path.join(save_path, save_name.removesuffix(".fsp")) + ".csv"
	else:
		file_csv_path = os.path.join(save_path, save_name.removesuffix(".fsp")) + "-" + str(save_index) + ".csv"
	save_temp = [int_to_record] + list(list_to_append)
	os.makedirs(os.path.dirname(file_csv_path), exist_ok=True)
	with open(file_csv_path, "a+") as fp:
		np.savetxt(fp, [save_temp], delimiter=",")
	# print(f"csv文件已保存至：{file_csv_path}")
	return file_csv_path


def get_channels_in_out(path_data, path_pd, show_flag=False, return_data_decode_flag=False, each_pix=3):
	data_count, data_raw = read_unique_csv(path_data)

	data_y = data_raw[:, 0]
	data_X = data_raw[:, 1:]

	data_X_decode = np.apply_along_axis(recover_original, axis=1, arr=data_X, repeat=each_pix)
	# print(f"展示前16条经过译码的输入数据为：\n{data_X_decode[0:16]}")
	pd_count, pd_raw = read_unique_csv(path_pd)

	pd_overview = pd_raw[0]
	pd_pds = pd_raw[1:]
	pd_decode = np.apply_along_axis(recover_original, axis=1, arr=pd_pds, repeat=each_pix)

	channels_in = len(data_X_decode[0])
	channels_out = len(pd_decode)
	if show_flag:
		print(f"不重复训练数据共有：{data_count}条")
		print(f"展示第0条输入数据为：\n{data_X[0]},展示前16条输出数据为：\n{data_y[0:16]}")
		print(f"不重复pd数据共有：{pd_count}条")
		print(f"展示前8条经过译码的输出pd为：\n{pd_decode[0:8]}")
	if not return_data_decode_flag:
		return channels_in, channels_out
	else:
		return channels_in, channels_out, data_X_decode


def recover_original(arr, repeat=3, remove_interleaved_zeros=True, eps=0.0):
	"""
	从扩展数组恢复原始数组（非零即 1 的逻辑）

	参数:
		arr: 一维数组或可迭代对象
		repeat: 每个元素重复次数（默认 3）
		remove_interleaved_zeros: 是否在还原后再隔一个取一个（用于旧流程里“中间插 0”的情况）
		eps: 判断“非零”的阈值；> eps 视为非零，默认 0（严格非零）

	返回:
		numpy 一维整型数组（0/1）
	"""
	arr = np.asarray(arr, dtype=float)

	if arr.size % repeat != 0:
		raise ValueError("数组长度不能被 repeat 整除")

	# 将数组按 repeat 分块
	blocks = arr.reshape(-1, repeat)

	# 只要一组里出现非零（> eps），该组就记为 1；否则 0
	reduced = (np.any(blocks > eps, axis=1)).astype(int)

	# 若旧数据流里有“中间插 0”，可开启该步
	if remove_interleaved_zeros:
		reduced = reduced[::2]
	# def recover_original(arr, repeat=3):
	# 	"""
	# 	从扩展数组恢复原始数组
	#
	# 	参数:
	# 		arr: numpy 一维数组 (扩展结果)
	# 		repeat: 每个元素重复次数 (默认 3)
	#
	# 	返回:
	# 		原始数组 (numpy 一维数组)
	# 	"""
	# 	arr = np.asarray(arr)
	#
	# 	# 第一步：解开重复
	# 	if arr.size % repeat != 0:
	# 		raise ValueError("数组长度不能被 repeat 整除")
	# 	reduced = arr.reshape(-1, repeat)[:, 0]  # 取每组的第一个
	#
	# 	# 第二步：去掉中间插的 0（取偶数位置）
	# 	original = reduced[::2]
	#
	# 	return original.astype(int)
	return reduced


def get_data_single_scale(channels_in, each_pix=3, data_single_scale_row=1, duty_cycle=0.5):
	data_single_scale_col = channels_in / duty_cycle * each_pix  # 默认占空比为50%，所以搞出2倍
	# 这里还有一个事必须提一下，如果bit_expand_flag=True，那么由于扩展组合编码的关系，实际的col数会是2倍
	data_single_scale = (data_single_scale_row, data_single_scale_col)
	# 下面这个位扩展标志位相关代码已弃用，改成在调用函数的外面直接翻倍输入通道
	# if bit_expand_flag:  # 如果采用扩展组合编码
	# 	# 这里插一句，这里有点屎山的感觉了，因为data_single_scale这个元组需要给generate_data_total()函数
	# 	# 但是如果使用扩展组合编码的话，实际上的data_single_scale会变为两倍，所以搞出了一个data_single_scale_temp变量去存这个结果
	# 	# 但是实际上后面的程序，哪哪都要这个data_singel_scale_temp，包括后面提到的size也是
	# 	# 也就是说，变量size才是真正的“数据尺寸”
	# 	data_single_scale_temp = (data_single_scale[0], data_single_scale[1] * 2)
	# else:
	# 	data_single_scale_temp = data_single_scale
	return data_single_scale


def get_E_datas_and_draw(
		FDTD_instance=None, monitor_name="local_outputs", attr="E",
		x_min=None, x_max=None,
		y_min=None, y_max=None,
		z_min=None, z_max=None, aspect="physical", frequency=0,
		dim="total", value="abs", title="光强",
		plot_flag=False, save_path=None):
	from typing import Tuple, Optional, Union, Mapping, Any
	import numpy as np
	import warnings
	import matplotlib.pyplot as plt

	Number = Union[int, float, np.number]

	# ---------------------------
	# 辅助工具函数（内部使用）
	# ---------------------------

	def _as_1d_vector(a: np.ndarray, name: str) -> np.ndarray:
		"""
		将 (N,), (N,1) 或 (1,N) 形式的一维向量标准化为 shape=(N,)。
		若是其他二维形状，报错（本实现不支持真正的2D网格坐标）。
		"""
		arr = np.asarray(a)
		if arr.ndim == 1:
			return arr
		if arr.ndim == 2:
			if 1 in arr.shape:
				return arr.reshape(-1)
			raise ValueError(f"{name} 必须是一维坐标（形如 (N,), (N,1) 或 (1,N)），当前形状为 {arr.shape}。")
		raise ValueError(f"{name} 维度必须为1或2，当前为 {arr.ndim}。")

	def _check_monotonic(arr: np.ndarray, name: str) -> str:
		"""
		检查坐标是否单调（允许非严格单调），返回 'increasing' 或 'decreasing'。
		若不单调，抛出异常。
		"""
		arr = np.asarray(arr)
		if arr.size <= 1:
			return 'increasing'
		dif = np.diff(arr)
		# 允许极小数值噪声
		tol = (np.abs(arr).max() + 1.0) * 1e-15
		if np.all(dif >= -tol):
			return 'increasing'
		if np.all(dif <= tol):
			return 'decreasing'
		raise ValueError(f"{name} 不是单调坐标（既非单调增也非单调减）。")

	def _resolve_none_bounds(arr: np.ndarray, minv: Optional[Number], maxv: Optional[Number]) -> Tuple[Number, Number]:
		"""
		将 None 边界替换为该轴的全范围（使用实际最小/最大值）。
		"""
		if minv is None:
			minv = arr.min()
		if maxv is None:
			maxv = arr.max()
		return minv, maxv

	def _nearly_equal(a: Number, b: Number, rtol: float = 1e-9, atol: float = 0.0) -> bool:
		return np.isclose(a, b, rtol=rtol, atol=atol)

	def _range_indices_monotonic(arr: np.ndarray, minv: Number, maxv: Number) -> Tuple[int, int]:
		"""
		在单调（增或减）的一维数组 arr 中，找到满足 minv <= arr[i] <= maxv 的闭区间索引 [i_start, i_end]。
		支持单调增/单调减，若无交集则抛出 ValueError。
		逻辑等价于“插空比较”：min 用“第一个满足阈值的样本”，max 用“最后一个不超过阈值的样本”，超出范围时钳制到边界。
		"""
		if minv > maxv:
			raise ValueError(f"输入范围无效：min ({minv}) > max ({maxv})。")
		arr = np.asarray(arr)
		if arr.size == 1:
			if minv <= arr[0] <= maxv:
				return 0, 0
			else:
				raise ValueError(f"所给范围 [{minv}, {maxv}] 与坐标只有的单点 {arr[0]} 无交集。")

		order = _check_monotonic(arr, "坐标")
		# 用布尔掩码在任意单调方向上选出区间
		mask = (arr >= minv) & (arr <= maxv)
		idx = np.where(mask)[0]
		if idx.size == 0:
			# 在边界外时：实现“钳制到可用端”
			if order == 'increasing':
				if maxv < arr[0]:
					# 全部在左边界之外
					raise ValueError(f"范围 [{minv}, {maxv}] 小于该轴最小值 {arr[0]}，无可选样本。")
				if minv > arr[-1]:
					raise ValueError(f"范围 [{minv}, {maxv}] 大于该轴最大值 {arr[-1]}，无可选样本。")
			else:  # decreasing
				if maxv > arr[0]:
					raise ValueError(f"范围 [{minv}, {maxv}] 大于该轴最大值(首元素) {arr[0]}，无可选样本。")
				if minv < arr[-1]:
					raise ValueError(f"范围 [{minv}, {maxv}] 小于该轴最小值(末元素) {arr[-1]}，无可选样本。")
			# 理论上走不到这里，因为上述已覆盖无交集情况
			raise ValueError("未找到任何索引。")

		# 连续性：单调坐标下应为连续区间
		return int(idx[0]), int(idx[-1])

	def _ensure_len_matches_axis(coord: np.ndarray, axis_len: int, axis_name: str):
		"""
		确保坐标长度与 E 的该轴长度相容：允许 1 或 axis_len，否则报错。
		"""
		if coord.size not in (1, axis_len):
			raise ValueError(f"{axis_name} 坐标长度为 {coord.size}，但 E 的该轴长度为 {axis_len}（仅允许 1 或完全一致）。")

	def _choose_dim_index(dim: Union[str, int]) -> int:
		"""
		将 dim: 'x'|'y'|'z' 或 0|1|2 映射到分量索引 0/1/2。
		"""
		if isinstance(dim, str):
			dim = dim.lower()
			mapping = {'x': 0, 'y': 1, 'z': 2}
			if dim not in mapping:
				raise ValueError("dim 只能是 'x'/'y'/'z' 或 0/1/2。")
			return mapping[dim]
		elif isinstance(dim, (int, np.integer)):
			if dim not in (0, 1, 2):
				raise ValueError("dim 只能是 'x'/'y'/'z' 或 0/1/2。")
			return int(dim)
		else:
			raise ValueError("dim 类型无效。")

	def _apply_value_mode(data: np.ndarray, mode: str) -> np.ndarray:
		"""
		将复数场按指定模式转换为实数：'abs'|'abs2'|'real'|'imag'|'phase'
		"""
		mode = str(mode).lower()
		if mode == 'abs':
			return np.abs(data)
		if mode == 'abs2':
			return np.abs(data) ** 2
		if mode == 'real':
			return np.real(data)
		if mode == 'imag':
			return np.imag(data)
		if mode == 'phase':
			return np.angle(data)
		raise ValueError("value 必须是 'abs'|'abs2'|'real'|'imag'|'phase' 之一。")

	# --------------------------------
	# 1) get_metric_idx
	# --------------------------------

	def get_metric_idx(
			Edatas: Mapping[str, Any],
			x_min: Optional[Number],
			x_max: Optional[Number],
			y_min: Optional[Number],
			y_max: Optional[Number],
			z_min: Optional[Number],
			z_max: Optional[Number],
	) -> Tuple[int, int, int, int, int, int, np.ndarray, np.ndarray, np.ndarray]:
		"""
		根据用户给定的空间范围，返回 xyz 三轴对应的闭区间索引，以及对应的坐标选取向量。

		规则与细节（与你确认的一致）：
		- 闭区间索引：返回的 *_idx_end 是包含端点的索引；切片时请用 [: end+1]。
		- None 表示该轴全范围。
		- 当某轴只有一个样本（比如 Nx==1），要求该轴的 min==max（或两者皆为 None）。
		- 坐标必须为一维向量（(N,), (N,1) 或 (1,N)），且单调（增或减）。
		- 索引选择采用“插空比较”：min 取第一个满足阈值的样本，max 取最后一个不超过阈值的样本；
		  超出范围则钳制到可用端，若完全无交集则报错。
		- 返回 x_select/y_select/z_select 为一维数组（闭区间，含端点）。

		返回：
			x_idx_start, x_idx_end, y_idx_start, y_idx_end, z_idx_start, z_idx_end,
			x_select, y_select, z_select
		"""
		E = np.asarray(Edatas["E"])
		Nx, Ny, Nz = E.shape[:3]

		x_arr = _as_1d_vector(np.asarray(Edatas["x"]), "x")
		y_arr = _as_1d_vector(np.asarray(Edatas["y"]), "y")
		z_arr = _as_1d_vector(np.asarray(Edatas["z"]), "z")

		_ensure_len_matches_axis(x_arr, Nx, "x")
		_ensure_len_matches_axis(y_arr, Ny, "y")
		_ensure_len_matches_axis(z_arr, Nz, "z")

		# 只允许坐标长度为 1 或等于该轴长度；若为 1 但轴长度>1，直接视为常量坐标重复。
		# —— 但选择区间时，仅允许 Nx==1 时 min==max（或 None）
		def _one_axis(coord: np.ndarray, Naxis: int, amin: Optional[Number], amax: Optional[Number], axis_name: str):
			coord = coord if coord.size > 1 else np.array([coord.item()])
			if Naxis == 1:
				# 该轴仅有一个记录
				if (amin is not None) and (amax is not None) and (not _nearly_equal(amin, amax)):
					raise ValueError(f"{axis_name} 轴只有一个样本，但给定的最小/最大值不相等：{amin} vs {amax}。")
				# None 或相等 -> 自动钳制为该唯一样本
				amin, amax = coord[0], coord[0]
				idx0 = 0
				return idx0, idx0, coord.copy()
			else:
				# 多样本的轴
				amin, amax = _resolve_none_bounds(coord, amin, amax)
				i0, i1 = _range_indices_monotonic(coord, amin, amax)
				return i0, i1, coord[i0:i1 + 1]

		x0, x1, x_sel = _one_axis(x_arr, Nx, x_min, x_max, "x")
		y0, y1, y_sel = _one_axis(y_arr, Ny, y_min, y_max, "y")
		z0, z1, z_sel = _one_axis(z_arr, Nz, z_min, z_max, "z")

		return x0, x1, y0, y1, z0, z1, x_sel, y_sel, z_sel

	# --------------------------------
	# 2) get_select_E
	# --------------------------------

	def get_select_E(
			Edatas: Mapping[str, Any],
			x_idx_start: int,
			x_idx_end: int,
			y_idx_start: int,
			y_idx_end: int,
			z_idx_start: int,
			z_idx_end: int,
			frequency: Union[int, float] = 0,
	) -> np.ndarray:
		"""
		用闭区间索引和频点选择，裁剪出指定空间范围的三维电场数据块。

		- 输入索引为闭区间（与你确认一致），函数内部会转成切片 end+1。
		- 返回 E_select 的形状为 (x_count, y_count, z_count, 3)。
		- 频点 frequency 同时支持：
			* 索引（int，0-based，可为负索引）
			* 实际频率值（float）：会在 Edatas['f'] 中找最近的频点，若相对误差 > 10% 则报错。
			  相对误差定义：abs(f_sel - freq) / abs(freq)，其中 freq=0 的特殊情况：仅当 f_sel 也为 0 时通过。
		"""
		E = np.asarray(Edatas["E"])
		Nx, Ny, Nz, Nf, Ncomp = E.shape
		if Ncomp != 3:
			raise ValueError(f"E 的最后一维应为 3（Ex,Ey,Ez），当前为 {Ncomp}。")

		# 切片边界检查
		def _check_bounds(a0, a1, N, axisname):
			if not (0 <= a0 < N) or not (0 <= a1 < N) or a0 > a1:
				raise IndexError(f"{axisname} 索引闭区间无效：[{a0}, {a1}]（轴长度 {N}）。")

		_check_bounds(x_idx_start, x_idx_end, Nx, "x")
		_check_bounds(y_idx_start, y_idx_end, Ny, "y")
		_check_bounds(z_idx_start, z_idx_end, Nz, "z")

		# 频点解析
		f_arr = _as_1d_vector(np.asarray(Edatas["f"]), "f")
		if isinstance(frequency, (int, np.integer)):
			f_idx = int(frequency)
			if not (-Nf <= f_idx < Nf):
				raise IndexError(f"频点索引越界：{f_idx}，可用范围 [0, {Nf - 1}]（支持负索引）。")
			f_idx = f_idx % Nf
		else:
			# 频率值
			freq_val = float(frequency)
			if f_arr.size == 0:
				raise ValueError("Edatas['f'] 为空，无法按频率值选择。")
			# 找最近频点
			dif = np.abs(f_arr - freq_val)
			f_idx = int(np.argmin(dif))
			f_sel = float(f_arr[f_idx])
			if freq_val == 0.0:
				if f_sel != 0.0:
					raise ValueError(f"请求频率为 0，但数据最近频点为 {f_sel}，相对误差不可定义，拒绝。")
			else:
				rel_err = abs(f_sel - freq_val) / abs(freq_val)
				if rel_err > 0.10:
					raise ValueError(f"所请求频率 {freq_val} 与最近频点 {f_sel} 的相对误差 {rel_err:.3f} 超过 10%。")

		E_sub = E[
				x_idx_start: x_idx_end + 1,
				y_idx_start: y_idx_end + 1,
				z_idx_start: z_idx_end + 1,
				f_idx,
				:
				]  # shape: (nx, ny, nz, 3)
		return E_sub

	def plot_E_2D(
			E_select: np.ndarray,
			x_select: Optional[np.ndarray] = None,
			y_select: Optional[np.ndarray] = None,
			z_select: Optional[np.ndarray] = None,
			dim: Optional[Union[str, int]] = None,  # 新：默认 None => 总体场强
			value: str = "abs2",  # 默认画强度
			title: Optional[str] = None,
			aspect: Union[str, float] = "auto",  # 支持 "physical"
	) -> Tuple[plt.Figure, plt.Axes, Any]:
		"""
		绘制二维（或退化到一维）的电场图像。

		参数
		----
		E_select : (nx, ny, nz, 3) 复数或实数数组
		x_select, y_select, z_select : 对应各维的一维坐标（长度需与 nx/ny/nz 匹配；None 则用索引）
		dim :
			- None 或 'total'：总体场强
			- 'x'/'y'/'z' 或 0/1/2：对应单个分量
		value :
			- 总体场强时：仅支持 'abs'（|E|）或 'abs2'（|E|^2）
			- 单分量时：'abs'|'abs2'|'real'|'imag'|'phase'
		aspect :
			- "auto"（默认）、"equal" 或 "physical"（按照真实坐标跨度设纵横比）
			- 也可传入数值，代表 y/x 的比例

		返回
		----
		fig, ax, handle
		"""
		E_select = np.asarray(E_select)
		if E_select.ndim != 4 or E_select.shape[-1] != 3:
			raise ValueError(f"E_select 形状应为 (nx, ny, nz, 3)，当前为 {E_select.shape}。")

		nx, ny, nz, _ = E_select.shape

		# --- 计算要绘制的标量场 E3v: (nx, ny, nz) ---
		total_mode = (dim is None) or (isinstance(dim, str) and str(dim).lower() == "total")
		# if total_mode:
		#     # 总体场强：|E| 或 |E|^2
		#     v = value.lower()
		#     if v not in ("abs", "abs2"):
		#         raise ValueError("总体场强模式下，value 仅支持 'abs' 或 'abs2'。")
		#     pow2 = np.sum(np.abs(E_select) ** 2, axis=-1)  # (nx, ny, nz)
		#     E3v = np.sqrt(pow2) if v == "abs" else pow2
		if total_mode:
			# 总体场强：|E| 或 |E|^2
			if value is None:  # 新增：默认行为
				v = "abs"
			else:
				v = value.lower()

			if v not in ("abs", "abs2"):
				raise ValueError("总体场强模式下，value 仅支持 'abs' 或 'abs2'。")

			pow2 = np.sum(np.abs(E_select) ** 2, axis=-1)  # (nx, ny, nz)
			E3v = np.sqrt(pow2) if v == "abs" else pow2
		else:
			dim_idx = _choose_dim_index(dim)
			E3 = E_select[..., dim_idx]  # (nx, ny, nz)
			E3v = _apply_value_mode(E3, value)
		# 记录分量名供标签使用
		# ---------------------------------------------

		# --- 坐标向量准备 ---
		xv = np.arange(nx) if x_select is None else np.asarray(x_select).reshape(-1)
		yv = np.arange(ny) if y_select is None else np.asarray(y_select).reshape(-1)
		zv = np.arange(nz) if z_select is None else np.asarray(z_select).reshape(-1)
		if xv.size != nx or yv.size != ny or zv.size != nz:
			raise ValueError(f"x/y/z_select 的长度必须分别匹配 (nx, ny, nz)=({nx},{ny},{nz})。")

		dims_gt1 = [ax for ax, n in zip(('x', 'y', 'z'), (nx, ny, nz)) if n > 1]

		fig, ax = plt.subplots()

		if len(dims_gt1) == 3:
			warnings.warn("检测到三轴均大于 1（体数据）。本函数仅绘制 2D/1D，请先在上游裁剪为二维切片。", RuntimeWarning)
			raise ValueError("三轴均大于 1，拒绝绘制。")

		# --- 二维绘图 ---
		if len(dims_gt1) == 2:
			# 三种唯一合法组合：
			if nz == 1 and nx > 1 and ny > 1:  # 横 x, 纵 y
				horiz_name, vert_name = 'x', 'y'
				H, V = xv, yv
				E2D = np.transpose(E3v[:, :, 0])  # (ny, nx) = (rows, cols)
			elif ny == 1 and nx > 1 and nz > 1:  # 横 x, 纵 z
				horiz_name, vert_name = 'x', 'z'
				H, V = xv, zv
				E2D = np.transpose(E3v[:, 0, :])  # (nz, nx)
			elif nx == 1 and ny > 1 and nz > 1:  # 横 y, 纵 z
				horiz_name, vert_name = 'y', 'z'
				H, V = yv, zv
				E2D = np.transpose(E3v[0, :, :])  # (nz, ny)
			else:
				raise RuntimeError("二维组合推断失败，请检查输入维度。")

			HH, VV = np.meshgrid(H, V)

			# 绘图关键代码
			m = ax.pcolormesh(HH, VV, E2D, shading='auto', cmap="jet")

			# 颜色条标签
			if total_mode:
				cb_label = "|E|" if value.lower() == "abs" else "|E|^2"
			else:
				comp = "xyz"[_choose_dim_index(dim)]
				if value.lower() == "abs":
					cb_label = f"|E_{comp}|"
				elif value.lower() == "abs2":
					cb_label = f"|E_{comp}|^2"
				elif value.lower() == "real":
					cb_label = f"Re(E_{comp})"
				elif value.lower() == "imag":
					cb_label = f"Im(E_{comp})"
				else:
					cb_label = f"phase(E_{comp})"
			# cbar = plt.colorbar(m, ax=ax)
			# cbar.set_label(cb_label)

			ax.set_xlabel(horiz_name)
			ax.set_ylabel(vert_name)
			if title:
				ax.set_title(title)

			# —— 纵横比（支持 "physical"）——
			if isinstance(aspect, (int, float)):
				ax.set_aspect(float(aspect), adjustable='box')
			elif isinstance(aspect, str):
				a = aspect.lower()
				if a == "equal":
					ax.set_aspect('equal', adjustable='box')
				elif a == "physical":
					xspan = float(np.max(H) - np.min(H))
					yspan = float(np.max(V) - np.min(V))
					if xspan > 0 and yspan > 0:
						ax.set_aspect(yspan / xspan, adjustable='box')
			# else: "auto" -> 默认

			# --------- 保留 imshow 实现（仅注释） ----------
			# extent = [H.min(), H.max(), V.min(), V.max()]
			# m2 = ax.imshow(E2D, extent=extent, origin='lower', aspect='auto')
			# if isinstance(aspect, str) and aspect.lower() == "equal":
			#     ax.set_aspect('equal', adjustable='box')
			# elif isinstance(aspect, str) and aspect.lower() == "physical":
			#     xspan = extent[1] - extent[0]
			#     yspan = extent[3] - extent[2]
			#     if xspan > 0 and yspan > 0:
			#         ax.set_aspect(yspan / xspan, adjustable='box')
			# ------------------------------------------------

			return fig, ax, m

		# --- 1D 退化 ---
		if len(dims_gt1) == 1:
			warnings.warn("当前切片退化为 1D，将绘制曲线图。", RuntimeWarning)
			if nx > 1 and ny == 1 and nz == 1:
				ax.plot(xv, E3v[:, 0, 0], lw=1.5)
				ax.set_xlabel('x')
			elif ny > 1 and nx == 1 and nz == 1:
				ax.plot(yv, E3v[0, :, 0], lw=1.5)
				ax.set_xlabel('y')
			elif nz > 1 and nx == 1 and ny == 1:
				ax.plot(zv, E3v[0, 0, :], lw=1.5)
				ax.set_xlabel('z')
			else:
				data_1d = E3v.reshape(-1)
				ax.plot(np.arange(data_1d.size), data_1d, lw=1.5)
				ax.set_xlabel('index')

			ylabel = "|E|" if (total_mode and value.lower() == "abs") else ("|E|^2" if total_mode else f"E ({value})")
			ax.set_ylabel(ylabel)
			if title:
				ax.set_title(title)
			ax.grid(True, alpha=0.3)
			return fig, ax, ax.lines[-1]

		# --- 单点 ---
		warnings.warn("检测到单点数据（3轴长度都为1），无法绘制有意义的 2D/1D 图。", RuntimeWarning)
		ax.plot([0], [0], 'o')
		ax.set_title(title or "Single point (no plot)")
		return fig, ax, ax.lines[-1] if ax.lines else None

	FD = FDTD_instance
	Edatas = FD.getresult(monitor_name, attr)
	# 1) 先拿到闭区间索引与坐标子集
	x0, x1, y0, y1, z0, z1, xs, ys, zs = get_metric_idx(
		Edatas,
		x_min=x_min, x_max=x_max,
		y_min=y_min, y_max=y_max,
		z_min=z_min, z_max=z_max
	)

	# 2) 按索引与频点裁剪电场（频点可用索引或实际值）
	E_sel = get_select_E(Edatas, x0, x1, y0, y1, z0, z1, frequency=frequency)  # 用索引
	# E_sel = get_select_E(Edatas, x0, x1, y0, y1, z0, z1, frequency=1.55e14)  # 用频率值

	# 3) 画图（默认强度 abs2；dim 选电场分量）

	# aspect = "physical"
	# aspect="auto"
	# aspect="equal"

	fig, ax, h = plot_E_2D(E_sel, xs, ys, zs, dim=dim, value=value, title=title, aspect=aspect)
	if plot_flag:
		plt.show()
	# E_scalar = np.sum(np.abs(E_sel) ** 2, axis=-1)
	# input("输入回车结束程序")

	if save_path:
		import os
		os.makedirs(save_path, exist_ok=True)
		import time
		current_time = time.strftime("%m%d-%H%M")
		fig.savefig(f"{save_path}{current_time}_{title}.png", dpi=300)
	return fig, ax, h
