from .fdtd_manager import get_fdtd_instance
import lumerpy as lupy

u = 1e-6


def add_power_monitor(name="phase", x_min=0, x_max=0, y_min=0, y_max=0, z_min=0, z_max=0,
					  monitor_type="2D Z-normal"):
	FD = get_fdtd_instance()
	ob_power_monitor = FD.addpower()
	FD.set("name", name)

	if monitor_type == "2D X-normal":
		if x_min != x_max:
			print("对待放置的2D X-normal监视器，输入的x_min和x_max不相等，这将是其x坐标，请检查！")
		else:
			FD.set("monitor type", monitor_type)
			FD.set("x", x_min)
			FD.set("y min", y_min)
			FD.set("y max", y_max)
			FD.set("z min", z_min)
			FD.set("z max", z_max)
	elif monitor_type == "2D Y-normal":
		if y_min != y_max:
			print("对待放置的2D Y-normal监视器，输入的y_min和y_max不相等，这将是其y坐标，请检查！")
		else:
			FD.set("monitor type", monitor_type)
			FD.set("y", y_min)
			FD.set("x min", x_min)
			FD.set("x max", x_max)
			FD.set("z min", z_min)
			FD.set("z max", z_max)
	elif monitor_type == "2D Z-normal":
		if z_min != z_max:
			print("对待放置的2D Z-normal监视器，输入的z_min和z_max不相等，这将是其z坐标，请检查！")
		else:
			FD.set("monitor type", monitor_type)
			FD.set("x min", x_min)
			FD.set("x max", x_max)
			FD.set("y min", y_min)
			FD.set("y max", y_max)
			FD.set("z", z_min)
	elif monitor_type == "Linear X":
		if y_min != y_max or z_min != z_max:
			print("对待放置的Linear X监视器，输入的y_min和y_max，和（或）z_min和z_max不相等，这将是其y，z坐标，请检查！")
		else:
			FD.set("monitor type", monitor_type)
			FD.set("x min", x_min)
			FD.set("x max", x_max)
			FD.set("y", y_min)
			FD.set("z", z_min)
	elif monitor_type == "Linear Y":
		if x_min != x_max or z_min != z_max:
			print("对待放置的Linear Y监视器，输入的x_min和x_max，和（或）z_min和z_max不相等，这将是其x，z坐标，请检查！")
		else:
			FD.set("monitor type", monitor_type)
			FD.set("y min", y_min)
			FD.set("y max", y_max)
			FD.set("x", x_min)
			FD.set("z", z_min)
	elif monitor_type == "Linear Z":
		if x_min != x_max or y_min != y_max:
			print("对待放置的Linear Z监视器，输入的x_min和x_max，和（或）y_min和y_max不相等，这将是其x，y坐标，请检查！")
		else:
			FD.set("monitor type", monitor_type)
			FD.set("z min", z_min)
			FD.set("z max", z_max)
			FD.set("x", x_min)
			FD.set("y", y_min)
	else:
		print("传入参数monitor_type设置错误，必须为"
			  "\n\t【2D X-normal】【2D Y-normal】【2D Z-normal】"
			  "\n\t【Linear X】【Linear Y】【Linear Z】\n中的一个")
	return ob_power_monitor


def add_global_monitor(name="global",
					   monitor_type="2D Z-normal", dipole_avoid=False, dipole_avoid_delta_x=0.1 * u):
	# 添加全局监视器，看场俯视图
	FD = get_fdtd_instance()
	if FD.getnamednumber("FDTD"):
		sim_name = "FDTD"
	elif FD.getnamednumber("FDE"):
		sim_name = "FDE"
	elif FD.getnamednumber("varFDTD"):
		sim_name = "varFDTD"
	elif FD.getnamednumber("EME"):
		sim_name = "EME"
	else:
		print("警告！未找到FDTD Solution或MODE Solution对应的仿真区域，无法创建全局监视器")
		return 0
	FD.select(sim_name)
	x_min = FD.getnamed("FDTD", "x min")
	x_max = FD.getnamed("FDTD", "x max")
	y_min = FD.getnamed("FDTD", "y min")
	y_max = FD.getnamed("FDTD", "y max")
	z_min = FD.getnamed("FDTD", "z min")
	z_max = FD.getnamed("FDTD", "z max")

	# dipole附近的场经常是非物理的，如果dipole_avoid非0，那么就往x正方向挪delta_x的距离，避免非物理波源的影响
	if dipole_avoid:
		if FD.getnamednumber("dipole"):
			if monitor_type == "2D Z-normal":
				x_min = FD.getnamed("dipole", "x")
				x_min = x_min + dipole_avoid_delta_x
		else:
			print("本函数还没写完，没找到名为dipole的源，先这样吧")
			return False

	ob_power_monitor = None

	if monitor_type == "2D X-normal":
		ob_power_monitor = add_power_monitor(name=name, x_min=(x_min + x_max) / 2, x_max=(x_min + x_max) / 2,
											 y_min=y_min, y_max=y_max,
											 z_min=z_min, z_max=z_max, monitor_type="2D X-normal")
	elif monitor_type == "2D Y-normal":
		ob_power_monitor = add_power_monitor(name=name, x_min=x_min, x_max=x_max,
											 y_min=(y_min + y_max) / 2, y_max=(y_min + y_max) / 2,
											 z_min=z_min, z_max=z_max, monitor_type="2D Y-normal")
	elif monitor_type == "2D Z-normal":
		ob_power_monitor = add_power_monitor(name=name, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max,
											 z_min=(z_min + z_max) / 2, z_max=(z_min + z_max) / 2,
											 monitor_type="2D Z-normal")
	elif monitor_type == "Linear X":
		ob_power_monitor = add_power_monitor(name=name, x_min=x_min, x_max=x_max, y_min=(y_min + y_max) / 2,
											 y_max=(y_min + y_max) / 2,
											 z_min=(z_min + z_max) / 2, z_max=(z_min + z_max) / 2,
											 monitor_type="Linear X")
	elif monitor_type == "Linear Y":
		ob_power_monitor = add_power_monitor(name=name, x_min=(x_min + x_max) / 2, x_max=(x_min + x_max) / 2,
											 y_min=y_min, y_max=y_max,
											 z_min=(z_min + z_max) / 2, z_max=(z_min + z_max) / 2,
											 monitor_type="Linear Y")
	elif monitor_type == "Linear Z":
		ob_power_monitor = add_power_monitor(name=name, x_min=(x_min + x_max) / 2, x_max=(x_min + x_max) / 2,
											 y_min=(y_min + y_max) / 2,
											 y_max=(y_min + y_max) / 2, z_min=z_min, z_max=z_max,
											 monitor_type="Linear Z")
	else:
		print("传入参数monitor_type设置错误，必须为"
			  "\n\t【2D X-normal】【2D Y-normal】【2D Z-normal】"
			  "\n\t【Linear X】【Linear Y】【Linear Z】\n中的一个")
		return None
	return ob_power_monitor


def add_power_monitor_metaline(monitor_name="", metaline_name=""):
	"""给指定名字的衍射线添加一条线类型功率监视器，几何位置位于衍射线中心"""
	FD = get_fdtd_instance()
	x_min = FD.getnamed(metaline_name, "x min")
	x_max = FD.getnamed(metaline_name, "x max")
	y = FD.getnamed(metaline_name, "y")
	z = FD.getnamed(metaline_name, "z")
	ob_power_monitor = add_power_monitor(name=monitor_name, x_min=x_min, x_max=x_max, y_min=y, y_max=y, z_min=z,
										 z_max=z, monitor_type="Linear X")
	return ob_power_monitor


def add_basic_monitors_X_prop(x_start=0, x_end=0, distance=0, fdtd_x_min=0, fdtd_x_max=0, fdtd_y_min=0, fdtd_y_max=0,
							  fdtd_z_min=0, fdtd_z_max=0, mesh_output_flag=False,mesh_equ_idx=2):
	'''添加全局监视器，看场俯视图'''
	FD = get_fdtd_instance()
	ob_moni_glo = add_global_monitor()
	# 添加前监视器，看场相位图
	ob_moni_fro = FD.addpower()
	FD.set("name", "front")
	FD.set("monitor type", "2D X-normal")
	FD.set("x", x_start)
	FD.set("y min", fdtd_y_min)
	FD.set("y max", fdtd_y_max)
	FD.set("z min", fdtd_z_min)
	FD.set("z max", fdtd_z_max)
	# 添加后监视器，看场相位图
	ob_moni_bac = FD.addpower()
	FD.set("name", "back")
	FD.set("monitor type", "2D X-normal")
	FD.set("x", x_end)
	FD.set("y min", fdtd_y_min)
	FD.set("y max", fdtd_y_max)
	FD.set("z min", fdtd_z_min)
	FD.set("z max", fdtd_z_max)

	ob_moni_loc = add_power_monitor(name="local", x_min=-10 * u, x_max=10 * u, y_min=fdtd_y_min, y_max=fdtd_y_max,
									z_min=0.11 * u,
									z_max=0.11 * u)
	ob_moni_glo1 = add_power_monitor(name="global_without_source_1", x_min=-10 * u, x_max=fdtd_x_max, y_min=fdtd_y_min,
									 y_max=fdtd_y_max, z_min=0.11 * u,
									 z_max=0.11 * u)
	ob_moni_glo2 = add_power_monitor(name="global_without_source_2", x_min=-distance - 10 * u, x_max=fdtd_x_max,
									 y_min=fdtd_y_min,
									 y_max=fdtd_y_max, z_min=0.11 * u,
									 z_max=0.11 * u)
	ob_moni_loc_outputs = add_power_monitor(name="local_outputs", x_min=fdtd_x_max - 0.1 * u,
											x_max=fdtd_x_max - 0.1 * u,
											y_min=fdtd_y_min,
											y_max=fdtd_y_max, z_min=fdtd_z_min,
											z_max=fdtd_z_max, monitor_type="2D X-normal")
	if mesh_output_flag:
		lupy.simulation.add_mesh(x_min=fdtd_x_max - 0.2 * u, x_max=fdtd_x_max,
								 y_min=fdtd_y_min, y_max=fdtd_y_max,
								 z_min=fdtd_z_min, z_max=fdtd_z_max,
								 set_equ_inx_flag=True,
								 equ_x_index=mesh_equ_idx,
								 equ_y_index=mesh_equ_idx,
								 equ_z_index=mesh_equ_idx,
								 )
	return ob_moni_glo, ob_moni_fro, ob_moni_bac, ob_moni_loc, ob_moni_glo1, ob_moni_glo2, ob_moni_loc_outputs


def add_eri_monitors(metaline_ls, layer_num):
	# 这里有bug，先不改了
	name_series_eri = "eri"
	print(f"共放置监视器数量：{len(metaline_ls)}")
	metalin_layer_num = int(len(metaline_ls) / layer_num)
	for j in range(layer_num):  # 放完一层放下一层
		name_layer_eri = name_series_eri + f"{j}"
		for i in range(metalin_layer_num - 1):
			moni_x_min = metaline_ls[i + j * metalin_layer_num]["x min"]
			moni_x_max = metaline_ls[i + j * metalin_layer_num]["x max"]
			moni_y = (metaline_ls[i + j * metalin_layer_num + 1]["y"] + metaline_ls[i + j * metalin_layer_num]["y"]) / 2
			moni_z = metaline_ls[i + j * metalin_layer_num]["z"]
			add_power_monitor(name=name_layer_eri + f"{i + j * metalin_layer_num}", x_min=moni_x_min, x_max=moni_x_max,
							  y_min=moni_y,
							  y_max=moni_y,
							  z_min=moni_z, z_max=moni_z, monitor_type="Linear X")
