import os
import shutil


def u_print(*args, **kwargs):
	'''
	把1e-6变为μ，输出更美观
	:param args:
	:param kwargs:
	:return:
	'''

	def format_scientific_notation(value):
		"""
		格式化单个值，如果是科学计数法的数字，转换为更美观的表示。
		"""
		if isinstance(value, (float, int)):  # 如果是数字类型，直接处理
			if 1e-07 < abs(value) < 1e-05:
				return f"{value * 1e6:.3f} μ"
			return value
		elif isinstance(value, str):  # 如果是字符串，检查是否含科学计数法的数字
			try:
				# 单独的科学计数法数字字符串
				num = float(value)
				if 1e-07 < abs(num) < 1e-05:
					return f"{num * 1e6:.3f} μ"
				return value
			except ValueError:
				# 含科学计数法数字的混合字符串
				# 查找并替换科学计数法数字
				import re
				def replace_scientific(match):
					num = float(match.group())
					if 1e-07 < abs(num) < 1e-05:
						return f"{num * 1e6:.3f} μ"
					return match.group()

				return re.sub(r"-?\d+(\.\d+)?e[+-]?\d+", replace_scientific, value)
		return value

	# 格式化所有的args
	formatted_args = [format_scientific_notation(arg) for arg in args]
	# 调用原生的print函数
	print(*formatted_args, **kwargs)


def str_to_list_for_excel(str):
	str.strip(",")
	for i in str.split(","):
		print(i)


def cal_slope():
	x1 = eval(input("x1="))
	y1 = eval(input("y1="))
	x2 = eval(input("x2="))
	y2 = eval(input("y2="))
	slope = (y2 - y1) / (x2 - x1)
	print(f"slope={slope:.3f}")
	neff = slope * 1.55e-6 / 2 / 3.1415927
	print(f"neff={neff:.3f}")


def min_span(min, max):
	'''转换min,max到pos,span'''
	return (min + max) / 2, max - min


def span_min(pos, span):
	'''转换pos,span到min,max'''
	return pos - span / 2, pos + span / 2


def cal_neff(L, Delta_phi):
	pi = 3.1415927
	wavelength = 1.55e-6
	k0 = 2 * pi / wavelength
	neff = wavelength / 2 / pi / L * Delta_phi
	return neff


def analyze_list_deviation(data_list):
	"""
	接收一个列表，返回平均值和偏离程度最大的项。

	Args:
		data_list (list): 一个包含数值的列表。

	Returns:
		tuple: 平均值和偏离程度最大的项 (mean, max_deviation_item, max_deviation_percent)。
	"""
	if not data_list:
		raise ValueError("列表不能为空！")

	# 计算平均值
	mean = sum(data_list) / len(data_list)

	# 计算每项与平均值的偏离程度（百分比形式）
	# deviations=[(项，偏离百分比),(项，偏离百分比),(项，偏离百分比)]
	deviations = [(item, abs(item - mean) / mean * 100) for item in data_list]

	# 找出偏离程度最大的项
	max_deviation_item, max_deviation_percent = max(deviations, key=lambda x: x[1])

	return mean, max_deviation_item, max_deviation_percent


def save_records(file_path=r"E:\0_Work_Documents\Simulation\lumerpy\01_equal-plane", file_name=r"temp.fsp",
				 file_path_copy=r"E:\0_Work_Documents\Simulation\lumerpy\01_equal-plane\records"):
	import os
	import time
	import shutil
	formatted_time = time.strftime("%Y%m%d_%H-%M-%S", time.localtime())
	saved_file = file_name.removesuffix(".fsp") + f"_{formatted_time}" + ".fsp"
	# saved_file=file_name.removesuffix(".fsp")+f"k{k}"+".fsp"
	saved_file_total = os.path.join(file_path_copy, saved_file)
	copy_file_total = os.path.join(file_path, file_name)
	shutil.copy(copy_file_total, saved_file_total)
	return True


def check_path_and_file(file_path, file_name, auto_newfile=True, template_file=None):
	"""
	检查路径和文件名是否存在。
	如果路径不存在则创建路径，如果文件名不存在则复制模板文件到指定路径并重命名。

	:param file_path: 文件路径 (字符串)
	:param file_name: 文件名 (字符串)
	:param auto_newfile: 若路径不存在，是否自动创建文件
	:param template_file: 模板文件路径 (字符串，可选，默认与库代码同路径下的模板文件)
	"""
	# 获取库文件所在的目录
	current_dir = os.path.dirname(os.path.abspath(__file__))
	# print(current_dir)
	if template_file is None:
		template_file = os.path.join(current_dir, "temp.fsp")
	else:
		# 确保提供的模板路径也是基于当前库路径
		if not os.path.isabs(template_file):
			template_file = os.path.join(current_dir, template_file)

	# 检查路径是否存在
	if not os.path.exists(file_path):
		if auto_newfile:  # 自动创建文件
			print(f"路径 '{file_path}' 不存在，正在创建路径...")
			os.makedirs(file_path)
			print(f"路径 '{file_path}' 创建成功！")
		else:
			raise FileExistsError("文件不存在，请检查文件路径")

	# 检查文件是否存在
	full_file_path = os.path.join(file_path, file_name)
	if not os.path.isfile(full_file_path):
		print(f"文件 '{full_file_path}' 不存在！")
		if template_file and os.path.isfile(template_file):
			shutil.copy(template_file, full_file_path)
			print(f"已复制模板文件 '{template_file}' \n并更名到目录：'{full_file_path}'\n")
		else:
			print(f"未提供有效的模板文件，无法创建 '{file_name}'。")
		return False
	else:
		# print(f"文件 '{full_file_path}' 已存在。")
		return True


def get_single_inputs_center_x(
		channels=2, data_single_scale=(1, 10), margins_cycle=(0.1, 0.1, 0.1, 0.1),
		duty_cycle=0.5, shift_flag=False):
	"""返回各输入通道的中心像素值，开始像素值，通道宽度"""
	data_single_h, data_single_w = data_single_scale
	top_rate, bottom_rate, left_rate, right_rate = margins_cycle

	margin_T = int(data_single_h * top_rate)
	margin_B = int(data_single_h * bottom_rate)
	margin_L = int(data_single_w * left_rate)
	margin_R = int(data_single_w * right_rate)

	inner_h = data_single_h - margin_T - margin_B
	inner_w = data_single_w - margin_L - margin_R

	single_cycle_w = int(inner_w / channels)
	remain_w = inner_w - single_cycle_w * channels

	if remain_w % 2 == 0:
		margin_L += remain_w // 2
		margin_R += remain_w // 2
	elif remain_w % 2 == 1:
		margin_L += (remain_w - 1) // 2
		margin_R += (remain_w - 1) // 2 + 1
	else:
		print("程序肯定有点问题")

	single_inputs_w = int(single_cycle_w * duty_cycle)

	centers = []
	starts = []
	shift = (single_cycle_w - int(single_cycle_w * duty_cycle)) / 2
	for i in range(channels):
		start_x = margin_L + i * single_cycle_w
		if shift_flag:
			start_x = start_x + shift
		starts.append(start_x)
		# 原来的中心 + 额外往左 0.5。因为像素是分立的，例如只有2个像素，那么中心位置应当是按照1.5个像素考虑比较合适。但是需要注意1.5个像素是“不存在的”
		center_x = start_x + single_inputs_w / 2.0 - 0.5
		if shift_flag:
			center_x = center_x + shift
		centers.append(center_x)
	extra_gap = 1 / 2 * (single_inputs_w / duty_cycle - single_inputs_w)  # 这里的extra_gap好像并不需要，因为训练的时候extra_gap就是0
	# 这里的extra_gap实际上起到shift的作用，但是为了提高可读性，打算将其放到函数外面去处理；extra_gap的作用就是平移半个没有光的那个方框长度
	# 参考的外面处理方法为：
	# effective_y_span = slots_y_max - slots_y_min
	# scale_ratio = (effective_y_span / size[1])
	# source_y_ls.append(centers[i] * scale_ratio + extra_gap * scale_ratio)
	# starts_ls.append(starts[i] * scale_ratio + extra_gap_y * scale_ratio)
	return centers, starts, single_inputs_w, extra_gap

# print(get_single_inputs_center_x(channels=2,data_single_scale=(1,21),duty_cycle=0.5,margins_cycle=(0,0,0,0)))
