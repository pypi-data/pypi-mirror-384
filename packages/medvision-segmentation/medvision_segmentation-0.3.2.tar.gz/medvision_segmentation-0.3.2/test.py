import os
import nibabel as nib

def print_nii_info_recursive(folder_path):
    """递归遍历文件夹并打印每个 NIfTI 文件的格式信息"""
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".nii") or file.endswith(".nii.gz"):
                file_path = os.path.join(root, file)
                print(f"\n📄 文件路径: {file_path}")

                try:
                    img = nib.load(file_path)
                    hdr = img.header

                    print("🧠 文件信息：")
                    print(f"  数据类型: {hdr.get_data_dtype()}")
                    print(f"  图像维度: {hdr.get_data_shape()}")
                    print(f"  像素间距: {hdr.get_zooms()}")
                    print(f"  空间单位: {hdr.get_xyzt_units()}")
                    print(f"  仿射矩阵:\n{img.affine}")

                except Exception as e:
                    print(f"⚠️  无法读取文件: {e}")

# 示例调用
folder = "LITS2017"  # 改成你的文件夹路径
print_nii_info_recursive(folder)