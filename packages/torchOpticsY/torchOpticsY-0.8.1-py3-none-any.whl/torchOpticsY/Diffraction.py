import torch
import torch.nn.functional as F


class BluesteinDFT:
    # Due to the error in periodic expansion, it can be treated by making up for zeros in the future
    # Now only the central region is relatively accurate, and the surrounding area is affected by pseudo-diffraction by periodic conditions
    def __init__(self, f1, f2, fs, mout, m_input, device="cpu"):
        self.device = torch.device(device)
        self.f1 = f1
        self.f2 = f2
        self.fs = fs
        self.mout = mout
        self.m_input = m_input

        # Frequency adjustment
        f11 = f1 + (mout * fs + f2 - f1) / (2 * mout)
        f22 = f2 + (mout * fs + f2 - f1) / (2 * mout)
        self.f11 = f11
        self.f22 = f22

        # Chirp parameters
        a = torch.exp(1j * 2 * torch.pi * torch.tensor(f11 / fs))
        w = torch.exp(-1j * 2 * torch.pi * torch.tensor(f22 - f11) / (mout * fs))
        self.a = a.to(self.device)
        self.w = w.to(self.device)

        h = torch.arange(
            -m_input + 1,
            max(mout - 1, m_input - 1) + 1,
            device=self.device,
            dtype=torch.float64,
        )
        h = self.w ** ((h**2) / 2)

        self.h = h
        self.mp = m_input + mout - 1
        padded_len = 2 ** int(torch.ceil(torch.log2(torch.tensor(self.mp))))
        self.padded_len = padded_len

        h_inv = torch.zeros(padded_len, dtype=torch.complex64, device=self.device)
        h_inv[: self.mp] = 1 / h[: self.mp]
        self.ft = torch.fft.fft(h_inv)

        b_exp = torch.arange(0, m_input, device=self.device)
        self.b_phase = (self.a**-b_exp) * h[m_input - 1 : 2 * m_input - 1]

        l = torch.linspace(0, mout - 1, mout, device=self.device)
        l = l / mout * (f22 - f11) + f11
        Mshift = -m_input / 2
        self.Mshift = torch.exp(-1j * 2 * torch.pi * l * (Mshift + 0.5) / fs)

    def transform(self, x, dim=-1):
        x = x.to(self.device)
        m = self.m_input

        dim = dim if dim >= 0 else x.ndim + dim

        if x.shape[dim] != m:
            print(m)
            print(x.shape)
            raise ValueError(
                f"Expected dimension {dim} to be of size {m}, but got {x.shape[dim]}"
            )

        x = x.transpose(dim, -1)

        b_phase = self.b_phase.view((1,) * (x.ndim - 1) + (-1,))
        x_weighted = x * b_phase

        original_shape = x_weighted.shape
        x_weighted = x_weighted.reshape(-1, m)

        b_padded = torch.zeros(
            (x_weighted.shape[0], self.padded_len),
            dtype=torch.complex64,
            device=self.device,
        )
        b_padded[:, :m] = x_weighted

        b_fft = torch.fft.fft(b_padded, dim=1)
        conv = b_fft * self.ft[None, :]
        result = torch.fft.ifft(conv, dim=1)

        result = (
            result[:, self.m_input - 1 : self.mp] * self.h[self.m_input - 1 : self.mp]
        )
        result = result * self.Mshift[None, :]

        new_shape = list(original_shape[:-1]) + [self.mout]
        result = result.reshape(*new_shape)

        result = result.transpose(-1, dim)

        return result


class DebyeWolf:
    def __init__(
        self,
        Min,
        xrange,
        yrange,
        zrange,
        Mout,
        lams,  # list of wavelengths
        NA,
        focal_length,
        n1=1,
        device="cpu",
    ):
        self.device = device
        self.Min = Min
        self.xrange = xrange
        self.yrange = yrange
        self.z_arr = torch.linspace(zrange[0], zrange[1], Mout[2], device=device)
        self.Moutx, self.Mouty = Mout[0], Mout[1]
        lams = torch.tensor(lams, device=device)
        self.lams, self.k0, self.n1, self.NA, self.focal_length = (
            lams,
            2 * torch.pi / lams,
            n1,
            NA,
            focal_length,
        )

        self.N = (Min - 1) / 2

        m = torch.linspace(-Min / 2, Min / 2, Min, device=self.device)
        n = torch.linspace(-Min / 2, Min / 2, Min, device=self.device)
        self.m_grid, self.n_grid = torch.meshgrid(m, n, indexing="ij")

        self.th = torch.asin(
            torch.clamp(
                NA * torch.sqrt(self.m_grid**2 + self.n_grid**2) / (self.N * n1), max=1
            )
        )
        self.mask = self.th > torch.arcsin(torch.tensor(NA / n1))
        self.phi = torch.atan2(self.n_grid, self.m_grid)
        self.phi[self.phi < 0] += 2 * torch.pi

        self._sqrt_costh = 1 / torch.sqrt(torch.cos(self.th).unsqueeze(-1))
        self._sqrt_costh[torch.isnan(self._sqrt_costh)] = 0
        self._sqrt_costh[self.mask] = 0

        fs = lams * (Min - 1) / (2 * NA)
        self.fs = fs
        self.bluesteins_y = []
        self.bluesteins_x = []
        self.C = (
            -1j
            * torch.exp(1j * self.k0 * n1 * focal_length)
            * focal_length
            * (lams)
            / (self.n1)
            / fs
            / fs
        )
        fs = fs.cpu().tolist()
        for f in fs:
            self.bluesteins_y.append(
                BluesteinDFT(
                    f / 2 + self.yrange[0],
                    f / 2 + self.yrange[1],
                    f,
                    self.Mouty,
                    Min,
                    device=device,
                )
            )
            self.bluesteins_x.append(
                BluesteinDFT(
                    f / 2 + self.xrange[0],
                    f / 2 + self.xrange[1],
                    f,
                    self.Moutx,
                    Min,
                    device=device,
                )
            )
        self.E_ideals = torch.ones_like(self.lams)
        self.R = torch.stack(
            [
                -torch.sin(self.th) * torch.cos(self.phi),
                -torch.sin(self.th) * torch.sin(self.phi),
                torch.cos(self.th),
            ],
            dim=-1,
        )
        self.R = self.R.unsqueeze(-2)

    def __call__(self, E, correct=False):
        # The input E has shape (batch, x, y, 2, lam),
        # where the z-component is not included.
        # The output E has shape (batch, x, y, z, 3, lam).
        # For different wavelengths (lam), a simple for-loop is used for now.

        Ex_in, Ey_in = E[..., 0:1, :], E[..., 1:2, :]
        th = self.th.unsqueeze(-1).unsqueeze(-1)
        phi = self.phi.unsqueeze(-1).unsqueeze(-1)
        z_arr = self.z_arr.unsqueeze(0).unsqueeze(0).unsqueeze(-1)
        k0, n1 = self.k0.view(1, 1, 1, -1), self.n1

        costh = torch.cos(th)
        _sqrt_costh = self._sqrt_costh.unsqueeze(-1)
        phase = torch.exp(1j * k0 * n1 * z_arr * costh)
        deltadim = 0
        C = (self.C / self.E_ideals).view(1, 1, 1, -1)
        E_out = torch.zeros(
            [self.Moutx, self.Mouty, self.z_arr.numel(), 3, self.lams.numel()],
            dtype=torch.complex64,
            device=self.device,
        )
        if E.dim() == 5:
            th = th.unsqueeze(0)
            phi = phi.unsqueeze(0)
            z_arr = z_arr.unsqueeze(0)
            k0 = k0.unsqueeze(0)
            costh = costh.unsqueeze(0)
            _sqrt_costh = _sqrt_costh.unsqueeze(0)
            phase = phase.unsqueeze(0)
            C = C.unsqueeze(0)
            deltadim = 1
            E_out = torch.zeros(
                [
                    E.size(0),
                    self.Moutx,
                    self.Mouty,
                    self.z_arr.numel(),
                    3,
                    self.lams.numel(),
                ],
                dtype=torch.complex64,
                device=self.device,
            )
        Ex = (
            (
                Ex_in * (1 + (costh - 1) * torch.cos(phi) ** 2)
                + Ey_in * (costh - 1) * torch.cos(phi) * torch.sin(phi)
            )
            * phase
            * _sqrt_costh
        )

        Ey = (
            (
                Ex_in * (costh - 1) * torch.cos(phi) * torch.sin(phi)
                + Ey_in * (1 + (costh - 1) * torch.sin(phi) ** 2)
            )
            * phase
            * _sqrt_costh
        )

        Ez = (
            (Ex_in * torch.cos(phi) + Ey_in * torch.sin(phi))
            * torch.sin(th)
            * phase
            * _sqrt_costh
        )
        if correct:
            temp = torch.stack([Ex, Ey, Ez], dim=-1)
            temp = temp - 0.5 * self.R * torch.sum(self.R * temp, dim=-1, keepdim=True)
            Ex, Ey, Ez = temp[:, :, :, 0], temp[:, :, :, 1], temp[:, :, :, 2]
        for i in range(self.lams.numel()):
            E_out[..., 0, i] = self.bluesteins_x[i].transform(
                self.bluesteins_y[i].transform(Ex[..., i], dim=1 + deltadim),
                dim=0 + deltadim,
            )
            E_out[..., 1, i] = self.bluesteins_x[i].transform(
                self.bluesteins_y[i].transform(Ey[..., i], dim=1 + deltadim),
                dim=0 + deltadim,
            )
            E_out[..., 2, i] = self.bluesteins_x[i].transform(
                self.bluesteins_y[i].transform(Ez[..., i], dim=1 + deltadim),
                dim=0 + deltadim,
            )

        return C * E_out

    def Get_Z_offset_Phase(self, z):
        k0, n1 = self.k0, self.n1
        costh = torch.cos(self.th)
        phase = k0.view(1, 1, -1) * n1 * z * (-costh).unsqueeze(-1)
        return phase


def fft_circular_conv2d(E, G):
    E_fft = torch.fft.fft2(E.permute(2, 0, 1))
    G_fft = torch.fft.fft2(G.permute(2, 0, 1))
    C_fft = E_fft * G_fft
    C_ifft = torch.fft.ifft2(C_fft).permute(1, 2, 0)
    return C_ifft


def fourier_upsample2d(E: torch.Tensor, up_sample=1) -> torch.Tensor:
    x, y = E.shape[0], E.shape[1]
    Xn, Yn = x * up_sample, y * up_sample

    # 2D FFT（仅前两维），正交归一避免缩放差异
    F = torch.fft.fft2(E, dim=(0, 1), norm="ortho")
    Fc = torch.fft.fftshift(F, dim=(0, 1))

    # 频域补零到更大网格
    Fp = torch.zeros((Xn, Yn) + E.shape[2:], dtype=E.dtype, device=E.device)

    x0 = (Xn - x + 1) // 2
    y0 = (Yn - y + 1) // 2
    Fp[x0 : x0 + x, y0 : y0 + y, ...] = Fc

    Fp = torch.fft.ifftshift(Fp, dim=(0, 1))
    up_E_full = torch.fft.ifft2(Fp, dim=(0, 1), norm="ortho")

    X_keep = (x - 1) * up_sample + 1
    Y_keep = (y - 1) * up_sample + 1
    up_E = up_E_full[:X_keep, :Y_keep, ...] * up_sample
    return up_E


def upsample_coords_xy(x: torch.Tensor, y: torch.Tensor, up_sample: int):
    """
    输入:
      x: 原 x 轴坐标，形状 (Nx,)
      y: 原 y 轴坐标，形状 (Ny,)
      up_sample: 正整数，上采样倍数

    返回:
      x_up: 形状 ((Nx-1)*up + 1,)
      y_up: 形状 ((Ny-1)*up + 1,)
      （范围不变，步长缩小 1/up）
    说明:
      假设 x、y 为等间距采样（FFT/零填充本身也要求等间距）
    """
    if up_sample < 1:
        raise ValueError("up_sample 必须 >= 1")
    if up_sample == 1:
        return x, y

    if x.numel() < 2 or y.numel() < 2:
        raise ValueError("x 和 y 至少需要 2 个点用于定义范围。")

    # 直接按起点和终点线性插值（等间距）
    dx = (x[1] - x[0]) / up_sample * 1.5 * (up_sample - 1)
    dy = (y[1] - y[0]) / up_sample * 1.5 * (up_sample - 1)
    x_up = torch.linspace(
        x[0] + dx,
        x[-1] + dx,
        (x.numel() - 1) * up_sample + 1,
        device=x.device,
        dtype=x.dtype,
    )
    y_up = torch.linspace(
        y[0] + dy,
        y[-1] + dy,
        (y.numel() - 1) * up_sample + 1,
        device=y.device,
        dtype=y.dtype,
    )
    return x_up, y_up


class Luneburg:
    # The calculation method for Ez is different and omitted here.
    # The sampling theorem must be satisfied: T < lambda / 2
    def __init__(
        self,
        uv_len,  # Integration region
        x_range,
        y_range,
        z_range,
        sampling_interval,  # Sampling interval, a 1D array; strictly followed in xy-directions,
        # while z-direction is adaptively adjusted
        lams,
        focal_length,  # Evaluation is based on this focal length
        n1=1,
        up_sample=1,  # Integer > 1,
        device="cuda",
    ):
        self.device = device
        self.up_sample = up_sample
        lams = torch.tensor(lams, device=device)
        self.lams = lams
        self.k = 2 * torch.pi * n1 / self.lams
        self.n1 = n1
        self.focal_length = focal_length
        uv_len = uv_len - sampling_interval[0]
        ux_arr = torch.arange(
            -uv_len / 2 + x_range[0] - sampling_interval[0],
            x_range[1] + uv_len / 2,
            step=sampling_interval[0],
            device=device,
        )

        vy_arr = torch.arange(
            -uv_len / 2 + y_range[0] - sampling_interval[1],
            y_range[1] + uv_len / 2,
            step=sampling_interval[1],
            device=device,
        )
        z_arr = torch.linspace(
            z_range[0] + focal_length,
            z_range[1] + focal_length,
            int((z_range[1] - z_range[0]) / sampling_interval[2] / 2) * 2 + 1,
            device=device,
        )

        center = (
            round((x_range[0] + x_range[1]) / 2 / sampling_interval[0])
            * sampling_interval[0]
        )
        u_arr = ux_arr - center
        u_start_id = torch.argmin(torch.abs(u_arr + uv_len / 2))
        u_end_id = torch.argmin(torch.abs(u_arr - uv_len / 2))
        u_arr = u_arr[u_start_id : u_end_id + 1] + sampling_interval[0] / 2
        du = torch.mean(u_arr)
        u_arr = u_arr - du
        center = (
            round((y_range[0] + y_range[1]) / 2 / sampling_interval[1])
            * sampling_interval[1]
        )
        v_arr = vy_arr - center
        v_start_id = torch.argmin(torch.abs(v_arr + uv_len / 2))
        v_end_id = torch.argmin(torch.abs(v_arr - uv_len / 2))
        v_arr = v_arr[v_start_id : v_end_id + 1] + sampling_interval[1] / 2
        dv = torch.mean(v_arr)
        v_arr = v_arr - dv

        x_start_id = torch.argmin(torch.abs(ux_arr - x_range[0]))
        x_end_id = torch.argmin(torch.abs(ux_arr - x_range[1]))
        y_start_id = torch.argmin(torch.abs(vy_arr - y_range[0]))
        y_end_id = torch.argmin(torch.abs(vy_arr - y_range[1]))

        x_arr = ux_arr[x_start_id : x_end_id + 1] - du
        y_arr = vy_arr[y_start_id : y_end_id + 1] - dv

        co_public = (
            -1j
            * sampling_interval[0]
            * sampling_interval[1]
            * n1
            / self.lams.view(1, 1, 1, -1)
        )  # / 4 / torch.pi
        R_q = torch.sqrt(
            (ux_arr.view(-1, 1, 1, 1)) ** 2
            + (vy_arr.view(1, -1, 1, 1)) ** 2
            + z_arr.view(1, 1, -1, 1) ** 2
        )
        G_2D = self.k * R_q * 1j
        G_2D = (
            torch.exp(G_2D)
            / R_q**2
            * co_public
            * (1 - 1 / G_2D)
            * torch.sinc(
                n1
                * ux_arr.view(-1, 1, 1, 1)
                * sampling_interval[0]
                / (R_q * lams.view(1, 1, 1, -1))
            )
            * torch.sinc(
                n1
                * vy_arr.view(1, -1, 1, 1)
                * sampling_interval[1]
                / (R_q * lams.view(1, 1, 1, -1))
            )
        )

        self.G_2D = G_2D

        self.u_arr = u_arr
        self.v_arr = v_arr
        self.x_arr, self.y_arr = upsample_coords_xy(x_arr, y_arr, up_sample)
        self.z_arr = z_arr

        self.x_num = x_end_id - x_start_id + 1
        self.y_num = y_end_id - y_start_id + 1

        self.u_pad_num = ux_arr.numel() - u_arr.numel()
        self.v_pad_num = vy_arr.numel() - v_arr.numel()
        self.dS = sampling_interval[0] * sampling_interval[1]

    def __call__(self, E):
        # E should have shape (u, v, lam)
        if E.dim() == 3:
            E_padded = E
            pad = (
                0,
                0,  # No padding applied to the 2nd dimension (D2)
                self.v_pad_num,
                0,  # Extend on both sides of the 1st dimension (D1)
                self.u_pad_num,
                0,  # Extend on both sides of the 0th dimension (D0)
            )

            E_padded = F.pad(E_padded, pad, mode="constant", value=0)
            E_out = torch.zeros(
                [
                    self.x_num,
                    self.y_num,
                    self.z_arr.numel(),
                    self.lams.numel(),
                ],
                device=self.device,
                dtype=torch.complex64,
            )
            for z in range(self.z_arr.numel()):
                E_out[:, :, z, :] = fft_circular_conv2d(
                    E_padded, self.G_2D[:, :, z] * self.z_arr[z]
                )[
                    : self.x_num,
                    : self.y_num,
                ]
            E_out = fourier_upsample2d(E_out, self.up_sample)
            return E_out

    def Get_G_2D(self, x_f, y_f, z_f):  # Typically used for optimization and validation
        z = self.focal_length + z_f  # Detection coordinate
        co_public = -1j * self.dS * self.n1 / self.lams  # / 4 / torch.pi
        R_q = torch.sqrt(
            z**2
            + (x_f - self.u_arr.view(-1, 1, 1)) ** 2
            + (y_f - self.v_arr.view(1, -1, 1)) ** 2
        )
        ik0R = self.k.view(1, 1, -1) * R_q * 1j
        G_2D = torch.exp(ik0R) / R_q**2 * (1 - 1 / ik0R) * co_public

        return z * G_2D


class LuneburgOld:
    # The calculation method for Ez is different and omitted here.
    # The sampling theorem must be satisfied: T < lambda / 2
    def __init__(
        self,
        uv_len,  # Integration region
        x_range,
        y_range,
        z_range,
        sampling_interval,  # Sampling interval, a 1D array; strictly followed in xy-directions,
        # while z-direction is adaptively adjusted
        lams,
        focal_length,  # Evaluation is based on this focal length
        n1=1,
        scale=1,  # Integer > 1, used to represent a reduced sampling frequency for E
        device="cuda",
    ):
        self.device = device
        self.scale = scale
        lams = torch.tensor(lams, device=device)
        self.lams = lams
        self.k = 2 * torch.pi * n1 / self.lams
        self.n1 = n1
        self.focal_length = focal_length
        uv_len = uv_len - sampling_interval[0]
        ux_arr = torch.arange(
            -uv_len / 2 + x_range[0] - sampling_interval[0],
            x_range[1] + uv_len / 2,
            step=sampling_interval[0],
            device=device,
        )

        vy_arr = torch.arange(
            -uv_len / 2 + y_range[0] - sampling_interval[1],
            y_range[1] + uv_len / 2,
            step=sampling_interval[1],
            device=device,
        )
        z_arr = torch.linspace(
            z_range[0] + focal_length,
            z_range[1] + focal_length,
            int((z_range[1] - z_range[0]) / sampling_interval[2] / 2) * 2 + 1,
            device=device,
        )

        center = (
            round((x_range[0] + x_range[1]) / 2 / sampling_interval[0])
            * sampling_interval[0]
        )
        u_arr = ux_arr - center
        u_start_id = torch.argmin(torch.abs(u_arr + uv_len / 2))
        u_end_id = torch.argmin(torch.abs(u_arr - uv_len / 2))
        u_arr = u_arr[u_start_id : u_end_id + 1 : scale] + sampling_interval[0] / 2
        du = torch.mean(u_arr)
        u_arr = u_arr - du
        center = (
            round((y_range[0] + y_range[1]) / 2 / sampling_interval[1])
            * sampling_interval[1]
        )
        v_arr = vy_arr - center
        v_start_id = torch.argmin(torch.abs(v_arr + uv_len / 2))
        v_end_id = torch.argmin(torch.abs(v_arr - uv_len / 2))
        v_arr = v_arr[v_start_id : v_end_id + 1 : scale] + sampling_interval[1] / 2
        dv = torch.mean(v_arr)
        v_arr = v_arr - dv

        x_start_id = torch.argmin(torch.abs(ux_arr - x_range[0]))
        x_end_id = torch.argmin(torch.abs(ux_arr - x_range[1]))
        y_start_id = torch.argmin(torch.abs(vy_arr - y_range[0]))
        y_end_id = torch.argmin(torch.abs(vy_arr - y_range[1]))

        x_arr = ux_arr[x_start_id : x_end_id + 1] - du
        y_arr = vy_arr[y_start_id : y_end_id + 1] - dv

        co_public = (
            -1j
            * sampling_interval[0]
            * sampling_interval[1]
            * n1
            / self.lams.view(1, 1, 1, -1)
        )  # / 4 / torch.pi
        R_q = torch.sqrt(
            (ux_arr.view(-1, 1, 1, 1)) ** 2
            + (vy_arr.view(1, -1, 1, 1)) ** 2
            + z_arr.view(1, 1, -1, 1) ** 2
        )
        G_2D = self.k * R_q * 1j
        G_2D = torch.exp(G_2D) / R_q**2 * co_public * (1 - 1 / G_2D)

        self.G_2D = G_2D

        self.u_arr = u_arr
        self.v_arr = v_arr
        self.x_arr = x_arr
        self.y_arr = y_arr
        self.z_arr = z_arr

        self.x_num = x_end_id - x_start_id + 1
        self.y_num = y_end_id - y_start_id + 1

        self.u_pad_num = ux_arr.numel() - u_arr.numel() * scale
        self.v_pad_num = vy_arr.numel() - v_arr.numel() * scale
        self.dS = sampling_interval[0] * sampling_interval[1]

    def __call__(self, E):
        # E should have shape (u, v, lam)
        if E.dim() == 3:
            E_padded = E.repeat_interleave(self.scale, dim=0)
            E_padded = E_padded.repeat_interleave(self.scale, dim=1)
            pad = (
                0,
                0,  # No padding applied to the 2nd dimension (D2)
                self.v_pad_num,
                0,  # Extend on both sides of the 1st dimension (D1)
                self.u_pad_num,
                0,  # Extend on both sides of the 0th dimension (D0)
            )

            E_padded = F.pad(E_padded, pad, mode="constant", value=0)
            E_out = torch.zeros(
                [
                    self.x_num,
                    self.y_num,
                    self.z_arr.numel(),
                    self.lams.numel(),
                ],
                device=self.device,
                dtype=torch.complex64,
            )
            for z in range(self.z_arr.numel()):
                E_out[:, :, z, :] = fft_circular_conv2d(
                    E_padded, self.G_2D[:, :, z] * self.z_arr[z]
                )[
                    : self.x_num,
                    : self.y_num,
                ]
            return E_out

    def Get_G_2D(self, x_f, y_f, z_f):  # Typically used for optimization and validation
        z = self.focal_length + z_f  # Detection coordinate
        co_public = (
            -1j * self.dS * self.n1 / self.lams * self.scale**2
        )  # / 4 / torch.pi
        R_q = torch.sqrt(
            z**2
            + (x_f - self.u_arr.view(-1, 1, 1)) ** 2
            + (y_f - self.v_arr.view(1, -1, 1)) ** 2
        )
        ik0R = self.k.view(1, 1, -1) * R_q * 1j
        G_2D = torch.exp(ik0R) / R_q**2 * (1 - 1 / ik0R) * co_public

        return z * G_2D
