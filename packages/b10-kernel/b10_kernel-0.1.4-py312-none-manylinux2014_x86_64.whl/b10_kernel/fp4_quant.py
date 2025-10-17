import torch


def scaled_fp4_grouped_quant(
    input_tensor: torch.Tensor,
    input_global_scale: torch.Tensor,
    mask: torch.Tensor,
):
    """
    Quantize input tensor to FP4 and return quantized tensor and scale, for
    grouped gemm inputs (e.g., grouped_gemm_nt_masked for flashinfer).
    Args:
        input: The input tensor to be quantized to FP4, with shape (l, m, k)
            l is number of groups, m is number of tokens per group, k is number of features.
        input_global_scale: A scalar scaling factor for the entire tensor, with
            shape (l,).
    Outputs:
        output: The quantized tensor in FP4, with shape (m, k // 2, l) but the physical
            layout is (l, m, k // 2). `// 2` is because two fp4 values are packed into
            an uint8.
        output_scales: The blockscale tensor in FP8-E4M3, with shape (32, 4, rm, 4, rk, l)
            but the physical layout is (l, rm, rk, 32, 4, 4).
    Note:
        For the shape of output_scales, `32 * 4 * rm` is a padded m to nearest multiple of 128.
        `4 * rk` is a padded `k // 16` to nearest multiple of 4. These layout constants are
        required by the NVIDIA Blackwell MMA operations.
    """
    device = input_tensor.device
    l, m, k = input_tensor.shape
    sf_vec_size = 16
    assert k % sf_vec_size == 0, f"k must be multiple of 16, but got {k}."

    scale_k = k // sf_vec_size
    padded_k = (scale_k + (4 - 1)) // 4 * 4
    padded_k_int32 = padded_k // 4
    padded_m = (m + (128 - 1)) // 128 * 128
    output = torch.empty(l, m, k // 2, device=device, dtype=torch.uint8)
    output_scales = torch.empty(
        l, padded_m, padded_k_int32, device=device, dtype=torch.int32
    )

    torch.ops.b10_kernel.scaled_fp4_quant.default(
        output.view(l * m, k // 2),
        output_scales.view(l * padded_m, padded_k_int32),
        input_tensor.view(l * m, k),
        input_global_scale,
        mask,
    )
    # The physical layout of the output is (l, m, k // 2), but we want to return a
    # logical layout (m, k // 2, l) required by the flashinfer masked group gemm.
    output = output.permute(1, 2, 0)
    # The physical layout of the output scales is already swizzled as (l, rm, rk, 32, 4, 4), a
    # requirement for the flashinfer masked group gemm, where rm=m/128 and rk=k/4. The logic
    # layout is (32, 4, rm, 4, rk, l).
    output_scales = output_scales.view(torch.float8_e4m3fn).view(
        l, padded_m // 128, padded_k // 4, 32, 4, 4
    )
    output_scales = output_scales.permute(3, 4, 1, 5, 2, 0)
    return output, output_scales
