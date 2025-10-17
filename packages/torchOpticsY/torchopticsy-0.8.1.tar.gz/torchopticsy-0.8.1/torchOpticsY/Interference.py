# %%
import torch
import torch.nn.functional as F
import cv2
import os
import matplotlib.pyplot as plt


# def visualize_filter(f_wave, angle_deg, mask, max_size=256):
#     """
#     用 matplotlib 显示低分辨率版本以提高显示速度
#     :param f_wave: complex tensor (H, W)
#     :param angle_deg: 用于标题
#     :param mask: bool or float tensor (H, W)
#     :param max_size: 显示最大尺寸（默认 256）
#     """
#     if f_wave.is_cuda:
#         f_wave = f_wave.cpu()
#     if mask.is_cuda:
#         mask = mask.cpu()

#     # 计算幅度谱
#     mag = torch.log1p(torch.abs(f_wave * mask))  # shape: (H, W)

#     # Downsample 图像（插值前需加 batch 和 channel 维度）
#     def downsample(tensor):
#         H, W = tensor.shape
#         scale = min(max_size / H, max_size / W, 1.0)
#         new_h = int(H * scale)
#         new_w = int(W * scale)
#         tensor = tensor.unsqueeze(0).unsqueeze(0)  # shape -> (1, 1, H, W)
#         return F.interpolate(
#             tensor, size=(new_h, new_w), mode="bilinear", align_corners=False
#         )[0, 0]

#     mask_small = downsample(mask.float())
#     mag_small = downsample(mag)

#     # 显示
#     plt.figure(figsize=(10, 5))

#     plt.subplot(1, 2, 1)
#     plt.imshow(mask_small, cmap="gray")
#     plt.title("Mask")

#     plt.subplot(1, 2, 2)
#     plt.imshow(mag_small, cmap="gray")
#     plt.title(f"Filtered FFT ({angle_deg}°)")

#     plt.tight_layout()
#     plt.show()


# class OffAxisPhase:
#     def __init__(
#         self,
#         file_name,
#         continuous=True,  # 默认是连续光
#     ):
#         self.continuous = continuous

#         # 支持的图片后缀
#         self.valid_ext = [".jpg", ".png", ".bmp"]

#         # 读取三幅图
#         BACK = self._read_image("BACK", file_name)
#         self.OBJ = torch.clamp(self._read_image("OBJ", file_name) - BACK, min=0)
#         self.REF = torch.clamp(self._read_image("REF", file_name) - BACK, min=0)
#         self.OBJ_REF = torch.clamp(self._read_image("OBJ_REF", file_name) - BACK, min=0)
#         self.INC = torch.clamp(self._read_image("INC", file_name) - BACK, min=0)
#         self.INC_REF = torch.clamp(self._read_image("INC_REF", file_name) - BACK, min=0)

#     def _read_image(self, prefix, file_name):
#         for ext in self.valid_ext:
#             img_path = os.path.join(file_name, f"{prefix}{ext}")
#             if os.path.exists(img_path):
#                 img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)  # 保留原始位深
#                 if img is None:
#                     raise ValueError(f"无法读取图像: {img_path}")
#                 # img = cv2.medianBlur(img, 3)
#                 # img = cv2.GaussianBlur(img, (3,3), sigmaX=1.0)
#                 img_tensor = torch.from_numpy(img)

#                 if img_tensor.dtype == torch.uint8:
#                     img_tensor = img_tensor.to(torch.float32) / 255.0
#                 elif img_tensor.dtype == torch.uint16:
#                     img_tensor = img_tensor.to(torch.float32) / 65535.0
#                 else:
#                     raise ValueError(f"不支持的图像位深: {img_tensor.dtype}")

#                 return img_tensor
#         raise FileNotFoundError(f"在 {file_name} 中找不到 {prefix} 图像")

#     def __call__(self, angle_deg=0, visualize=False):
#         def filter_one(input_tensor, angle_deg):
#             f = torch.fft.fftshift(torch.fft.fft2(input_tensor))

#             H, W = f.shape
#             ky_vals = torch.fft.fftshift(torch.fft.fftfreq(H, d=1.0 / H)).to(f.device)
#             kx_vals = torch.fft.fftshift(torch.fft.fftfreq(W, d=1.0 / W)).to(f.device)
#             KY, KX = torch.meshgrid(ky_vals, kx_vals, indexing="ij")

#             angle = torch.deg2rad(torch.tensor(angle_deg))
#             vx, vy = torch.cos(angle), torch.sin(angle)

#             cross = vx * KY - vy * KX
#             mask = cross >= 0

#             # 可视化
#             if visualize:
#                 visualize_filter(f, angle_deg, mask)
#             f_filtered = f * mask
#             result = torch.fft.ifft2(torch.fft.ifftshift(f_filtered))
#             return result

#         a = self.OBJ_REF - self.OBJ - self.REF
#         b = self.INC_REF - self.INC - self.REF

#         a = filter_one(a, angle_deg)
#         b = filter_one(b, angle_deg)

#         E = a / b
#         E[~torch.isfinite(E)] = 0
#         return E


# 新的
class OffAxisPhase:
    def __init__(
        self,
        file_name,
        continuous=True,  # 默认是连续光
        block_size=1024,  # 每个子块的大小
        overlap=0,  # 子块之间是否重叠
    ):
        self.continuous = continuous
        self.block_size = block_size
        self.overlap = overlap

        # 支持的图片后缀
        self.valid_ext = [".jpg", ".png", ".bmp"]

        # 读取图像
        BACK = self._read_image("BACK", file_name)
        self.OBJ = torch.clamp(self._read_image("OBJ", file_name) - BACK, min=0)
        self.REF = torch.clamp(self._read_image("REF", file_name) - BACK, min=0)
        self.OBJ_REF = torch.clamp(self._read_image("OBJ_REF", file_name) - BACK, min=0)
        self.INC = torch.clamp(self._read_image("INC", file_name) - BACK, min=0)
        self.INC_REF = torch.clamp(self._read_image("INC_REF", file_name) - BACK, min=0)

    def _read_image(self, prefix, file_name):
        for ext in self.valid_ext:
            img_path = os.path.join(file_name, f"{prefix}{ext}")
            if os.path.exists(img_path):
                img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                if img is None:
                    raise ValueError(f"无法读取图像: {img_path}")
                img_tensor = torch.from_numpy(img)

                if img_tensor.dtype == torch.uint8:
                    img_tensor = img_tensor.to(torch.float32) / 255.0
                elif img_tensor.dtype == torch.uint16:
                    img_tensor = img_tensor.to(torch.float32) / 65535.0
                else:
                    raise ValueError(f"不支持的图像位深: {img_tensor.dtype}")
                return img_tensor
        raise FileNotFoundError(f"在 {file_name} 中找不到 {prefix} 图像")

    def _split_blocks(self, img):
        H, W = img.shape
        step = self.block_size - self.overlap
        blocks = []

        y_list = list(range(0, H - self.block_size + 1, step))
        x_list = list(range(0, W - self.block_size + 1, step))

        # 确保边缘覆盖
        if y_list[-1] != H - self.block_size:
            y_list.append(H - self.block_size)
        if x_list[-1] != W - self.block_size:
            x_list.append(W - self.block_size)

        for y in y_list:
            for x in x_list:
                blocks.append(
                    ((y, x), img[y : y + self.block_size, x : x + self.block_size])
                )

        return blocks, H, W

    def _estimate_angle(self, block, global_angle):
        """先用全局角度粗筛，再精确估计局部峰值角度"""
        f = torch.fft.fftshift(torch.fft.fft2(block))

        H, W = f.shape
        ky_vals = torch.fft.fftshift(torch.fft.fftfreq(H, d=1.0 / H)).to(f.device)
        kx_vals = torch.fft.fftshift(torch.fft.fftfreq(W, d=1.0 / W)).to(f.device)
        KY, KX = torch.meshgrid(ky_vals, kx_vals, indexing="ij")

        angle = torch.deg2rad(torch.tensor(global_angle))
        vx, vy = torch.cos(angle), torch.sin(angle)

        cross = vx * KY - vy * KX
        mask = cross >= 0
        mag = torch.abs(f) * mask  # 只保留一半
        # 去掉直流分量
        cy, cx = H // 2, W // 2
        mag[cy - 5 : cy + 5, cx - 5 : cx + 5] = 0
        # ==== Step 2: 找峰值 ====
        max_pos = torch.nonzero(mag == mag.max(), as_tuple=False)[0]
        dy, dx = max_pos[0] - mag.size(0) / 2, max_pos[1] - mag.size(1) / 2
        angle_loc = torch.atan2(-dx, dy)  # 子图峰值方向

        return torch.rad2deg(angle_loc).item(), f, mag

    def _filter_one(self, input_tensor, angle_deg):
        f = torch.fft.fftshift(torch.fft.fft2(input_tensor))

        H, W = f.shape
        ky_vals = torch.fft.fftshift(torch.fft.fftfreq(H, d=1.0 / H)).to(f.device)
        kx_vals = torch.fft.fftshift(torch.fft.fftfreq(W, d=1.0 / W)).to(f.device)
        KY, KX = torch.meshgrid(ky_vals, kx_vals, indexing="ij")

        angle = torch.deg2rad(torch.tensor(angle_deg))
        vx, vy = torch.cos(angle), torch.sin(angle)

        cross = vx * KY - vy * KX
        mask = cross >= 0

        f_filtered = f * mask
        result = torch.fft.ifft2(torch.fft.ifftshift(f_filtered))
        return result, f, mask

    def __call__(self, angle_deg=0, visualize=False, vis_num=4):
        # 分块处理
        a_full = self.OBJ_REF - self.OBJ - self.REF
        b_full = self.INC_REF - self.INC - self.REF

        blocks, H, W = self._split_blocks(a_full)
        E_full = torch.zeros((H, W), dtype=torch.complex64)

        vis_count = 0
        for (y, x), a_block in blocks:
            b_block = b_full[y : y + self.block_size, x : x + self.block_size]

            # 每个子块独立估计方向
            block_angle, f_b, mag_b = self._estimate_angle(b_block, angle_deg)

            a_filtered, f_a, mask_a = self._filter_one(a_block, block_angle)
            b_filtered, _, mask_b = self._filter_one(b_block, block_angle)

            E = a_filtered / b_filtered
            E[~torch.isfinite(E)] = 0

            # 放回全图
            E_full[y : y + self.block_size, x : x + self.block_size] = E

            # 可视化部分子图
            if visualize and vis_count < vis_num:
                plt.figure(figsize=(12, 6))
                plt.suptitle(f"Block ({y},{x}), angle={block_angle:.2f}°")

                plt.subplot(2, 2, 1)
                plt.imshow(torch.log1p(mag_b).cpu(), cmap="gray")
                plt.title("b FFT magnitude (before)")

                plt.subplot(2, 2, 2)
                plt.imshow(torch.log1p(torch.abs(f_b * mask_b)).cpu(), cmap="gray")
                plt.title("b FFT after mask")

                plt.subplot(2, 2, 3)
                plt.imshow(torch.log1p(torch.abs(torch.abs(f_a))).cpu(), cmap="gray")
                plt.title("a FFT magnitude (before)")

                plt.subplot(2, 2, 4)
                plt.imshow(torch.log1p(torch.abs(f_a * mask_a)).cpu(), cmap="gray")
                plt.title("a FFT after mask")

                plt.tight_layout()
                plt.show()

                vis_count += 1

        return E_full
