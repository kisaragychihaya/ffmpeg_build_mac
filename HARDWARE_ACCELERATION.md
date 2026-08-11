# 硬件加速编解码器支持列表

本文档列出本仓库 GitHub Action 构建的 FFmpeg 9.0(macOS arm64,Apple Silicon)中已验证可用的硬件加速编解码器。

**shared 与 static 两个构建的硬件加速能力完全一致**(configure 参数相同,仅链接方式不同),本文档对两者均适用。

数据来源:构建成功的 CI 日志中 `./configure` 输出及 `ffmpeg -hwaccels` / `-encoders` 实测结果(shared 与 static 均已核对)。

## 可用的硬件加速框架

`ffmpeg -hwaccels` 输出:

| 框架 | 说明 |
| --- | --- |
| `videotoolbox` | Apple 原生硬件编解码框架(GPU/媒体引擎) |
| `opencl` | OpenCL GPU 通用计算(部分滤镜) |
| `vulkan` | Vulkan GPU 计算(部分解码/滤镜) |

编译参数确认包含:`--enable-videotoolbox`、`--enable-audiotoolbox`、`--enable-opencl`、`--enable-neon`。

## 视频硬件编码器(VideoToolbox)

| 编码器 | 编码格式 | 用法示例 |
| --- | --- | --- |
| `h264_videotoolbox` | H.264 / AVC | `ffmpeg -i in.mp4 -c:v h264_videotoolbox -b:v 8M out.mp4` |
| `hevc_videotoolbox` | H.265 / HEVC | `ffmpeg -i in.mp4 -c:v hevc_videotoolbox -tag:v hvc1 out.mp4` |
| `prores_videotoolbox` | Apple ProRes | `ffmpeg -i in.mp4 -c:v prores_videotoolbox -profile:v 3 out.mov` |

## 视频硬件解码(VideoToolbox hwaccel)

FFmpeg 9 没有独立的 `*_videotoolbox` 解码器条目,硬件解码通过 `-hwaccel videotoolbox` 启用。支持的格式(configure 输出的 hwaccels):

- H.263(`h263_videotoolbox`)
- MPEG-1 / MPEG-2 / MPEG-4(`mpeg1/mpeg2/mpeg4_videotoolbox`)
- H.264 / AVC(`h264_videotoolbox`)
- H.265 / HEVC(`hevc_videotoolbox`)
- AV1(`av1_videotoolbox`)
- VP9(`vp9_videotoolbox`)
- ProRes / ProRes RAW(`prores_videotoolbox`、`prores_raw_videotoolbox`)

用法示例:

```bash
# 硬解 + 软编
ffmpeg -hwaccel videotoolbox -i in.mp4 -c:v libx265 out.mp4

# 硬解 + 硬编(零拷贝转码)
ffmpeg -hwaccel videotoolbox -hwaccel_output_format videotoolbox \
  -i in.mp4 -c:v hevc_videotoolbox -b:v 6M out.mp4
```

## Vulkan 加速

configure 输出的 Vulkan hwaccels:

- 解码:`apv_vulkan`、`av1_vulkan`、`dpx_vulkan`、`ffv1_vulkan`、`h264_vulkan`、`hevc_vulkan`、`mpeg? / vp9_vulkan`、`prores_vulkan`、`prores_raw_vulkan`
- 在 Apple Silicon 上 Vulkan 经由 MoltenVK 映射到 Metal

## Metal 加速

configure 输出中 `metal` 在 "External libraries providing hardware acceleration" 列表中(shared 与 static 均有),主要提供:

- `yadif_videotoolbox` 滤镜:Metal compute 实现的去隔行(VideoToolbox 帧零拷贝处理),编译产物为 `libavfilter/metal/vf_yadif_videotoolbox.metallib`

用法示例:

```bash
ffmpeg -hwaccel videotoolbox -i interlaced.mov \
  -vf yadif_videotoolbox -c:v hevc_videotoolbox out.mp4
```

## 音频硬件编解码器(AudioToolbox)

编码器:

| 编码器 | 格式 |
| --- | --- |
| `aac_at` | AAC |
| `alac_at` | Apple Lossless |
| `ilbc_at` | iLBC |
| `pcm_alaw_at` / `pcm_mulaw_at` | G.711 A-law / μ-law |

解码器:

`aac_at`、`ac3_at`(AC-3)、`eac3_at`(E-AC-3)、`alac_at`、`amr_nb_at`、`gsm_ms_at`、`ilbc_at`、`mp1_at`、`mp2_at`、`mp3_at`、`adpcm_ima_qt_at`、`qdm2_at`、`qdmc_at`、`pcm_alaw_at`、`pcm_mulaw_at`

用法示例:

```bash
# 使用 AudioToolbox 硬件 AAC 编码
ffmpeg -i in.wav -c:a aac_at -b:a 256k out.m4a
```

## NEON SIMD

`--enable-neon` 已启用,所有软件编解码路径(x264、x265、dav1d 等)均使用 ARM NEON 指令集优化,无需任何参数,自动生效。

## 备注

- GitHub Actions 的 macOS runner 是虚拟机,CI 中的功能测试使用 `-allow_sw 1` 回退;在真实 Apple Silicon 硬件上,上述 VideoToolbox 编解码均走硬件路径。
- 验证本机可用的硬件编码器:`ffmpeg -hide_banner -encoders | grep videotoolbox`
